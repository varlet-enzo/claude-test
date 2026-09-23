import httpx

from conftest import chunks, ndjson
from mon_ia.assistant import MAX_TOOL_ROUNDS, Assistant
from mon_ia.storage import display_messages


def texts(events, kind="text"):
    return "".join(event["text"] for event in events if event["type"] == kind)


def test_answer_is_streamed_and_saved(assistant, fake):
    fake.replies.append(chunks("Bonjour Léo, ravi de te voir !"))
    conversation = assistant.store.new()

    events = list(assistant.chat(conversation, "Salut", model="qwen3:8b"))

    assert events[0] == {"type": "conversation", "id": conversation["id"], "title": "Salut"}
    assert texts(events) == "Bonjour Léo, ravi de te voir !"
    assert events[-1] == {"type": "done", "model": "qwen3:8b", "stats": {"tokens": 20, "speed": 20.0}}
    saved = assistant.store.load(conversation["id"])
    assert saved["title"] == "Salut"
    assert [message["role"] for message in saved["messages"]] == ["user", "assistant"]
    assert saved["messages"][1]["content"] == "Bonjour Léo, ravi de te voir !"

    request = fake.chat_requests[0]
    assert request["messages"][0]["role"] == "system"
    assert "Tu es Nova" in request["messages"][0]["content"]
    assert "mercredi 23 septembre 2026" in request["messages"][0]["content"]
    assert request["messages"][-1] == {"role": "user", "content": "Salut"}
    assert request["options"] == {"num_ctx": 8192}
    assert request["think"] is False
    assert [tool["function"]["name"] for tool in request["tools"]] == [
        "memoriser",
        "oublier",
        "calculer",
        "date_heure",
        "recherche_web",
        "lire_page_web",
    ]


def test_follow_up_messages_include_the_history(assistant, fake):
    fake.replies += [chunks("Premier."), chunks("Second.")]
    conversation = assistant.store.new()
    list(assistant.chat(conversation, "Un", model="qwen3:8b"))
    list(assistant.chat(conversation, "Deux", model="qwen3:8b"))

    sent = fake.chat_requests[1]["messages"]
    assert [(message["role"], message.get("content")) for message in sent[1:]] == [
        ("user", "Un"),
        ("assistant", "Premier."),
        ("user", "Deux"),
    ]


def test_tool_call_then_answer(assistant, fake):
    fake.replies += [chunks("Je calcule.", tool_calls=[("calculer", {"expression": "12*7"})]), chunks("Ça fait 84.")]
    conversation = assistant.store.new()

    events = list(assistant.chat(conversation, "Combien font 12 fois 7 ?", model="qwen3:8b"))

    assert {"type": "tool_call", "name": "calculer", "label": "Calcul : 12*7"} in events
    assert {"type": "tool_result", "name": "calculer", "summary": "= 84", "error": False} in events
    second = fake.chat_requests[1]["messages"]
    assert second[-2]["role"] == "assistant"
    assert second[-2]["tool_calls"] == [{"function": {"name": "calculer", "arguments": {"expression": "12*7"}}}]
    assert second[-1] == {"role": "tool", "content": "12*7 = 84", "tool_name": "calculer"}

    saved = assistant.store.load(conversation["id"])["messages"]
    assert [message["role"] for message in saved] == ["user", "assistant", "tool", "assistant"]
    bubble = display_messages(saved)[1]
    assert bubble["text"] == "Je calcule.\n\nÇa fait 84."
    assert bubble["tools"] == [{"name": "calculer", "label": "Calcul : 12*7", "summary": "= 84", "error": False}]


def test_memory_tool_feeds_the_next_conversations(assistant, fake):
    fake.replies += [
        chunks(tool_calls=[("memoriser", {"information": "Il s'appelle Léo et adore le basket."})]),
        chunks("Enchanté Léo !"),
        chunks("Tu t'appelles Léo."),
    ]
    list(assistant.chat(assistant.store.new(), "Je m'appelle Léo et j'adore le basket", model="qwen3:8b"))
    assert "- Il s'appelle Léo et adore le basket." in assistant.memory.read()

    list(assistant.chat(assistant.store.new(), "Comment je m'appelle ?", model="qwen3:8b"))
    assert "Il s'appelle Léo et adore le basket." in fake.chat_requests[2]["messages"][0]["content"]


def test_thinking_is_streamed_and_saved(assistant, fake):
    fake.replies.append(chunks("42.", thinking="Voyons voir, la réponse est..."))
    conversation = assistant.store.new()

    events = list(assistant.chat(conversation, "La grande question ?", model="qwen3:8b", thinking=True))

    assert fake.chat_requests[0]["think"] is True
    assert texts(events, "thinking") == "Voyons voir, la réponse est..."
    assert assistant.store.load(conversation["id"])["messages"][-1]["thinking"] == "Voyons voir, la réponse est..."


