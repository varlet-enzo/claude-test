"""Un faux Ollama pour tester l'IA sans télécharger de modèle."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx
import ollama
import pytest

from mon_ia.assistant import Assistant
from mon_ia.config import Config


def chunks(
    text: str = "",
    *,
    thinking: str = "",
    tool_calls: list[tuple[str, dict[str, Any]]] | None = None,
    done_reason: str = "stop",
) -> list[dict[str, Any]]:
    """Une réponse de /api/chat découpée en morceaux, comme le fait Ollama en streaming."""
    base = {"model": "fake", "created_at": "2026-09-23T12:00:00Z", "done": False}
    lines = [{**base, "message": {"role": "assistant", "content": "", "thinking": thinking[i : i + 5]}} for i in range(0, len(thinking), 5)]
    lines += [{**base, "message": {"role": "assistant", "content": text[i : i + 5]}} for i in range(0, len(text), 5)]
    if tool_calls:
        calls = [
            {"id": f"call_{index}", "function": {"index": index, "name": name, "arguments": arguments}}
            for index, (name, arguments) in enumerate(tool_calls)
        ]
        lines.append({**base, "message": {"role": "assistant", "content": "", "tool_calls": calls}})
    lines.append(
        {
            **base,
            "message": {"role": "assistant", "content": ""},
            "done": True,
            "done_reason": done_reason,
            "total_duration": 2_000_000_000,
            "prompt_eval_count": 50,
            "eval_count": 20,
            "eval_duration": 1_000_000_000,
        }
    )
    return lines


def ndjson(lines: list[dict[str, Any]]) -> httpx.Response:
    return httpx.Response(200, content="".join(json.dumps(line) + "\n" for line in lines).encode())


class FakeOllama:
    def __init__(self) -> None:
        # None = Ollama trop ancien pour annoncer les capacités du modèle.
        self.capabilities: dict[str, list[str] | None] = {
            "qwen3:8b": ["completion", "tools", "thinking"],
            "gemma3:4b": ["completion", "vision"],
            "nomic-embed-text:latest": ["embedding"],
        }
        self.replies: list[Any] = []
        self.chat_requests: list[dict[str, Any]] = []
        self.pull_error: str | None = None
        self.down = False

    def handler(self, request: httpx.Request) -> httpx.Response:
        if self.down:
            raise httpx.ConnectError("Connexion refusée", request=request)
        body = json.loads(request.content) if request.content else {}
        path = request.url.path
        if path == "/api/tags":
            models = [
                {
                    "name": name,
                    "model": name,
                    "modified_at": "2026-09-01T10:00:00Z",
                    "size": 5_200_000_000,
                    "digest": "abc123",
                    "details": {"format": "gguf", "family": name.split(":")[0], "parameter_size": "8.2B", "quantization_level": "Q4_K_M"},
                }
                for name in self.capabilities
            ]
            return httpx.Response(200, json={"models": models})
        if path == "/api/show":
            name = body.get("model")
            if name not in self.capabilities:
                return httpx.Response(404, json={"error": f"model '{name}' not found"})
            data: dict[str, Any] = {"modelfile": "", "parameters": "", "template": "", "details": {}, "model_info": {}}
            if self.capabilities[name] is not None:
                data["capabilities"] = self.capabilities[name]
            return httpx.Response(200, json=data)
        if path == "/api/chat":
            self.chat_requests.append(body)
            reply = self.replies.pop(0)
            if callable(reply):
                reply = reply(body)
            return reply if isinstance(reply, httpx.Response) else ndjson(reply)
        if path == "/api/pull":
            if self.pull_error:
                return ndjson([{"status": "pulling manifest"}, {"error": self.pull_error}])
            return ndjson(
                [
                    {"status": "pulling manifest"},
                    {"status": "pulling 3a2b1c", "digest": "sha256:3a2b1c", "total": 1000, "completed": 400},
                    {"status": "pulling 3a2b1c", "digest": "sha256:3a2b1c", "total": 1000, "completed": 1000},
                    {"status": "verifying sha256 digest"},
                    {"status": "writing manifest"},
                    {"status": "success"},
                ]
            )
        return httpx.Response(404, json={"error": "not found"})


def no_network(*args: Any) -> Any:
    raise AssertionError("Les tests ne doivent pas accéder à internet.")


@pytest.fixture
def fake() -> FakeOllama:
    return FakeOllama()


@pytest.fixture
def config(tmp_path) -> Config:
    return Config(data_dir=tmp_path / "data")


@pytest.fixture
def make_assistant(fake, config):
    def factory(**kwargs: Any) -> Assistant:
        client = ollama.Client(host="http://ollama.test", transport=httpx.MockTransport(fake.handler))
        kwargs.setdefault("search", no_network)
        kwargs.setdefault("fetch", no_network)
        return Assistant(config, client=client, clock=lambda: datetime(2026, 9, 23, 14, 5), **kwargs)

    return factory


@pytest.fixture
def assistant(make_assistant) -> Assistant:
    return make_assistant()
