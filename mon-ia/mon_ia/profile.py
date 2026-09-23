"""Identité de l'IA : son nom et sa personnalité, modifiables depuis l'interface."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from .storage import write_json_atomic

DEFAULT_PERSONALITY = """Tu es {nom}, l'assistant IA personnel de ton utilisateur.
Tu tournes entièrement sur son ordinateur : ce qu'il te dit reste chez lui.

Ton caractère :
- chaleureux, curieux et honnête ;
- tu tutoies l'utilisateur et tu réponds dans sa langue (le français par défaut) ;
- tu vas droit au but, puis tu développes seulement si c'est utile ou si on te le demande ;
- quand tu ne sais pas ou que tu n'es pas sûr, tu le dis au lieu d'inventer ;
- tu mets en forme tes réponses en Markdown quand ça aide (listes, titres, blocs de code).
"""

DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def french_date(moment: datetime) -> str:
    return f"{DAYS[moment.weekday()]} {moment.day} {MONTHS[moment.month - 1]} {moment.year}"


class Profile:
    def __init__(self, data_dir: Path, default_name: str) -> None:
        data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = data_dir / "reglages.json"
        self.personality_path = data_dir / "personnalite.md"
        self.default_name = default_name
        self._lock = threading.Lock()
        if not self.personality_path.exists():
            self.personality_path.write_text(DEFAULT_PERSONALITY, encoding="utf-8")

    def _settings(self) -> dict:
        try:
            return json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            return {}

    @property
    def name(self) -> str:
        return self._settings().get("nom") or self.default_name

    def set_name(self, name: str) -> None:
        name = " ".join(name.split())
        if not name or len(name) > 40:
            raise ValueError("Le nom doit faire entre 1 et 40 caractères.")
        with self._lock:
            settings = self._settings()
            settings["nom"] = name
            write_json_atomic(self.settings_path, settings)

    @property
    def personality(self) -> str:
        try:
            return self.personality_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return DEFAULT_PERSONALITY

    def set_personality(self, text: str) -> None:
        with self._lock:
            self.personality_path.write_text(text.strip() + "\n" if text.strip() else DEFAULT_PERSONALITY, encoding="utf-8")

    def system_prompt(self, *, memory: str, tool_guide: str, now: datetime, guest: str | None = None) -> str:
        parts = [self.personality.replace("{nom}", self.name).strip()]
        if guest:
            parts.append(
                f"Tu discutes en ce moment avec {guest}, un ami de la personne qui t'héberge sur son ordinateur. "
                "« L'utilisateur », c'est lui."
            )
        parts += [
            f"Nous sommes le {french_date(now)}.",
            "## Ce que tu sais sur l'utilisateur (ta mémoire à long terme)\n"
            + (memory or "Tu ne sais encore rien sur lui : tu l'apprendras au fil de vos discussions."),
        ]
        if tool_guide:
            parts.append("## Tes outils\n" + tool_guide)
        else:
            parts.append("Tu n'as pas accès à internet ni à des outils : réponds avec tes propres connaissances.")
        return "\n\n".join(parts)
