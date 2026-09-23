from datetime import datetime, timedelta, timezone

import pytest

from mon_ia.memory import Memory
from mon_ia.tools import Toolbox, ToolFailure, calculate, check_public_url, format_number


@pytest.fixture
def memory(tmp_path):
    return Memory(tmp_path / "memoire.md")


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2 + 2", "4"),
        ("12.5 * 4 / 3", "16.6666666667"),
        ("2^10", "1024"),
        ("sqrt(2) ** 2", "2"),
        ("-(3 - 10) % 4", "3"),
        ("round(pi, 3)", "3.142"),
        ("max(1, 7, 3) + factorial(5)", "127"),
        ("10 ÷ 4 × 2", "5"),
        ("9 ** 999", "1.9420791685e+953"),
    ],
)
def test_calculator(expression, expected):
    assert format_number(calculate(expression)) == expected


@pytest.mark.parametrize(
    "expression",
    ['__import__("os").system("ls")', "().__class__", "9 ** 9 ** 9", "factorial(5000)", "1 / 0", "x + 1", "2 +", "True + 1"],
)
def test_calculator_refuses_anything_else(expression):
    with pytest.raises(ToolFailure):
        calculate(expression)


@pytest.mark.parametrize(
    "url",
    ["http://127.0.0.1:11434/api/tags", "http://192.168.1.1/", "http://10.0.0.8/admin", "http://[::1]/", "file:///etc/passwd", "ftp://93.184.216.34/", "pas une adresse"],
)
def test_local_and_invalid_urls_are_refused(url):
    with pytest.raises(ToolFailure):
        check_public_url(url)


def test_public_ip_is_allowed():
    assert check_public_url(" http://93.184.216.34/page ") == "http://93.184.216.34/page"


def test_web_tools_can_be_disabled(memory):
    assert Toolbox(memory, web=False).names == ["memoriser", "oublier", "calculer", "date_heure"]
    assert "recherche_web" not in Toolbox(memory, web=False).guide()


def test_remember_and_forget(memory):
    toolbox = Toolbox(memory, web=False)

    assert toolbox.run("memoriser", {"information": "Il adore les chats."}).summary == "Retenu : Il adore les chats."
    assert toolbox.run("memoriser", {"information": "il adore les chats."}).summary == "Déjà en mémoire"
    assert toolbox.run("oublier", {"texte": "chats"}).summary == "1 souvenir effacé"
    assert toolbox.run("oublier", {"texte": "chats"}).summary == "Aucun souvenir correspondant"
    assert toolbox.run("memoriser", {"information": "   "}).error


def test_wrong_parameter_names_are_tolerated(memory):
    assert Toolbox(memory, web=False).run("calculer", {"expr": "6 * 7"}).summary == "= 42"


def test_errors_are_reported_to_the_model(memory):
    toolbox = Toolbox(memory, web=False)

    unknown = toolbox.run("pirater", {})
    missing = toolbox.run("calculer", {})

    assert unknown.error and "n'existe pas" in unknown.content
    assert missing.error and "expression" in missing.content


def test_date_and_time(memory):
    paris = timezone(timedelta(hours=2), "CEST")
    toolbox = Toolbox(memory, clock=lambda: datetime(2026, 9, 23, 14, 5, tzinfo=paris))

    result = toolbox.run("date_heure", {})

    assert result.summary == "mercredi 23 septembre 2026, 14:05"
    assert result.content == "Nous sommes le mercredi 23 septembre 2026, 14:05 (fuseau horaire : CEST)."


def test_web_search_results_are_formatted(memory):
    calls = []

    def search(query, region, max_results):
        calls.append((query, region, max_results))
        return [{"title": "Météo Paris", "href": "https://meteo.example/paris", "body": "Soleil, 24 °C."}]

    result = Toolbox(memory, search=search).run("recherche_web", {"requete": "météo Paris"})

    assert calls == [("météo Paris", "fr-fr", 5)]
    assert result.summary == "1 résultat"
    assert "1. Météo Paris\n   https://meteo.example/paris\n   Soleil, 24 °C." in result.content


def test_web_search_failure_does_not_crash(memory):
    def search(query, region, max_results):
        raise RuntimeError("trop de requêtes")

    result = Toolbox(memory, search=search).run("recherche_web", {"requete": "actualités"})

    assert result.error
    assert "trop de requêtes" in result.content


def test_read_page_is_truncated(memory):
    toolbox = Toolbox(memory, page_chars=100, fetch=lambda url: "a" * 4000)

    result = toolbox.run("lire_page_web", {"url": "http://93.184.216.34/article"})

    assert result.summary == "Page lue (4 000 caractères)"
    assert "[… page tronquée : 4000 caractères au total]" in result.content


def test_read_page_refuses_local_addresses(memory):
    result = Toolbox(memory, fetch=lambda url: "secret").run("lire_page_web", {"url": "http://192.168.1.1/"})

    assert result.error
    assert "secret" not in result.content


def test_labels():
    assert Toolbox.describe("recherche_web", {"requete": "météo"}) == "Recherche web : « météo »"
    assert Toolbox.describe("lire_page_web", {"url": "https://fr.wikipedia.org/wiki/Paris"}) == "Lecture de fr.wikipedia.org"
    assert Toolbox.describe("memoriser", {"information": "secret"}) == "Mémorisation"
