"""Les outils que l'IA peut utiliser pendant une conversation.

Tout est gratuit et sans compte : la mémoire, le calcul et l'heure sont 100 % locaux ; la
recherche web interroge des moteurs publics (DuckDuckGo, Bing, Wikipédia…) via le paquet `ddgs`.
"""

from __future__ import annotations

import ast
import ipaddress
import logging
import math
import operator
import socket
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping

from .memory import Memory
from .profile import french_date

log = logging.getLogger(__name__)

SEARCH_RESULTS = 5


class ToolFailure(Exception):
    """Erreur prévue, expliquée à l'IA pour qu'elle puisse corriger son appel."""


@dataclass
class ToolResult:
    content: str  # ce que lit l'IA
    summary: str  # le résumé affiché à l'écran
    error: bool = False


def _definition(name: str, description: str, **properties: str) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {key: {"type": "string", "description": text} for key, text in properties.items()},
                "required": list(properties),
            },
        },
    }


DEFINITIONS = {
    "memoriser": _definition(
        "memoriser",
        "Enregistre une information durable dans ta mémoire à long terme. À utiliser de toi-même dès que "
        "l'utilisateur t'apprend quelque chose d'important sur lui (prénom, goûts, projets, proches, "
        "préférences…) ou te demande de retenir quelque chose.",
        information="L'information à retenir, en une phrase courte qui se comprend seule. "
        "Exemple : « Il s'appelle Léo et joue au basket le samedi. »",
    ),
    "oublier": _definition(
        "oublier",
        "Efface de ta mémoire à long terme les souvenirs qui contiennent un texte donné. À utiliser quand "
        "l'utilisateur te demande d'oublier quelque chose.",
        texte="Un mot ou un extrait du souvenir à effacer.",
    ),
    "recherche_web": _definition(
        "recherche_web",
        "Cherche sur internet. À utiliser pour l'actualité, les informations récentes ou quand tu dois "
        "vérifier un fait précis dont tu n'es pas sûr.",
        requete="Les mots-clés de la recherche.",
    ),
    "lire_page_web": _definition(
        "lire_page_web",
        "Lit le texte d'une page web à partir de son adresse (un résultat de recherche ou un lien donné par "
        "l'utilisateur).",
        url="L'adresse complète de la page, qui commence par http:// ou https://.",
    ),
    "calculer": _definition(
        "calculer",
        "Calcule une expression mathématique de façon exacte. À utiliser pour tous les calculs, même simples. "
        "Opérations : + - * / // % ** ; fonctions : sqrt, sin, cos, tan, log, ln, log10, exp, abs, round, "
        "floor, ceil, min, max, factorial ; constantes : pi, e.",
        expression="L'expression à calculer, par exemple (12.5 * 4) / 3 ou sqrt(2) ** 10.",
    ),
    "date_heure": _definition("date_heure", "Donne la date et l'heure exactes en ce moment."),
}

GUIDE = {
    "memoriser": "- memoriser / oublier : ta mémoire à long terme. Retiens de toi-même ce que l'utilisateur "
    "t'apprend d'important sur lui, sans lui demander la permission.",
    "recherche_web": "- recherche_web puis lire_page_web : pour l'actualité et les faits récents. Indique tes "
    "sources (les adresses des pages).",
    "calculer": "- calculer : pour tous les calculs, au lieu de calculer de tête.",
    "date_heure": "- date_heure : pour connaître l'heure exacte.",
}


# --- Calculatrice sûre : seules les opérations mathématiques sont autorisées -----------------

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "sqrt": math.sqrt,
    "racine": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "ln": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "arrondi": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "min": min,
    "max": max,
    "factorial": math.factorial,
    "hypot": math.hypot,
    "degrees": math.degrees,
    "radians": math.radians,
}
_CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}


def _evaluate(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.Name) and node.id in _CONSTANTS:
        return _CONSTANTS[node.id]
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        left, right = _evaluate(node.left), _evaluate(node.right)
        # Sans cette limite, 9**9**9 bloquerait l'ordinateur pendant des heures.
        if isinstance(node.op, ast.Pow) and (abs(right) > 1000 or (abs(left) > 10**100 and abs(right) > 1)):
            raise ToolFailure("puissance trop grande")
        return _BINARY_OPS[type(node.op)](left, right)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FUNCTIONS
        and not node.keywords
        and len(node.args) <= 10
    ):
        args = [_evaluate(arg) for arg in node.args]
        if node.func.id == "factorial" and args and isinstance(args[0], (int, float)) and args[0] > 1000:
            raise ToolFailure("factorielle trop grande (maximum 1000)")
        return _FUNCTIONS[node.func.id](*args)
    raise ToolFailure("seuls les nombres, les opérations et les fonctions mathématiques sont autorisés")


