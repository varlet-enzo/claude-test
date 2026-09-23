"""Mémoire à long terme : un simple fichier texte (data/memoire.md).

L'IA y ajoute ce qu'elle apprend sur toi grâce à ses outils, et tu peux le lire ou le
modifier à la main à tout moment (depuis l'interface ou avec un éditeur de texte).
"""

from __future__ import annotations

import re
import threading
from pathlib import Path

HEADER = "# Ce que je sais sur toi\n\n"
MAX_FACT_LENGTH = 500
MAX_FORGOTTEN = 5


def _normalize(fact: str) -> str:
    fact = re.sub(r"\s+", " ", fact).strip()
    return re.sub(r"^[-*•]\s*", "", fact)


class Memory:
    def __init__(self, path: Path, max_prompt_chars: int = 6000) -> None:
        self.path = path
        self.max_prompt_chars = max_prompt_chars
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> str:
        try:
            return self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def write(self, text: str) -> None:
        with self._lock:
            self.path.write_text(text, encoding="utf-8")

    def facts(self) -> list[str]:
        return [_normalize(line) for line in self.read().splitlines() if line.strip() and not line.startswith("#")]

    def add(self, fact: str) -> bool:
        """Ajoute un souvenir. Renvoie False s'il était déjà connu."""
        fact = _normalize(fact)
        if not fact:
            raise ValueError("L'information à retenir est vide.")
        if len(fact) > MAX_FACT_LENGTH:
            raise ValueError(f"L'information est trop longue (maximum {MAX_FACT_LENGTH} caractères) : résume-la.")
        with self._lock:
            content = self.read()
            if fact.lower() in (known.lower() for known in self.facts()):
                return False
            if not content.strip():
                content = HEADER
            elif not content.endswith("\n"):
                content += "\n"
            self.path.write_text(content + f"- {fact}\n", encoding="utf-8")
            return True

    def forget(self, text: str) -> list[str]:
        """Supprime les lignes qui contiennent `text` et renvoie les souvenirs effacés."""
        needle = _normalize(text).lower()
        if len(needle) < 3:
            raise ValueError("Précise ce qu'il faut oublier (au moins 3 caractères).")
        with self._lock:
            kept, removed = [], []
            for line in self.read().splitlines():
                if not line.startswith("#") and needle in line.lower():
                    removed.append(_normalize(line))
                else:
                    kept.append(line)
            if len(removed) > MAX_FORGOTTEN:
                raise ValueError(
                    f"{len(removed)} souvenirs contiennent « {text} » : sois plus précis, "
                    "ou modifie la mémoire depuis le menu Mémoire."
                )
            if removed:
                self.path.write_text("\n".join(kept) + "\n", encoding="utf-8")
            return removed

    def for_prompt(self) -> str:
        """Le contenu à glisser dans les instructions de l'IA (les souvenirs les plus récents d'abord si c'est trop long)."""
        facts = self.facts()
        if not facts:
            return ""
        lines: list[str] = []
        total = 0
        for fact in reversed(facts):
            total += len(fact) + 3
            if total > self.max_prompt_chars:
                break
            lines.append(f"- {fact}")
        lines.reverse()
        if len(lines) < len(facts):
            lines.insert(0, f"(Mémoire trop longue : seuls les {len(lines)} souvenirs les plus récents sont affichés.)")
        return "\n".join(lines)
