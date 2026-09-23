"""Le moteur de l'IA : discute avec le modèle local via Ollama, gère le contexte, les outils et la sauvegarde.

`Assistant.chat()` renvoie une suite d'événements (dictionnaires) que l'interface web et le
terminal affichent au fil de l'eau :

    conversation  la conversation (id, titre) à laquelle appartient le message
    thinking      un morceau de la réflexion du modèle
    text          un morceau de la réponse
    tool_call     l'IA utilise un outil (label = description lisible)
    tool_result   résultat de l'outil (summary = résumé lisible)
    notice        information à afficher (réponse coupée, image ignorée…)
    done          fin de la réponse, avec quelques statistiques
    error         problème à afficher à l'utilisateur
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from typing import Any, Callable, Iterator, Sequence

import httpx
import ollama

from .config import Config
from .memory import Memory
from .profile import Profile
from .storage import DEFAULT_TITLE, ConversationStore, make_title, now_iso
from .tools import Toolbox, ddgs_fetch, ddgs_search

log = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 6
# Estimations prudentes pour ne pas dépasser la mémoire de travail du modèle.
CHARS_PER_TOKEN = 3.5
IMAGE_TOKENS = 1000
ANSWER_SHARE = 0.25


class AssistantError(Exception):
    """Erreur à montrer telle quelle à l'utilisateur."""


def normalize_model_name(name: str) -> str:
    name = name.strip()
    return name if ":" in name.rsplit("/", 1)[-1] else f"{name}:latest"


