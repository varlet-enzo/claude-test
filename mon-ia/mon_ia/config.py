"""Réglages techniques, lus depuis le fichier `.env` (tous facultatifs)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent

TRUE_WORDS = {"1", "oui", "o", "yes", "y", "true", "vrai", "on"}
FALSE_WORDS = {"0", "non", "n", "no", "false", "faux", "off"}


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name, "").strip().lower()
    if value in TRUE_WORDS:
        return True
    if value in FALSE_WORDS:
        return False
    return default


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    try:
        return int(value) if value else default
    except ValueError:
        raise SystemExit(f"Réglage invalide : {name}={value!r} (un nombre entier est attendu).")


@dataclass
class Config:
    # Nom donné à l'IA au premier lancement (modifiable ensuite depuis l'interface).
    name: str = "Nova"
    # Modèle Ollama utilisé par défaut (voir le README pour choisir selon ton matériel).
    model: str = "qwen3:8b"
    # Adresse d'Ollama. None = celle par défaut (http://127.0.0.1:11434) ou la variable OLLAMA_HOST.
    ollama_host: str | None = None
    # Taille de la « mémoire de travail » du modèle, en tokens. Plus grand = conversations et
    # documents plus longs, mais plus de mémoire vive utilisée.
    context_size: int = 8192
    # Réflexion approfondie activée par défaut (plus intelligent, mais plus lent).
    thinking: bool = False
    # Autorise l'IA à chercher sur internet (DuckDuckGo & co, gratuit et sans compte).
    web_search: bool = True
    search_region: str = "fr-fr"
    # Dossier où sont rangées les conversations, la mémoire et la personnalité.
    data_dir: Path = PROJECT_DIR / "data"
    # Adresse de l'interface web. 127.0.0.1 = accessible uniquement depuis ton ordinateur.
    host: str = "127.0.0.1"
    port: int = 8000

    @classmethod
    def load(cls, env_file: Path | None = None) -> Config:
        load_dotenv(env_file or PROJECT_DIR / ".env")
        defaults = cls()
        data_dir = Path(os.getenv("IA_DONNEES", "").strip() or defaults.data_dir)
        if not data_dir.is_absolute():
            data_dir = PROJECT_DIR / data_dir
        context_size = _read_int("IA_CONTEXTE", defaults.context_size)
        if context_size < 2048:
            raise SystemExit("IA_CONTEXTE doit valoir au moins 2048.")
        return cls(
            name=os.getenv("IA_NOM", "").strip() or defaults.name,
            model=os.getenv("IA_MODELE", "").strip() or defaults.model,
            ollama_host=os.getenv("OLLAMA_HOST", "").strip() or None,
            context_size=context_size,
            thinking=_read_bool("IA_REFLEXION", defaults.thinking),
            web_search=_read_bool("IA_RECHERCHE_WEB", defaults.web_search),
            search_region=os.getenv("IA_REGION_RECHERCHE", "").strip() or defaults.search_region,
            data_dir=data_dir,
            host=os.getenv("IA_HOTE", "").strip() or defaults.host,
            port=_read_int("IA_PORT", defaults.port),
        )
