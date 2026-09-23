import base64
import json

import pytest
from fastapi.testclient import TestClient

from conftest import chunks
from mon_ia.web import create_app


@pytest.fixture
def client(assistant):
    return TestClient(create_app(assistant), base_url="http://127.0.0.1:8000")


def events(response):
    assert response.status_code == 200
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


def test_page_and_scripts_are_served(client):
    assert "Mon IA" in client.get("/").text
    for path in ("/static/app.js", "/static/style.css", "/static/vendor/marked.umd.js", "/static/vendor/purify.min.js"):
        assert client.get(path).status_code == 200


def test_other_websites_cannot_talk_to_the_ai(assistant):
    foreign = TestClient(create_app(assistant), base_url="http://site-malveillant.example")
    assert foreign.get("/api/infos").status_code == 400


def test_infos_and_models(client):
    assert client.get("/api/infos").json() == {
        "name": "Nova",
        "version": "1.0.0",
        "thinking": False,
        "web_search": True,
        "context_size": 8192,
    }
    models = client.get("/api/modeles").json()
    assert models["ok"] is True
    assert models["default"] == "qwen3:8b"


def test_full_conversation(client, fake):
    fake.replies += [chunks("Salut !"), chunks("Re !")]

    first = events(client.post("/api/chat", json={"message": "Coucou", "model": "qwen3:8b"}))
    conversation_id = first[0]["id"]
    events(client.post("/api/chat", json={"conversation_id": conversation_id, "message": "Encore", "model": "qwen3:8b"}))

    assert first[-1]["type"] == "done"
    assert [item["id"] for item in client.get("/api/conversations").json()] == [conversation_id]
    detail = client.get(f"/api/conversations/{conversation_id}").json()
    assert detail["title"] == "Coucou"
    assert [item["text"] for item in detail["messages"]] == ["Coucou", "Salut !", "Encore", "Re !"]
    assert len(fake.chat_requests[1]["messages"]) == 4

    assert client.delete(f"/api/conversations/{conversation_id}").json() == {"ok": True}
    assert client.get(f"/api/conversations/{conversation_id}").status_code == 404
    assert client.delete(f"/api/conversations/{conversation_id}").status_code == 404


def test_chat_with_a_document(client, fake):
    fake.replies.append(chunks("Une liste de courses."))
    document = {"name": "courses.txt", "type": "text/plain", "data": base64.b64encode("pain\nlait".encode()).decode()}

    events(client.post("/api/chat", json={"message": "Résume", "attachments": [document], "model": "qwen3:8b"}))

    assert "--- Début du fichier « courses.txt » ---\npain\nlait" in fake.chat_requests[0]["messages"][-1]["content"]


def test_bad_requests_are_explained(client):
    empty = client.post("/api/chat", json={"message": "   "})
    broken = client.post("/api/chat", json={"message": "Lis", "attachments": [{"name": "a.bin", "type": "", "data": base64.b64encode(b"\x00\x01").decode()}]})
    unknown = client.post("/api/chat", json={"conversation_id": "0" * 32, "message": "Salut"})

    assert empty.status_code == 400 and empty.json()["detail"] == "Le message est vide."
    assert broken.status_code == 400 and "format non pris en charge" in broken.json()["detail"]
    assert unknown.status_code == 404
    assert client.get("/api/conversations/..%2F..%2Fsecret").status_code == 404


def test_memory_can_be_read_and_edited(client):
    assert client.get("/api/memoire").json() == {"text": ""}
    assert client.put("/api/memoire", json={"text": "- J'aime le jazz\n"}).json() == {"text": "- J'aime le jazz\n"}
    assert client.get("/api/memoire").json()["text"] == "- J'aime le jazz\n"


def test_name_and_personality_can_be_changed(client, fake):
    changed = client.put("/api/profil", json={"name": "Jarvis", "personality": "Tu es {nom}, un majordome."}).json()
    fake.replies.append(chunks("Monsieur ?"))
    events(client.post("/api/chat", json={"message": "Salut", "model": "qwen3:8b"}))

    assert changed == {"name": "Jarvis", "personality": "Tu es {nom}, un majordome.\n"}
    assert client.get("/api/infos").json()["name"] == "Jarvis"
    assert fake.chat_requests[0]["messages"][0]["content"].startswith("Tu es Jarvis, un majordome.")
    assert client.put("/api/profil", json={"name": "", "personality": "x"}).status_code == 400


def test_model_download_progress(client):
    progress = events(client.post("/api/modeles/telecharger", json={"model": "qwen3:4b"}))

    assert progress[0]["type"] == "progress"
    assert progress[-1] == {"type": "done", "model": "qwen3:4b"}