def _split_turns(messages: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    turns: list[list[dict[str, Any]]] = []
    for message in messages:
        if message.get("role") == "user" or not turns:
            turns.append([])
        turns[-1].append(message)
    return turns


class Assistant:
    def __init__(
        self,
        config: Config,
        *,
        client: ollama.Client | None = None,
        search: Callable[[str, str, int], list[dict[str, Any]]] = ddgs_search,
        fetch: Callable[[str], str] = ddgs_fetch,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.config = config
        self.client = client or ollama.Client(host=config.ollama_host)
        self.ollama_url = config.ollama_host or "http://127.0.0.1:11434"
        self.context_chars = int(config.context_size * CHARS_PER_TOKEN)
        self.store = ConversationStore(config.data_dir / "conversations")
        self.memory = Memory(config.data_dir / "memoire.md", max_prompt_chars=min(6000, self.context_chars // 5))
        self.profile = Profile(config.data_dir, config.name)
        self.toolbox = Toolbox(
            self.memory,
            web=config.web_search,
            region=config.search_region,
            page_chars=min(20000, int(self.context_chars * 0.35)),
            search=search,
            fetch=fetch,
        )
        self._clock = clock
        self._capabilities: dict[str, set[str] | None] = {}
        self._tools_refused: set[str] = set()
        self._busy: set[str] = set()
        self._busy_lock = threading.Lock()

    # --- Modèles -----------------------------------------------------------------------------

    def _unreachable(self) -> str:
        return (
            f"Impossible de joindre Ollama ({self.ollama_url}). Vérifie qu'il est installé et lancé : "
            "https://ollama.com/download"
        )

    def _describe_error(self, exc: ollama.ResponseError, model: str) -> str:
        message = exc.error or str(exc)
        lowered = message.lower()
        if exc.status_code == 404 or "not found" in lowered:
            return (
                f"Le modèle « {model} » n'est pas installé. Télécharge-le depuis le menu « Modèles » "
                f"ou avec la commande : ollama pull {model}"
            )
        if "memory" in lowered:
            return (
                f"Pas assez de mémoire pour faire tourner « {model} » ({message}). "
                "Choisis un modèle plus petit ou baisse IA_CONTEXTE dans le fichier .env."
            )
        return f"Erreur d'Ollama : {message}"

    def list_models(self) -> list[dict[str, Any]]:
        try:
            response = self.client.list()
        except (ConnectionError, httpx.TransportError) as exc:
            raise AssistantError(self._unreachable()) from exc
        models = []
        for model in response.models:
            details = model.details
            models.append(
                {
                    "name": model.model,
                    "size": int(model.size or 0),
                    "parameters": details.parameter_size if details else None,
                    "family": details.family if details else None,
                }
            )
        return sorted(models, key=lambda item: item["name"])

    def capabilities(self, model: str) -> set[str] | None:
        """Ce que sait faire un modèle (tools, thinking, vision…). None = Ollama trop ancien pour le dire."""
        if model not in self._capabilities:
            info = self.client.show(model)
            self._capabilities[model] = set(info.capabilities) if info.capabilities is not None else None
        return self._capabilities[model]

    def models_overview(self) -> dict[str, Any]:
        try:
            models = self.list_models()
        except AssistantError as exc:
            return {"ok": False, "error": str(exc), "models": [], "default": self.config.model}
        chat_models = []
        for model in models:
            try:
                capabilities = self.capabilities(model["name"])
            except (ollama.ResponseError, ConnectionError, httpx.TransportError):
                capabilities = None
            if capabilities is not None and "completion" not in capabilities:
                continue  # modèle d'embeddings, inutilisable pour discuter
            model["capabilities"] = sorted(capabilities) if capabilities is not None else None
            chat_models.append(model)
        return {
            "ok": True,
            "error": None,
            "models": chat_models,
            "default": self.default_model([model["name"] for model in chat_models]),
        }

    def default_model(self, installed: list[str] | None = None) -> str:
        """Le modèle choisi dans les réglages s'il est installé, sinon le premier modèle installé."""
        if installed is None:
            try:
                installed = [model["name"] for model in self.list_models()]
            except AssistantError:
                return self.config.model
        wanted = normalize_model_name(self.config.model)
        for name in installed:
            if normalize_model_name(name) == wanted:
                return name
        return installed[0] if installed else self.config.model

    def pull(self, model: str) -> Iterator[dict[str, Any]]:
        """Télécharge un modèle depuis la bibliothèque d'Ollama, en donnant la progression."""
        model = model.strip()
        if not model:
            yield {"type": "error", "message": "Indique le nom du modèle à télécharger, par exemple qwen3:8b."}
            return
        stream = None
        try:
            stream = self.client.pull(model, stream=True)
            for progress in stream:
                yield {
                    "type": "progress",
                    "status": progress.status or "",
                    "completed": progress.completed or 0,
                    "total": progress.total or 0,
                }
            self._capabilities.pop(model, None)
            self._tools_refused.discard(model)
            yield {"type": "done", "model": model}
        except ollama.ResponseError as exc:
            message = exc.error or str(exc)
            if "file does not exist" in message or "not found" in message.lower():
                message = f"Le modèle « {model} » n'existe pas sur ollama.com/library. Vérifie son nom (exemple : qwen3:8b)."
            else:
                message = f"Téléchargement impossible : {message}"
            yield {"type": "error", "message": message}
        except (ConnectionError, httpx.TransportError):
            yield {"type": "error", "message": self._unreachable()}
        finally:
            if stream is not None:
                stream.close()

    # --- Conversation ------------------------------------------------------------------------

    @property
    def attachment_chars(self) -> int:
        return int(self.context_chars * 0.5)

    def chat(
        self,
        conversation: dict[str, Any],
        text: str,
        *,
        images: Sequence[tuple[str, str]] = (),
        documents: Sequence[tuple[str, str]] = (),
        model: str | None = None,
        thinking: bool | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Envoie un message et renvoie la réponse au fil de l'eau.

        images : liste de (nom du fichier, image JPEG en base64)
        documents : liste de (nom du fichier, texte extrait)
        """
        conversation_id = conversation["id"]
        with self._busy_lock:
            busy = conversation_id in self._busy
            if not busy:
                self._busy.add(conversation_id)
        if busy:
            yield {"type": "error", "message": "Une réponse est déjà en cours dans cette conversation."}
            return
        try:
            yield from self._chat(conversation, text, list(images), list(documents), model, thinking)
        finally:
            with self._busy_lock:
                self._busy.discard(conversation_id)

    def _compose(self, text: str, documents: list[tuple[str, str]]) -> str:
        parts = [text.strip()] if text.strip() else []
        limit = self.attachment_chars // max(1, len(documents))
        for name, body in documents:
            if len(body) > limit:
                body = body[:limit] + (
                    f"\n[… document tronqué : {len(body)} caractères au total, trop long pour la mémoire de travail actuelle]"
                )
            parts.append(f"--- Début du fichier « {name} » ---\n{body}\n--- Fin du fichier « {name} » ---")
        return "\n\n".join(parts)

    @staticmethod
    def _think_parameter(model: str, capabilities: set[str] | None, wanted: bool) -> bool | str | None:
        if capabilities is None or "thinking" not in capabilities:
            return None
        if "gpt-oss" in model:
            return "medium" if wanted else "low"  # gpt-oss réfléchit toujours un peu : on règle l'intensité
        return wanted

    def _for_model(self, message: dict[str, Any], vision: bool, keep_thinking: bool) -> dict[str, Any]:
        role = message["role"]
        converted: dict[str, Any] = {"role": role, "content": message.get("content", "")}
        if role == "user" and message.get("images"):
            if vision:
                converted["images"] = list(message["images"])
            else:
                count = len(message["images"])
                converted["content"] += f"\n\n[L'utilisateur a joint {count} image(s), mais tu ne peux pas voir les images.]"
        elif role == "assistant":
            if message.get("tool_calls"):
                converted["tool_calls"] = message["tool_calls"]
            if keep_thinking and message.get("thinking"):
                converted["thinking"] = message["thinking"]
        elif role == "tool":
            converted["tool_name"] = message.get("tool_name", "")
        return converted

    @staticmethod
    def _weight(message: dict[str, Any]) -> int:
        weight = len(message.get("content") or "") + len(message.get("thinking") or "")
        if message.get("tool_calls"):
            weight += len(json.dumps(message["tool_calls"], ensure_ascii=False))
        return weight + len(message.get("images") or []) * int(IMAGE_TOKENS * CHARS_PER_TOKEN)

    def _request_messages(
        self, system_prompt: str, messages: list[dict[str, Any]], turn_start: int, vision: bool
    ) -> tuple[list[dict[str, Any]], bool]:
        """Construit ce qu'on envoie au modèle, en oubliant les plus vieux échanges si ça ne rentre pas.

        Renvoie aussi True si le tour en cours dépasse à lui seul la mémoire de travail.
        """
        budget = int(self.context_chars * (1 - ANSWER_SHARE)) - len(system_prompt)
        current = [self._for_model(message, vision, keep_thinking=True) for message in messages[turn_start:]]
        used = sum(self._weight(message) for message in current)
        kept: list[dict[str, Any]] = []
        for turn in reversed(_split_turns(messages[:turn_start])):
            converted = [self._for_model(message, vision, keep_thinking=False) for message in turn]
            weight = sum(self._weight(message) for message in converted)
            if used + weight > budget:
                break
            kept = converted + kept
            used += weight
        return [{"role": "system", "content": system_prompt}, *kept, *current], used > budget

    def _save_partial(self, conversation: dict[str, Any], content: str, reasoning: str, model: str, notice: str) -> None:
        message: dict[str, Any] = {
            "role": "assistant",
            "content": content,
            "model": model,
            "created_at": now_iso(),
            "notices": [notice],
        }
        if reasoning:
            message["thinking"] = reasoning
        conversation["messages"].append(message)
        try:
            self.store.save(conversation)
        except OSError:
            log.exception("Impossible de sauvegarder la réponse partielle")

    def _chat(
        self,
        conversation: dict[str, Any],
        text: str,
        images: list[tuple[str, str]],
        documents: list[tuple[str, str]],
        model: str | None,
        thinking: bool | None,
    ) -> Iterator[dict[str, Any]]:
        model = model or self.default_model()
        messages = conversation["messages"]
        names = [name for name, _ in images] + [name for name, _ in documents]
        user_message: dict[str, Any] = {
            "role": "user",
            "content": self._compose(text, documents),
            "display": text,
            "created_at": now_iso(),
        }
        if names:
            user_message["attachments"] = names
        if images:
            user_message["images"] = [data for _, data in images]
        messages.append(user_message)
        if conversation.get("title", DEFAULT_TITLE) == DEFAULT_TITLE:
            conversation["title"] = make_title(text or (names[0] if names else ""))
        self.store.save(conversation)
        yield {"type": "conversation", "id": conversation["id"], "title": conversation["title"]}
        turn_start = len(messages) - 1

        try:
            capabilities = self.capabilities(model)
        except ollama.ResponseError as exc:
            yield {"type": "error", "message": self._describe_error(exc, model)}
            return
        except (ConnectionError, httpx.TransportError):
            yield {"type": "error", "message": self._unreachable()}
            return

        use_tools = bool(self.toolbox.names) and model not in self._tools_refused and (
            capabilities is None or "tools" in capabilities
        )
        think = self._think_parameter(model, capabilities, self.config.thinking if thinking is None else thinking)
        vision = capabilities is None or "vision" in capabilities
        notices: list[str] = []
        if images and not vision:
            notices.append("Ce modèle ne sait pas lire les images : elles ont été ignorées. Essaie un modèle « vision », par exemple gemma3.")

        def build_system_prompt() -> str:
            return self.profile.system_prompt(
                memory=self.memory.for_prompt(),
                tool_guide=self.toolbox.guide() if use_tools else "",
                now=self._clock(),
            )

        system_prompt = build_system_prompt()
        total_tokens, total_seconds, rounds, announced = 0, 0.0, 0, False
        while True:
            allow_tools = use_tools and rounds < MAX_TOOL_ROUNDS
            request, too_long = self._request_messages(system_prompt, messages, turn_start, vision)
            if not announced:
                announced = True
                if too_long:
                    notices.append(
                        "Ton message est très long pour la mémoire de travail du modèle : la fin risque d'être ignorée. "
                        "Augmente IA_CONTEXTE dans le fichier .env si ton ordinateur a assez de mémoire."
                    )
                for notice in notices:
                    yield {"type": "notice", "message": notice}
            content, reasoning, calls, final = "", "", [], None
            stream = None
            try:
                stream = self.client.chat(
                    model=model,
                    messages=request,
                    tools=self.toolbox.definitions() if allow_tools else None,
                    think=think,
                    stream=True,
                    options={"num_ctx": self.config.context_size},
                )
                for chunk in stream:
                    if chunk.message.thinking:
                        reasoning += chunk.message.thinking
                        yield {"type": "thinking", "text": chunk.message.thinking}
                    if chunk.message.content:
                        content += chunk.message.content
                        yield {"type": "text", "text": chunk.message.content}
                    if chunk.message.tool_calls:
                        calls.extend(chunk.message.tool_calls)
                    if chunk.done:
                        final = chunk
            except (GeneratorExit, KeyboardInterrupt):
                self._save_partial(conversation, content, reasoning, model, "Réponse interrompue.")
                raise
            except ollama.ResponseError as exc:
                if allow_tools and "does not support tools" in (exc.error or ""):
                    self._tools_refused.add(model)
                    use_tools = False
                    system_prompt = build_system_prompt()
                    continue
                if think is not None and "does not support thinking" in (exc.error or ""):
                    think = None
                    continue
                error = self._describe_error(exc, model)
            except (ConnectionError, httpx.TransportError):
                error = self._unreachable()
            except Exception as exc:
                log.exception("Erreur pendant la génération")
                error = f"Erreur inattendue : {exc}"
            else:
                error = None
            finally:
                if stream is not None:
                    stream.close()

            if error:
                if content or reasoning:
                    self._save_partial(conversation, content, reasoning, model, f"Réponse interrompue par une erreur : {error}")
                yield {"type": "error", "message": error}
                return

            if final is not None:
                total_tokens += final.eval_count or 0
                total_seconds += (final.eval_duration or 0) / 1e9

            if calls and allow_tools:
                step: dict[str, Any] = {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [
                        {"function": {"name": call.function.name, "arguments": dict(call.function.arguments or {})}}
                        for call in calls
                    ],
                }
                if reasoning:
                    step["thinking"] = reasoning
                pending = [step]
                try:
                    for call in step["tool_calls"]:
                        name, arguments = call["function"]["name"], call["function"]["arguments"]
                        label = self.toolbox.describe(name, arguments)
                        yield {"type": "tool_call", "name": name, "label": label}
                        result = self.toolbox.run(name, arguments)
                        pending.append(
                            {
                                "role": "tool",
                                "tool_name": name,
                                "content": result.content,
                                "label": label,
                                "summary": result.summary,
                                "error": result.error,
                            }
                        )
                        yield {"type": "tool_result", "name": name, "summary": result.summary, "error": result.error}
                except (GeneratorExit, KeyboardInterrupt):
                    self._save_partial(conversation, content, reasoning, model, "Réponse interrompue.")
                    raise
                messages.extend(pending)
                self.store.save(conversation)
                rounds += 1
                continue

            final_notices = []
            if final is not None and final.done_reason == "length":
                final_notices.append(
                    "Réponse coupée : la mémoire de travail du modèle est pleine. "
                    "Commence une nouvelle conversation ou augmente IA_CONTEXTE."
                )
            if not content.strip():
                final_notices.append("Le modèle n'a rien répondu. Réessaie ou reformule ta question.")
            for notice in final_notices:
                yield {"type": "notice", "message": notice}
            stats = {"tokens": total_tokens, "speed": round(total_tokens / total_seconds, 1) if total_seconds else None}
            answer: dict[str, Any] = {
                "role": "assistant",
                "content": content,
                "model": model,
                "created_at": now_iso(),
                "stats": stats,
            }
            if reasoning:
                answer["thinking"] = reasoning
            if notices or final_notices:
                answer["notices"] = notices + final_notices
            messages.append(answer)
            self.store.save(conversation)
            yield {"type": "done", "model": model, "stats": stats}
            return
