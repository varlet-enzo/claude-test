from datetime import datetime

import pytest

from mon_ia.memory import Memory
from mon_ia.profile import DEFAULT_PERSONALITY, Profile
from mon_ia.storage import ConversationStore, display_messages, make_title


def test_conversations_are_saved_listed_and_deleted(tmp_path):
    store = ConversationStore(tmp_path)
    first, second = store.new(), store.new()
    first["title"], second["title"] = "Première", "Seconde"
    store.save(first)
    store.save(second)
    first["updated_at"] = "2099-01-01T00:00:00"
    (tmp_path / f"{first['id']}.json").write_text(__import__("json").dumps(first), encoding="utf-8")

    assert [item["title"] for item in store.list()] == ["Première", "Seconde"]
    assert store.load(second["id"])["title"] == "Seconde"
    store.delete(second["id"])
    with pytest.raises(KeyError):
        store.load(second["id"])


@pytest.mark.parametrize("bad_id", ["../../etc/passwd", "", "ABC", "0" * 31])
def test_invalid_conversation_ids_are_refused(tmp_path, bad_id):
    with pytest.raises(KeyError):
        ConversationStore(tmp_path).load(bad_id)


def test_titles():
    assert make_title("\n  Bonjour toi  \nsuite") == "Bonjour toi"
    assert make_title("") == "Nouvelle conversation"
    assert make_title("a" * 100) == "a" * 59 + "…"


def test_display_merges_a_whole_turn():
    messages = [
        {"role": "user", "content": "Doc: ...", "display": "Résume", "attachments": ["a.jpg", "b.pdf"], "images": ["QUJD"]},
        {"role": "assistant", "content": "", "thinking": "Hmm", "tool_calls": [{"function": {"name": "calculer", "arguments": {}}}]},
        {"role": "tool", "tool_name": "calculer", "content": "= 2", "label": "Calcul : 1+1", "summary": "= 2", "error": False},
        {"role": "assistant", "content": "Deux.", "model": "qwen3:8b", "stats": {"tokens": 3, "speed": 9.5}, "notices": ["Info"]},
    ]

    user, bubble = display_messages(messages)

    assert user == {"role": "user", "text": "Résume", "attachments": ["a.jpg", "b.pdf"], "images": ["data:image/jpeg;base64,QUJD"]}
    assert bubble == {
        "role": "assistant",
        "text": "Deux.",
        "thinking": "Hmm",
        "tools": [{"name": "calculer", "label": "Calcul : 1+1", "summary": "= 2", "error": False}],
        "notices": ["Info"],
        "model": "qwen3:8b",
        "stats": {"tokens": 3, "speed": 9.5},
    }


def test_memory_keeps_the_most_recent_facts_when_too_long(tmp_path):
    memory = Memory(tmp_path / "memoire.md", max_prompt_chars=40)
    for fact in ["Fait numéro un", "Fait numéro deux", "Fait numéro trois"]:
        memory.add(fact)

    prompt = memory.for_prompt()

    assert "Fait numéro trois" in prompt
    assert "Fait numéro un" not in prompt
    assert "Mémoire trop longue" in prompt


def test_memory_can_be_edited_by_hand(tmp_path):
    memory = Memory(tmp_path / "memoire.md")
    memory.write("# Moi\n\nJ'habite à Lyon.\n* Je code en Python\n")

    assert memory.facts() == ["J'habite à Lyon.", "Je code en Python"]
    assert memory.add("Je code en python") is False
    assert memory.forget("lyon") == ["J'habite à Lyon."]
    assert memory.read() == "# Moi\n\n* Je code en Python\n"


def test_forgetting_needs_a_precise_request(tmp_path):
    memory = Memory(tmp_path / "memoire.md")
    for index in range(7):
        memory.add(f"Souvenir de vacances numéro {index}")

    with pytest.raises(ValueError, match="au moins 3 caractères"):
        memory.forget("a")
    with pytest.raises(ValueError, match="7 souvenirs"):
        memory.forget("vacances")
    assert len(memory.facts()) == 7
    assert memory.forget("numéro 3") == ["Souvenir de vacances numéro 3"]


def test_profile_name_and_personality(tmp_path):
    profile = Profile(tmp_path, "Nova")
    assert profile.name == "Nova"
    assert profile.personality == DEFAULT_PERSONALITY

    profile.set_name("  Jarvis  ")
    profile.set_personality("Tu es {nom}, un majordome très poli.")
    prompt = profile.system_prompt(memory="", tool_guide="", now=datetime(2026, 1, 1))

    assert Profile(tmp_path, "Nova").name == "Jarvis"
    assert prompt.startswith("Tu es Jarvis, un majordome très poli.")
    assert "jeudi 1 janvier 2026" in prompt
    assert "Tu ne sais encore rien sur lui" in prompt
    assert "Tu n'as pas accès à internet" in prompt
    with pytest.raises(ValueError):
        profile.set_name(" ")
    profile.set_personality("   ")
    assert profile.personality == DEFAULT_PERSONALITY