def calculate(expression: str) -> int | float:
    expression = expression.strip().replace("^", "**").replace("×", "*").replace("÷", "/").replace("−", "-")
    if len(expression) > 300:
        raise ToolFailure("expression trop longue")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise ToolFailure(f"expression invalide : {expression}") from None
    try:
        return _evaluate(tree.body)
    except ZeroDivisionError:
        raise ToolFailure("division par zéro") from None
    except OverflowError:
        raise ToolFailure("résultat trop grand") from None
    except (ValueError, TypeError) as exc:
        raise ToolFailure(f"calcul impossible ({exc})") from None


def format_number(value: int | float) -> str:
    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer() and abs(value) < 1e16:
            return str(int(value))
        return f"{value:.12g}"
    try:
        text = str(value)
    except ValueError:  # entier de plus de 4300 chiffres
        text = ""
    if text and len(text.lstrip("-")) <= 40:
        return text
    exponent = int(math.log10(abs(value)))
    mantissa = str(abs(value) // 10 ** (exponent - 10))
    sign = "-" if value < 0 else ""
    return f"{sign}{mantissa[0]}.{mantissa[1:]}e+{exponent}"


# --- Web -----------------------------------------------------------------------------------


def check_public_url(url: str) -> str:
    """Refuse les adresses locales ou privées (box internet, NAS, Ollama lui-même…)."""
    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ToolFailure("adresse invalide : elle doit commencer par http:// ou https://")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except (socket.gaierror, UnicodeError):
        raise ToolFailure(f"site introuvable : {parsed.hostname}") from None
    for info in infos:
        address = ipaddress.ip_address(str(info[4][0]).split("%")[0])
        if not address.is_global:
            raise ToolFailure("les adresses locales ou privées ne sont pas autorisées")
    return url.strip()


def ddgs_search(query: str, region: str, max_results: int) -> list[dict[str, Any]]:
    from ddgs import DDGS

    return DDGS(timeout=10).text(query, region=region, max_results=max_results)


def ddgs_fetch(url: str) -> str:
    from ddgs import DDGS

    content = DDGS(timeout=15).extract(url, fmt="text_markdown")["content"]
    return content if isinstance(content, str) else content.decode("utf-8", "replace")


# --- Boîte à outils ------------------------------------------------------------------------


def _text_argument(arguments: Mapping[str, Any], key: str) -> str:
    value = arguments.get(key)
    if value is None and len(arguments) == 1:
        # Les petits modèles se trompent parfois de nom de paramètre : on reste tolérant.
        value = next(iter(arguments.values()))
    if value is None:
        raise ToolFailure(f"le paramètre « {key} » est manquant")
    text = value if isinstance(value, str) else str(value)
    if not text.strip():
        raise ToolFailure(f"le paramètre « {key} » est vide")
    return text.strip()


class Toolbox:
    def __init__(
        self,
        memory: Memory,
        *,
        web: bool = True,
        region: str = "fr-fr",
        page_chars: int = 10000,
        search: Callable[[str, str, int], list[dict[str, Any]]] = ddgs_search,
        fetch: Callable[[str], str] = ddgs_fetch,
        clock: Callable[[], datetime] = lambda: datetime.now().astimezone(),
    ) -> None:
        self.memory = memory
        self.region = region
        self.page_chars = page_chars
        self._search_fn = search
        self._fetch_fn = fetch
        self._clock = clock
        self._handlers: dict[str, Callable[[Mapping[str, Any]], ToolResult]] = {
            "memoriser": self._remember,
            "oublier": self._forget,
            "calculer": self._calculate,
            "date_heure": self._now,
        }
        if web:
            self._handlers["recherche_web"] = self._search
            self._handlers["lire_page_web"] = self._read_page

    @property
    def names(self) -> list[str]:
        return list(self._handlers)

    def definitions(self) -> list[dict[str, Any]]:
        return [DEFINITIONS[name] for name in self._handlers]

    def guide(self) -> str:
        lines = [GUIDE[name] for name in self._handlers if name in GUIDE]
        return "\n".join(lines + ["Après avoir utilisé un outil, réponds normalement à l'utilisateur."])

    @staticmethod
    def describe(name: str, arguments: Mapping[str, Any]) -> str:
        """Libellé lisible d'un appel d'outil, pour l'affichage."""
        value = next((str(v) for v in arguments.values() if v), "") if isinstance(arguments, Mapping) else ""
        short = value if len(value) <= 80 else value[:79] + "…"
        if name == "memoriser":
            return "Mémorisation"
        if name == "oublier":
            return f"Oubli : « {short} »"
        if name == "recherche_web":
            return f"Recherche web : « {short} »"
        if name == "lire_page_web":
            return f"Lecture de {urllib.parse.urlparse(value).hostname or short}"
        if name == "calculer":
            return f"Calcul : {short}"
        if name == "date_heure":
            return "Date et heure"
        return f"Outil {name}"

    def run(self, name: str, arguments: Any) -> ToolResult:
        handler = self._handlers.get(name)
        if handler is None:
            return ToolResult(f"Erreur : l'outil « {name} » n'existe pas.", f"Outil inconnu : {name}", error=True)
        try:
            return handler(arguments if isinstance(arguments, Mapping) else {})
        except ToolFailure as exc:
            return ToolResult(f"Erreur : {exc}.", str(exc).capitalize(), error=True)
        except Exception as exc:
            log.exception("L'outil %s a planté", name)
            return ToolResult(f"Erreur inattendue : {exc}.", "Erreur inattendue", error=True)

    def _remember(self, arguments: Mapping[str, Any]) -> ToolResult:
        fact = _text_argument(arguments, "information")
        try:
            added = self.memory.add(fact)
        except ValueError as exc:
            raise ToolFailure(str(exc)) from None
        if added:
            return ToolResult("C'est enregistré dans ta mémoire.", f"Retenu : {fact}")
        return ToolResult("C'était déjà dans ta mémoire.", "Déjà en mémoire")

    def _forget(self, arguments: Mapping[str, Any]) -> ToolResult:
        text = _text_argument(arguments, "texte")
        try:
            removed = self.memory.forget(text)
        except ValueError as exc:
            raise ToolFailure(str(exc)) from None
        if not removed:
            return ToolResult(f"Aucun souvenir ne contient « {text} ».", "Aucun souvenir correspondant")
        listing = "\n".join(f"- {fact}" for fact in removed)
        plural = "s" if len(removed) > 1 else ""
        return ToolResult(f"Souvenirs effacés :\n{listing}", f"{len(removed)} souvenir{plural} effacé{plural}")

    def _calculate(self, arguments: Mapping[str, Any]) -> ToolResult:
        expression = _text_argument(arguments, "expression")
        result = format_number(calculate(expression))
        return ToolResult(f"{expression} = {result}", f"= {result}")

    def _now(self, arguments: Mapping[str, Any]) -> ToolResult:
        moment = self._clock()
        text = f"{french_date(moment)}, {moment:%H:%M}"
        timezone = moment.tzname()
        return ToolResult(f"Nous sommes le {text}" + (f" (fuseau horaire : {timezone})." if timezone else "."), text)

    def _search(self, arguments: Mapping[str, Any]) -> ToolResult:
        query = _text_argument(arguments, "requete")
        try:
            results = self._search_fn(query, self.region, SEARCH_RESULTS)
        except ImportError:
            raise ToolFailure("la recherche web n'est pas installée (commande : pip install ddgs)") from None
        except Exception as exc:
            if "no results" in str(exc).lower():
                results = []
            else:
                raise ToolFailure(f"la recherche a échoué ({exc})") from None
        if not results:
            return ToolResult(f"Aucun résultat pour « {query} ».", "Aucun résultat")
        lines = [f"Résultats de recherche pour « {query} » :"]
        for index, result in enumerate(results, start=1):
            lines.append(f"\n{index}. {result.get('title', '').strip()}\n   {result.get('href', '')}\n   {result.get('body', '').strip()}")
        plural = "s" if len(results) > 1 else ""
        return ToolResult("\n".join(lines), f"{len(results)} résultat{plural}")

    def _read_page(self, arguments: Mapping[str, Any]) -> ToolResult:
        url = check_public_url(_text_argument(arguments, "url"))
        try:
            text = self._fetch_fn(url)
        except ImportError:
            raise ToolFailure("la lecture de pages web n'est pas installée (commande : pip install ddgs)") from None
        except Exception as exc:
            raise ToolFailure(f"impossible de lire la page ({exc})") from None
        text = text.strip()
        if not text:
            raise ToolFailure("la page ne contient pas de texte lisible")
        total = len(text)
        if total > self.page_chars:
            text = text[: self.page_chars] + f"\n\n[… page tronquée : {total} caractères au total]"
        return ToolResult(f"Contenu de {url} :\n\n{text}", f"Page lue ({total:,} caractères)".replace(",", " "))
