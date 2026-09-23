"""Comptes et connexion, pour partager ton IA avec tes potes (mode partage).

Le mode partage s'active dès que IA_MOT_DE_PASSE est défini. Tout le monde doit alors se
connecter : toi avec le pseudo « admin », tes potes avec les comptes de IA_AMIS.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from .assistant import OWNER
from .config import Config

SESSION_COOKIE = "monia_session"
SESSION_SECONDS = 30 * 24 * 3600
MAX_FAILURES = 8
FAILURE_WINDOW = 15 * 60


class LoginError(Exception):
    """Connexion refusée (message destiné à l'utilisateur)."""


@dataclass(frozen=True)
class User:
    name: str

    @property
    def is_owner(self) -> bool:
        return self.name == OWNER


def _load_secret(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        path.parent.mkdir(parents=True, exist_ok=True)
        secret = secrets.token_bytes(32)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as file:
            file.write(secret)
        return secret


class Accounts:
    def __init__(self, config: Config) -> None:
        self.enabled = config.sharing
        self._passwords = {OWNER: config.password, **config.friends} if config.sharing else {}
        self._secret = _load_secret(config.data_dir / ".secret") if config.sharing else b""
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _fingerprint(self, name: str) -> str:
        # Changer un mot de passe dans .env déconnecte automatiquement la personne concernée.
        return hmac.new(self._secret, self._passwords[name].encode(), hashlib.sha256).hexdigest()[:16]

    def _sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode(), hashlib.sha256).hexdigest()

    def login(self, pseudo: str, password: str, client: str) -> User:
        now = time.monotonic()
        with self._lock:
            recent = [moment for moment in self._failures.get(client, []) if now - moment < FAILURE_WINDOW]
            self._failures[client] = recent
            if len(recent) >= MAX_FAILURES:
                raise LoginError("Trop d'essais ratés. Réessaie dans un quart d'heure.")
        name = pseudo.strip().lower()
        expected = self._passwords.get(name)
        if expected is None or not hmac.compare_digest(expected.encode(), password.encode()):
            with self._lock:
                self._failures[client].append(now)
            raise LoginError("Pseudo ou mot de passe incorrect.")
        with self._lock:
            self._failures.pop(client, None)
        return User(name)

    def cookie_for(self, user: User) -> str:
        data = {"u": user.name, "v": self._fingerprint(user.name), "exp": int(time.time()) + SESSION_SECONDS}
        payload = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
        return f"{payload}.{self._sign(payload)}"

    def user_from_cookie(self, cookie: str | None) -> User | None:
        if not self.enabled:
            return User(OWNER)
        if not cookie or "." not in cookie:
            return None
        payload, signature = cookie.rsplit(".", 1)
        if not hmac.compare_digest(self._sign(payload), signature):
            return None
        try:
            data = json.loads(base64.urlsafe_b64decode(payload.encode()))
            name = data["u"]
        except (ValueError, KeyError, TypeError):
            return None
        if name not in self._passwords or data.get("v") != self._fingerprint(name) or data.get("exp", 0) < time.time():
            return None
        return User(name)
