"""Réglages techniques, lus depuis le fichier `.env` (tous facultatifs)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
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


def _read_friends(value: str) -> dict[str, str]:
    """IA_AMIS=leo:motdepasse1, sam:motdepasse2  ->  {"leo": "motdepasse1", "sam": "motdepasse2"}"""
    friends: dict[str, str] = {}
    for entry in filter(None, (part.strip() for part in value.split(","))):
        pseudo, separator, password = entry.partition(":")
        pseudo, password = pseudo.strip().lower(), password.strip()
        if not separator or not re.fullmatch(r"[a-z0-9_-]{2,20}", pseudo) or pseudo == "admin":
            raise SystemExit(
                f"IA_AMIS : « {entry} » est invalide. Écris pseudo:motdepasse, avec un pseudo de 2 à 20 lettres "
                "sans accent ni espace (et différent de « admin »)."
            )
        if len(password) < 6:
            raise SystemExit(f"IA_AMIS : le mot de passe de « {pseudo} » doit faire au moins 6 caractères.")
        friends[pseudo] = password
    return friends


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
    # Mode partage : ton mot de passe (compte « admin ») et les comptes de tes potes.
    password: str | None = None
    friends: dict[str, str] = field(default_factory=dict)

    @property
    def sharing(self) -> bool:
        return self.password is not None

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
        password = os.getenv("IA_MOT_DE_PASSE", "").strip() or None
        friends = _read_friends(os.getenv("IA_AMIS", ""))
        if password is not None and len(password) < 8:
            raise SystemExit("IA_MOT_DE_PASSE doit faire au moins 8 caractères.")
        if friends and password is None:
            raise SystemExit("IA_AMIS a besoin de IA_MOT_DE_PASSE (ton propre mot de passe) pour fonctionner.")
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
            password=password,
            friends=friends,
        )