def test_think_parameter_depends_on_the_model():
    assert Assistant._think_parameter("qwen3:8b", {"completion", "thinking"}, True) is True
    assert Assistant._think_parameter("qwen3:8b", {"completion", "thinking"}, False) is False
    assert Assistant._think_parameter("gpt-oss:20b", {"completion", "thinking"}, True) == "medium"
    assert Assistant._think_parameter("gpt-oss:20b", {"completion", "thinking"}, False) == "low"
    assert Assistant._think_parameter("gemma3:4b", {"completion", "vision"}, True) is None
    assert Assistant._think_parameter("vieux:latest", None, True) is None


def test_vision_model_receives_images_but_no_tools(assistant, fake):
    fake.replies.append(chunks("Un chat roux."))

    list(assistant.chat(assistant.store.new(), "C'est quoi ?", images=[("chat.jpg", "aGVsbG8=")], model="gemma3:4b"))

    request = fake.chat_requests[0]
    assert not request.get("tools")
    assert "think" not in request
    assert request["messages"][-1]["images"] == ["aGVsbG8="]
    assert "Tes outils" not in request["messages"][0]["content"]


def test_text_only_model_ignores_images_and_says_so(assistant, fake):
    fake.replies.append(chunks("Je ne peux pas voir les images."))
    conversation = assistant.store.new()

    events = list(assistant.chat(conversation, "Regarde", images=[("photo.jpg", "aGVsbG8=")], model="qwen3:8b"))

    assert any(event["type"] == "notice" and "images" in event["message"] for event in events)
    last = fake.chat_requests[0]["messages"][-1]
    assert "images" not in last
    assert "1 image(s)" in last["content"]
    assert display_messages(assistant.store.load(conversation["id"])["messages"])[1]["notices"]


def test_documents_are_added_to_the_message(assistant, fake):
    fake.replies.append(chunks("C'est une liste de courses."))
    conversation = assistant.store.new()

    list(assistant.chat(conversation, "Résume", documents=[("courses.txt", "pain\nlait")], model="qwen3:8b"))

    content = fake.chat_requests[0]["messages"][-1]["content"]
    assert content == "Résume\n\n--- Début du fichier « courses.txt » ---\npain\nlait\n--- Fin du fichier « courses.txt » ---"
    user = display_messages(assistant.store.load(conversation["id"])["messages"])[0]
    assert user == {"role": "user", "text": "Résume", "attachments": ["courses.txt"], "images": []}


def test_huge_documents_are_truncated(assistant, fake):
    fake.replies.append(chunks("D'accord."))

    list(assistant.chat(assistant.store.new(), "Lis", documents=[("roman.txt", "a" * 100_000)], model="qwen3:8b"))

    content = fake.chat_requests[0]["messages"][-1]["content"]
    assert len(content) < assistant.attachment_chars + 500
    assert "document tronqué : 100000 caractères" in content


def test_old_ollama_without_tool_support_is_retried_without_tools(assistant, fake):
    fake.capabilities["vieux:latest"] = None
    fake.replies += [
        httpx.Response(400, json={"error": "registry.ollama.ai/library/vieux:latest does not support tools"}),
        chunks("Salut !"),
        chunks("Re !"),
    ]

    events = list(assistant.chat(assistant.store.new(), "Salut", model="vieux:latest"))
    list(assistant.chat(assistant.store.new(), "Re", model="vieux:latest"))

    assert fake.chat_requests[0]["tools"]
    assert "think" not in fake.chat_requests[0]
    assert not fake.chat_requests[1].get("tools")
    assert "Tes outils" not in fake.chat_requests[1]["messages"][0]["content"]
    assert events[-1]["type"] == "done"
    assert not fake.chat_requests[2].get("tools")


def test_ollama_not_running(assistant, fake):
    fake.down = True

    events = list(assistant.chat(assistant.store.new(), "Salut", model="qwen3:8b"))

    assert events[-1]["type"] == "error"
    assert "Impossible de joindre Ollama" in events[-1]["message"]


def test_ollama_stops_during_the_conversation(assistant, fake):
    assistant.capabilities("qwen3:8b")
    fake.down = True

    events = list(assistant.chat(assistant.store.new(), "Salut", model="qwen3:8b"))

    assert events[-1]["type"] == "error"
    assert "Impossible de joindre Ollama" in events[-1]["message"]


def test_missing_model_explains_how_to_install_it(assistant):
    events = list(assistant.chat(assistant.store.new(), "Salut", model="inconnu:7b"))

    assert events[-1]["type"] == "error"
    assert "ollama pull inconnu:7b" in events[-1]["message"]


def test_out_of_memory_error_is_explained(assistant, fake):
    fake.replies.append(httpx.Response(500, json={"error": "model requires more system memory (12.0 GiB) than is available (7.5 GiB)"}))

    events = list(assistant.chat(assistant.store.new(), "Salut", model="qwen3:8b"))

    assert "Pas assez de mémoire" in events[-1]["message"]