# --- Mode partage -------------------------------------------------------------------------


@pytest.fixture
def shared(make_assistant, config):
    config.password = "motdepasse-admin"
    config.friends = {"leo": "soleil42", "sam": "banane77"}
    app = create_app(make_assistant())
    return lambda: TestClient(app, base_url="https://abc-def.trycloudflare.com")


def login(client, pseudo, password):
    return client.post("/api/connexion", json={"pseudo": pseudo, "password": password})


def test_sharing_requires_a_login(shared):
    client = shared()

    assert client.get("/").status_code == 200
    assert client.get("/api/session").json() == {"sharing": True, "user": None, "owner": False}
    for path in ("/api/infos", "/api/modeles", "/api/conversations", "/api/memoire", "/api/profil"):
        assert client.get(path).status_code == 401
    assert client.post("/api/chat", json={"message": "Salut"}).status_code == 401


def test_wrong_passwords_are_refused_then_blocked(shared):
    client = shared()

    assert login(client, "leo", "mauvais").status_code == 401
    assert login(client, "inconnu", "soleil42").status_code == 401
    assert login(client, "sam", "soleil42").status_code == 401
    for _ in range(5):
        login(client, "leo", "mauvais")
    blocked = login(client, "leo", "soleil42")

    assert blocked.status_code == 429
    assert "Trop d'essais" in blocked.json()["detail"]


def test_each_friend_has_a_private_space(shared, fake):
    leo, sam, admin = shared(), shared(), shared()
    assert login(leo, "LEO", "soleil42").json() == {"user": "leo", "owner": False}
    assert login(sam, "sam", "banane77").status_code == 200
    assert login(admin, "admin", "motdepasse-admin").json() == {"user": "admin", "owner": True}
    fake.replies += [chunks("Salut Léo !"), chunks("Salut Sam !")]

    leo_conversation = events(leo.post("/api/chat", json={"message": "Coucou", "model": "qwen3:8b"}))[0]["id"]
    events(sam.post("/api/chat", json={"message": "Yo", "model": "qwen3:8b"}))
    leo.put("/api/memoire", json={"text": "- Il joue au basket\n"})

    assert [item["title"] for item in leo.get("/api/conversations").json()] == ["Coucou"]
    assert [item["title"] for item in sam.get("/api/conversations").json()] == ["Yo"]
    assert admin.get("/api/conversations").json() == []
    assert sam.get(f"/api/conversations/{leo_conversation}").status_code == 404
    assert sam.delete(f"/api/conversations/{leo_conversation}").status_code == 404
    assert sam.get("/api/memoire").json() == {"text": ""}
    assert admin.get("/api/memoire").json() == {"text": ""}
    assert "Tu discutes en ce moment avec Leo" in fake.chat_requests[0]["messages"][0]["content"]


def test_only_the_owner_changes_the_ai(shared):
    leo, admin = shared(), shared()
    login(leo, "leo", "soleil42")
    login(admin, "admin", "motdepasse-admin")
    profile = {"name": "Jarvis", "personality": "Tu es {nom}."}

    assert leo.get("/api/profil").status_code == 200
    assert leo.put("/api/profil", json=profile).status_code == 403
    assert leo.post("/api/modeles/telecharger", json={"model": "qwen3:4b"}).status_code == 403
    assert admin.put("/api/profil", json=profile).status_code == 200
    assert leo.get("/api/session").json() == {"sharing": True, "user": "leo", "owner": False}


def test_forged_or_outdated_sessions_are_refused(shared, make_assistant, config):
    client = shared()
    login(client, "leo", "soleil42")
    cookie = client.cookies.get("monia_session")
    payload, signature = cookie.rsplit(".", 1)
    forged_payload = base64.urlsafe_b64encode(json.dumps({"u": "admin", "v": "x", "exp": 9999999999}).encode()).decode()

    for bad in (f"{forged_payload}.{signature}", f"{payload}.{'0' * 64}", "nimportequoi"):
        other = shared()
        other.cookies.set("monia_session", bad)
        assert other.get("/api/conversations").status_code == 401

    config.friends = {"leo": "nouveau-mdp"}  # mot de passe changé dans .env puis IA relancée
    relaunched = TestClient(create_app(make_assistant()), base_url="https://abc-def.trycloudflare.com")
    relaunched.cookies.set("monia_session", cookie)
    assert relaunched.get("/api/conversations").status_code == 401


def test_logout(shared):
    client = shared()
    login(client, "leo", "soleil42")

    client.post("/api/deconnexion")

    assert client.get("/api/conversations").status_code == 401
