"""L'interface web : un petit serveur local (FastAPI) qui sert la page de discussion."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, AsyncIterator, Generator

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__
from .assistant import Assistant, Space
from .auth import SESSION_COOKIE, SESSION_SECONDS, Accounts, LoginError, User
from .files import AttachmentError, prepare_attachments
from .storage import display_messages

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
_END = object()


class AttachmentIn(BaseModel):
    name: str = Field(max_length=255)
    type: str = ""
    data: str


class ChatIn(BaseModel):
    conversation_id: str | None = None
    message: str = ""
    attachments: list[AttachmentIn] = []
    model: str | None = None
    thinking: bool | None = None


class PullIn(BaseModel):
    model: str


class MemoryIn(BaseModel):
    text: str


class ProfileIn(BaseModel):
    name: str
    personality: str


class LoginIn(BaseModel):
    pseudo: str = Field(max_length=40)
    password: str = Field(max_length=200)


def event_stream(events: Generator[dict[str, Any], None, None]) -> StreamingResponse:
    """Transmet les événements au navigateur au fur et à mesure."""

    async def body() -> AsyncIterator[str]:
        try:
            while True:
                try:
                    event = await run_in_threadpool(next, events, _END)
                except Exception as exc:
                    log.exception("Erreur pendant la réponse")
                    event = {"type": "error", "message": f"Erreur inattendue : {exc}"}
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    break
                if event is _END:
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        finally:
            # Fermer le générateur arrête la génération côté Ollama et sauvegarde la réponse partielle.
            events.close()

    # Pas de « text/event-stream » : les tunnels rapides de Cloudflare ne le transmettent pas.
    # « no-transform » empêche les intermédiaires de compresser, donc de retenir, le flux.
    return StreamingResponse(
        body(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


def create_app(assistant: Assistant) -> FastAPI:
    app = FastAPI(title="Mon IA", version=__version__, docs_url=None, redoc_url=None, openapi_url=None)
    accounts = Accounts(assistant.config)
    if assistant.config.host in LOCAL_HOSTS and not accounts.enabled:
        # Sans mot de passe, empêche un site malveillant de piloter ton IA (attaque « DNS rebinding »).
        # En mode partage, c'est la connexion qui protège, et le lien Cloudflare doit pouvoir passer.
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    def current_user(request: Request) -> User:
        user = accounts.user_from_cookie(request.cookies.get(SESSION_COOKIE))
        if user is None:
            raise HTTPException(401, "Connecte-toi pour continuer.")
        return user

    def owner_only(user: User = Depends(current_user)) -> User:
        if not user.is_owner:
            raise HTTPException(403, "Réservé à la personne qui héberge l'IA.")
        return user

    def space(user: User = Depends(current_user)) -> Space:
        return assistant.space_for(user.name)

    @app.get("/api/session")
    def session(request: Request) -> dict[str, Any]:
        user = accounts.user_from_cookie(request.cookies.get(SESSION_COOKIE))
        return {
            "sharing": accounts.enabled,
            "user": user.name if user else None,
            "owner": bool(user and user.is_owner),
        }

    @app.post("/api/connexion")
    def login(body: LoginIn, request: Request, response: Response) -> dict[str, Any]:
        if not accounts.enabled:
            return {"user": "admin", "owner": True}
        client = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "?")
        try:
            user = accounts.login(body.pseudo, body.password, client)
        except LoginError as exc:
            status = 429 if "Trop d'essais" in str(exc) else 401
            raise HTTPException(status, str(exc)) from None
        response.set_cookie(
            SESSION_COOKIE,
            accounts.cookie_for(user),
            max_age=SESSION_SECONDS,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
        )
        return {"user": user.name, "owner": user.is_owner}

    @app.post("/api/deconnexion")
    def logout(response: Response) -> dict[str, bool]:
        response.delete_cookie(SESSION_COOKIE)
        return {"ok": True}

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})

    @app.get("/api/infos", dependencies=[Depends(current_user)])
    def infos() -> dict[str, Any]:
        return {
            "name": assistant.profile.name,
            "version": __version__,
            "thinking": assistant.config.thinking,
            "web_search": assistant.config.web_search,
            "context_size": assistant.config.context_size,
        }

    @app.get("/api/modeles", dependencies=[Depends(current_user)])
    def models() -> dict[str, Any]:
        return assistant.models_overview()

    @app.post("/api/modeles/telecharger", dependencies=[Depends(owner_only)])
    def pull(body: PullIn) -> StreamingResponse:
        return event_stream(assistant.pull(body.model))

    @app.get("/api/conversations")
    def conversations(mine: Space = Depends(space)) -> list[dict[str, Any]]:
        return mine.store.list()

    @app.get("/api/conversations/{conversation_id}")
    def conversation(conversation_id: str, mine: Space = Depends(space)) -> dict[str, Any]:
        try:
            data = mine.store.load(conversation_id)
        except KeyError:
            raise HTTPException(404, "Conversation introuvable.") from None
        return {"id": data["id"], "title": data["title"], "messages": display_messages(data["messages"])}

    @app.delete("/api/conversations/{conversation_id}")
    def delete_conversation(conversation_id: str, mine: Space = Depends(space)) -> dict[str, bool]:
        try:
            mine.store.delete(conversation_id)
        except KeyError:
            raise HTTPException(404, "Conversation introuvable.") from None
        return {"ok": True}

    @app.post("/api/chat")
    def chat(body: ChatIn, user: User = Depends(current_user)) -> StreamingResponse:
        mine = assistant.space_for(user.name)
        if body.conversation_id:
            try:
                conversation = mine.store.load(body.conversation_id)
            except KeyError:
                raise HTTPException(404, "Conversation introuvable.") from None
        else:
            conversation = mine.store.new()
        try:
            images, documents = prepare_attachments(body.attachments)
        except AttachmentError as exc:
            raise HTTPException(400, str(exc)) from None
        if not body.message.strip() and not images and not documents:
            raise HTTPException(400, "Le message est vide.")
        return event_stream(
            assistant.chat(
                conversation,
                body.message,
                images=images,
                documents=documents,
                model=body.model or None,
                thinking=body.thinking,
                space=mine,
                guest=None if user.is_owner else user.name.capitalize(),
            )
        )

    @app.get("/api/memoire")
    def read_memory(mine: Space = Depends(space)) -> dict[str, str]:
        return {"text": mine.memory.read()}

    @app.put("/api/memoire")
    def write_memory(body: MemoryIn, mine: Space = Depends(space)) -> dict[str, str]:
        mine.memory.write(body.text)
        return {"text": mine.memory.read()}

    @app.get("/api/profil", dependencies=[Depends(current_user)])
    def read_profile() -> dict[str, str]:
        return {"name": assistant.profile.name, "personality": assistant.profile.personality}

    @app.put("/api/profil", dependencies=[Depends(owner_only)])
    def write_profile(body: ProfileIn) -> dict[str, str]:
        try:
            assistant.profile.set_name(body.name)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
        assistant.profile.set_personality(body.personality)
        return {"name": assistant.profile.name, "personality": assistant.profile.personality}

    return app
