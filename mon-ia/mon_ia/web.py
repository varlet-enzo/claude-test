"""L'interface web : un petit serveur local (FastAPI) qui sert la page de discussion."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, AsyncIterator, Generator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__
from .assistant import Assistant
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


def event_stream(events: Generator[dict[str, Any], None, None]) -> StreamingResponse:
    """Transmet les événements au navigateur au fur et à mesure (Server-Sent Events)."""

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

    return StreamingResponse(
        body(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


def create_app(assistant: Assistant) -> FastAPI:
    app = FastAPI(title="Mon IA", version=__version__, docs_url=None, redoc_url=None, openapi_url=None)
    if assistant.config.host in LOCAL_HOSTS:
        # Empêche un site malveillant de piloter ton IA via une attaque de type « DNS rebinding ».
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})

    @app.get("/api/infos")
    def infos() -> dict[str, Any]:
        return {
            "name": assistant.profile.name,
            "version": __version__,
            "thinking": assistant.config.thinking,
            "web_search": assistant.config.web_search,
            "context_size": assistant.config.context_size,
        }

    @app.get("/api/modeles")
    def models() -> dict[str, Any]:
        return assistant.models_overview()

    @app.post("/api/modeles/telecharger")
    def pull(body: PullIn) -> StreamingResponse:
        return event_stream(assistant.pull(body.model))

    @app.get("/api/conversations")
    def conversations() -> list[dict[str, Any]]:
        return assistant.store.list()

    @app.get("/api/conversations/{conversation_id}")
    def conversation(conversation_id: str) -> dict[str, Any]:
        try:
            data = assistant.store.load(conversation_id)
        except KeyError:
            raise HTTPException(404, "Conversation introuvable.") from None
        return {"id": data["id"], "title": data["title"], "messages": display_messages(data["messages"])}

    @app.delete("/api/conversations/{conversation_id}")
    def delete_conversation(conversation_id: str) -> dict[str, bool]:
        try:
            assistant.store.delete(conversation_id)
        except KeyError:
            raise HTTPException(404, "Conversation introuvable.") from None
        return {"ok": True}

    @app.post("/api/chat")
    def chat(body: ChatIn) -> StreamingResponse:
        if body.conversation_id:
            try:
                conversation = assistant.store.load(body.conversation_id)
            except KeyError:
                raise HTTPException(404, "Conversation introuvable.") from None
        else:
            conversation = assistant.store.new()
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
            )
        )

    @app.get("/api/memoire")
    def read_memory() -> dict[str, str]:
        return {"text": assistant.memory.read()}

    @app.put("/api/memoire")
    def write_memory(body: MemoryIn) -> dict[str, str]:
        assistant.memory.write(body.text)
        return {"text": assistant.memory.read()}

    @app.get("/api/profil")
    def read_profile() -> dict[str, str]:
        return {"name": assistant.profile.name, "personality": assistant.profile.personality}

    @app.put("/api/profil")
    def write_profile(body: ProfileIn) -> dict[str, str]:
        try:
            assistant.profile.set_name(body.name)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
        assistant.profile.set_personality(body.personality)
        return {"name": assistant.profile.name, "personality": assistant.profile.personality}

    return app
