"""Discuter avec ton IA directement dans le terminal."""

from __future__ import annotations

import os
import sys

from .assistant import Assistant, AssistantError, normalize_model_name

BOLD, DIM, CYAN, YELLOW, RED, RESET = "\033[1m", "\033[2m", "\033[36m", "\033[33m", "\033[31m", "\033[0m"

HELP = """Commandes :
  /nouveau          commencer une nouvelle conversation
  /modele [nom]     voir ou changer de modèle
  /modeles          lister les modèles installés
  /reflexion        activer ou désactiver la réflexion approfondie
  /memoire          voir ce que ton IA sait sur toi
  /aide             afficher cette aide
  /quitter          quitter (ou Ctrl+D)"""


def _colors_supported() -> bool:
    if not sys.stdout.isatty() or os.getenv("NO_COLOR"):
        return False
    if os.name == "nt":
        os.system("")  # active les codes couleur dans l'ancienne console Windows
    return True


class Terminal:
    def __init__(self, assistant: Assistant, *, model: str | None, thinking: bool, show_thinking: bool) -> None:
        self.assistant = assistant
        self.model = model
        self.thinking = thinking
        self.show_thinking = show_thinking
        self.colors = _colors_supported()
        self.conversation = assistant.store.new()

    def paint(self, style: str, text: str) -> str:
        return f"{style}{text}{RESET}" if self.colors else text

    def run(self) -> int:
        try:
            installed = [model["name"] for model in self.assistant.list_models()]
        except AssistantError as exc:
            print(self.paint(RED, f"⚠ {exc}"))
            return 1
        if not installed:
            print(self.paint(YELLOW, "Aucun modèle n'est installé. Installe-en un, par exemple :  ollama pull qwen3:8b"))
            return 1
        self.model = self.model or self.assistant.default_model(installed)
        if normalize_model_name(self.model) not in {normalize_model_name(name) for name in installed}:
            print(self.paint(YELLOW, f"Le modèle « {self.model} » n'est pas installé. Modèles disponibles : {', '.join(installed)}"))
            return 1

        name = self.assistant.profile.name
        print(self.paint(BOLD, f"\n✦ {name}") + f" — ton IA locale (modèle : {self.model}). Tape /aide pour l'aide.")
        while True:
            try:
                text = input(self.paint(BOLD, "\nToi › "))
            except (EOFError, KeyboardInterrupt):
                print("\nÀ bientôt !")
                return 0
            text = text.strip()
            if not text:
                continue
            if text.startswith("/"):
                if self.command(text) == "quit":
                    print("À bientôt !")
                    return 0
                continue
            self.answer(text)

    def command(self, line: str) -> str | None:
        command, _, argument = line.partition(" ")
        argument = argument.strip()
        if command in ("/quitter", "/quit", "/exit"):
            return "quit"
        if command == "/aide":
            print(HELP)
        elif command == "/nouveau":
            self.conversation = self.assistant.store.new()
            print("Nouvelle conversation.")
        elif command == "/modeles":
            try:
                for model in self.assistant.list_models():
                    marker = "→" if model["name"] == self.model else " "
                    print(f" {marker} {model['name']}  ({model['size'] / 1e9:.1f} Go)")
            except AssistantError as exc:
                print(self.paint(RED, f"⚠ {exc}"))
        elif command == "/modele":
            if not argument:
                print(f"Modèle actuel : {self.model}")
            else:
                self.model = argument
                print(f"Modèle : {self.model}")
        elif command == "/reflexion":
            self.thinking = not self.thinking
            print(f"Réflexion approfondie : {'activée' if self.thinking else 'désactivée'}.")
        elif command == "/memoire":
            print(self.assistant.memory.read().strip() or "(Ta mémoire est vide pour l'instant.)")
        else:
            print(f"Commande inconnue : {command}. Tape /aide pour la liste.")
        return None

    def answer(self, text: str) -> None:
        print(self.paint(BOLD + CYAN, f"\n{self.assistant.profile.name} ›"), end=" ", flush=True)
        events = self.assistant.chat(self.conversation, text, model=self.model, thinking=self.thinking)
        thinking_shown = False
        try:
            for event in events:
                kind = event["type"]
                if kind == "thinking":
                    if self.show_thinking:
                        print(self.paint(DIM, event["text"]), end="", flush=True)
                    elif not thinking_shown:
                        print(self.paint(DIM, "(réfléchit…)"), end=" ", flush=True)
                    thinking_shown = True
                elif kind == "text":
                    if thinking_shown:
                        print("\n")
                        thinking_shown = False
                    print(event["text"], end="", flush=True)
                elif kind == "tool_call":
                    print(self.paint(YELLOW, f"\n  ⚙ {event['label']}"), end="", flush=True)
                elif kind == "tool_result":
                    print(self.paint(RED if event["error"] else DIM, f" → {event['summary']}"), flush=True)
                elif kind == "notice":
                    print(self.paint(YELLOW, f"\n  ℹ {event['message']}"), flush=True)
                elif kind == "error":
                    print(self.paint(RED, f"\n  ⚠ {event['message']}"), flush=True)
                elif kind == "done":
                    stats = event["stats"]
                    if stats.get("speed"):
                        print(self.paint(DIM, f"\n  [{stats['tokens']} tokens · {stats['speed']} tokens/s]"), end="")
        except KeyboardInterrupt:
            events.close()
            print(self.paint(YELLOW, "\n  [réponse interrompue]"), end="")
        print()