def test_old_exchanges_are_dropped_when_the_context_is_full(make_assistant, fake, config):
    config.context_size = 2048
    assistant = make_assistant()
    conversation = assistant.store.new()
    for index in range(6):
        conversation["messages"] += [
            {"role": "user", "content": f"question {index} " + "x" * 1000},
            {"role": "assistant", "content": f"réponse {index} " + "y" * 1000},
        ]
    fake.replies.append(chunks("ok"))

    list(assistant.chat(conversation, "dernière question", model="qwen3:8b"))

    sent = fake.chat_requests[0]["messages"]
    everything = " ".join(message["content"] for message in sent)
    assert sent[0]["role"] == "system"
    assert sent[1]["role"] == "user"
    assert sent[-1]["content"] == "dernière question"
    assert "question 5" in everything
    assert "question 0" not in everything


def test_interrupted_answer_is_kept(assistant, fake):
    fake.replies += [chunks("Il était une fois un dragon très gentil."), chunks("Suite.")]
    conversation = assistant.store.new()

    events = assistant.chat(conversation, "Raconte une histoire", model="qwen3:8b")
    for event in events:
        if event["type"] == "text":
            break
    events.close()

    last = assistant.store.load(conversation["id"])["messages"][-1]
    assert last["role"] == "assistant"
    assert last["content"] == "Il ét"
    assert last["notices"] == ["Réponse interrompue."]
    assert list(assistant.chat(conversation, "Continue", model="qwen3:8b"))[-1]["type"] == "done"


def test_error_in_the_middle_of_an_answer_keeps_what_was_written(assistant, fake):
    lines = chunks("Voici le début")[:-1] + [{"error": "le modèle a planté"}]
    fake.replies.append(ndjson(lines))
    conversation = assistant.store.new()

    events = list(assistant.chat(conversation, "Explique", model="qwen3:8b"))

    assert events[-1] == {"type": "error", "message": "Erreur d'Ollama : le modèle a planté"}
    last = assistant.store.load(conversation["id"])["messages"][-1]
    assert last["content"] == "Voici le début"
    assert last["notices"] == ["Réponse interrompue par une erreur : Erreur d'Ollama : le modèle a planté"]


def test_conversation_deleted_during_an_answer_stays_deleted(assistant, fake):
    fake.replies.append(chunks("Une réponse qui arrive trop tard."))
    conversation = assistant.store.new()
    events = assistant.chat(conversation, "Salut", model="qwen3:8b")
    next(events)

    assistant.store.delete(conversation["id"])
    list(events)

    assert assistant.store.list() == []


def test_only_one_answer_at_a_time_per_conversation(assistant, fake):
    fake.replies += [chunks("Première."), chunks("Seconde.")]
    conversation = assistant.store.new()

    first = assistant.chat(conversation, "Un", model="qwen3:8b")
    next(first)
    second = list(assistant.chat(conversation, "Deux", model="qwen3:8b"))
    list(first)

    assert second == [{"type": "error", "message": "Une réponse est déjà en cours dans cette conversation."}]


def test_tool_rounds_are_limited(assistant, fake):
    fake.replies += [chunks(tool_calls=[("date_heure", {})])] * MAX_TOOL_ROUNDS + [chunks("Il est 14 h 05.")]

    events = list(assistant.chat(assistant.store.new(), "Quelle heure est-il ?", model="qwen3:8b"))

    assert sum(event["type"] == "tool_call" for event in events) == MAX_TOOL_ROUNDS
    assert not fake.chat_requests[-1].get("tools")
    assert events[-1]["type"] == "done"


def test_truncated_or_empty_answers_are_flagged(assistant, fake):
    fake.replies += [chunks("Une réponse coupée", done_reason="length"), chunks("")]

    cut = list(assistant.chat(assistant.store.new(), "Longue réponse", model="qwen3:8b"))
    empty = list(assistant.chat(assistant.store.new(), "Rien", model="qwen3:8b"))

    assert any(event["type"] == "notice" and "Réponse coupée" in event["message"] for event in cut)
    assert any(event["type"] == "notice" and "rien répondu" in event["message"] for event in empty)


def test_models_overview_hides_embedding_models(assistant):
    overview = assistant.models_overview()

    assert overview["ok"] is True
    assert [model["name"] for model in overview["models"]] == ["gemma3:4b", "qwen3:8b"]
    assert overview["models"][1]["capabilities"] == ["completion", "thinking", "tools"]
    assert overview["default"] == "qwen3:8b"


def test_default_model_falls_back_to_an_installed_one(make_assistant, config):
    config.model = "llama3.2"
    assert make_assistant().default_model() == "gemma3:4b"


def test_models_overview_when_ollama_is_down(assistant, fake):
    fake.down = True

    overview = assistant.models_overview()

    assert overview["ok"] is False
    assert "Impossible de joindre Ollama" in overview["error"]


def test_pull_reports_progress(assistant):
    events = list(assistant.pull("qwen3:4b"))

    assert events[0] == {"type": "progress", "status": "pulling manifest", "completed": 0, "total": 0}
    assert {"type": "progress", "status": "pulling 3a2b1c", "completed": 400, "total": 1000} in events
    assert events[-1] == {"type": "done", "model": "qwen3:4b"}


def test_pull_of_an_unknown_model(assistant, fake):
    fake.pull_error = "pull model manifest: file does not exist"

    events = list(assistant.pull("nexistepas"))

    assert events[-1]["type"] == "error"
    assert "n'existe pas" in events[-1]["message"]
