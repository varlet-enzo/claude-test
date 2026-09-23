"""Sauvegarde des conversations : un fichier JSON par conversation, dans data/conversations."""

from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_TITLE = "Nouvelle conversation"
_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def make_title(text: str, max_length: int = 60) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first_line:
        return DEFAULT_TITLE
    if len(first_line) <= max_length:
        return first_line
    return first_line[: max_length - 1].rstrip() + "…"


def write_json_atomic(path: Path, data: Any) -> None:
    """Écrit dans un fichier temporaire puis le renomme : un plantage ne corrompt jamais le fichier."""
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=1)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


class ConversationStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self._deleted: set[str] = set()

    def _path(self, conversation_id: str) -> Path:
        if not _ID_PATTERN.match(conversation_id or ""):
            raise KeyError(conversation_id)
        return self.directory / f"{conversation_id}.json"

    def new(self) -> dict[str, Any]:
        now = now_iso()
        return {"id": uuid.uuid4().hex, "title": DEFAULT_TITLE, "created_at": now, "updated_at": now, "messages": []}

    def save(self, conversation: dict[str, Any]) -> None:
        if conversation["id"] in self._deleted:
            return  # supprimée pendant qu'une réponse s'écrivait : on ne la fait pas réapparaître
        conversation["updated_at"] = now_iso()
        write_json_atomic(self._path(conversation["id"]), conversation)

    def load(self, conversation_id: str) -> dict[str, Any]:
        path = self._path(conversation_id)
        if not path.exists():
            raise KeyError(conversation_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def delete(self, conversation_id: str) -> None:
        path = self._path(conversation_id)
        if not path.exists():
            raise KeyError(conversation_id)
        self._deleted.add(conversation_id)
        path.unlink()

    def list(self) -> list[dict[str, Any]]:
        summaries = []
        for path in self.directory.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            summaries.append({"id": data["id"], "title": data.get("title", DEFAULT_TITLE), "updated_at": data.get("updated_at", "")})
        summaries.sort(key=lambda item: item["updated_at"], reverse=True)
        return summaries


def display_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Regroupe les messages bruts en bulles à afficher.

    Un tour de l'IA peut contenir plusieurs messages (réflexion, appels d'outils, résultats,
    réponse finale) : ils sont fusionnés dans une seule bulle, comme pendant le direct.
    """
    items: list[dict[str, Any]] = []
    bubble: dict[str, Any] | None = None
    for message in messages:
        role = message.get("role")
        if role == "user":
            bubble = None
            items.append(
                {
                    "role": "user",
                    "text": message.get("display", message.get("content", "")),
                    "attachments": message.get("attachments", []),
                    "images": [f"data:image/jpeg;base64,{image}" for image in message.get("images", [])],
                }
            )
            continue
        if role not in ("assistant", "tool"):
            continue
        if bubble is None:
            bubble = {"role": "assistant", "text": "", "thinking": "", "tools": [], "notices": [], "model": None, "stats": None}
            items.append(bubble)
        if role == "assistant":
            if message.get("content"):
                bubble["text"] += ("\n\n" if bubble["text"] else "") + message["content"]
            if message.get("thinking"):
                bubble["thinking"] += ("\n\n" if bubble["thinking"] else "") + message["thinking"]
            for call in message.get("tool_calls") or []:
                function = call.get("function", {})
                bubble["tools"].append({"name": function.get("name", "?"), "label": None, "summary": None, "error": False})
            bubble["notices"].extend(message.get("notices", []))
            bubble["model"] = message.get("model") or bubble["model"]
            bubble["stats"] = message.get("stats") or bubble["stats"]
        else:
            for tool in bubble["tools"]:
                if tool["summary"] is None and tool["name"] == message.get("tool_name"):
                    tool["label"] = message.get("label")
                    tool["summary"] = message.get("summary", "")
                    tool["error"] = bool(message.get("error"))
                    break
    return items
