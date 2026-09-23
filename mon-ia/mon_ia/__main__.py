"""Point d'entrée : `python -m mon_ia` (interface web) ou `python -m mon_ia chat` (terminal)."""

from __future__ import annotations

import argparse
import logging
import socket
import sys
import threading
import webbrowser

from . import __version__
from .assistant import Assistant
from .config import Config


def _already_listening(host: str, port: int) -> bool:
    # On teste une connexion plutôt qu'un bind : juste après un redémarrage, le port reste
    # réservé quelques secondes par le système alors que le serveur peut démarrer sans souci.
    target = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    try:
        with socket.create_connection((target, port), timeout=0.5):
            return True
    except OSError:
        return False


def run_web(assistant: Assistant, host: str, port: int, open_browser: bool) -> int:
    import uvicorn

    from .web import create_app

    url = f"http://{'127.0.0.1' if host in ('0.0.0.0', '::') else host}:{port}"
    if _already_listening(host, port):
        print(f"Le port {port} est déjà utilisé : ton IA est peut-être déjà lancée ({url}).")
        print("Sinon, choisis un autre port avec IA_PORT dans le fichier .env.")
        if open_browser:
            webbrowser.open(url)
        return 1
    print(f"\n  ✦ {assistant.profile.name} est prête : {url}")
    print("  Garde cette fenêtre ouverte pendant que tu l'utilises (Ctrl+C pour arrêter).\n")
    if open_browser:
        threading.Timer(1.5, webbrowser.open, args=(url,)).start()
    uvicorn.run(create_app(assistant), host=host, port=port, log_level="warning")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Évite un plantage si la console ne sait pas afficher certains caractères (émojis…).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    parser = argparse.ArgumentParser(
        prog="python -m mon_ia", description="Ton IA personnelle, 100 % locale et gratuite (grâce à Ollama)."
    )
    parser.add_argument("--version", action="version", version=f"Mon IA {__version__}")
    modes = parser.add_subparsers(dest="mode", metavar="{web,chat}")
    web = modes.add_parser("web", help="ouvrir l'interface dans le navigateur (par défaut)")
    web.add_argument("--port", type=int, help="port de l'interface (par défaut 8000)")
    web.add_argument("--hote", help="adresse d'écoute (par défaut 127.0.0.1 : ton ordinateur uniquement)")
    web.add_argument("--sans-navigateur", action="store_true", help="ne pas ouvrir le navigateur automatiquement")
    chat = modes.add_parser("chat", help="discuter dans le terminal")
    chat.add_argument("--modele", help="modèle à utiliser, par exemple qwen3:8b")
    chat.add_argument("--reflexion", action="store_true", help="activer la réflexion approfondie")
    chat.add_argument("--voir-reflexion", action="store_true", help="afficher la réflexion du modèle")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s : %(message)s")
    config = Config.load()

    if args.mode == "chat":
        from .cli import Terminal

        terminal = Terminal(
            Assistant(config),
            model=args.modele,
            thinking=args.reflexion or config.thinking,
            show_thinking=args.voir_reflexion,
        )
        return terminal.run()

    config.host = getattr(args, "hote", None) or config.host
    config.port = getattr(args, "port", None) or config.port
    return run_web(Assistant(config), config.host, config.port, not getattr(args, "sans_navigateur", False))


if __name__ == "__main__":
    sys.exit(main())
