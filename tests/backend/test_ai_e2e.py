import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-fake-for-test")


def test_ai_tools_list():
    from backend.api.main import app
    client = TestClient(app)
    r = client.get("/api/v1/ai/tools")
    assert r.status_code == 200
    data = r.json()
    assert len(data["tools"]) == 9
    assert "get_forecast" in [t["function"]["name"] for t in data["tools"]]


def test_ai_config():
    from backend.api.main import app
    client = TestClient(app)
    r = client.get("/api/v1/ai/config")
    assert r.status_code == 200
    data = r.json()
    assert "active_backend" in data
    assert "model" in data


def test_ai_chat_non_stream(monkeypatch):
    from backend.api.main import app
    from backend.api.routes import ai as ai_route

    def fake_chat(cfg, session_id, user_message):
        return {"content": "Test answer", "tool_rounds": 0}

    monkeypatch.setattr(ai_route.chat_service, "chat", fake_chat)

    client = TestClient(app)
    r = client.post("/api/v1/ai/chat", json={
        "session_id": "test-session-1",
        "messages": [{"role": "user", "content": "hi"}],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["content"] == "Test answer"


def test_ai_chat_empty_message():
    from backend.api.main import app
    client = TestClient(app)
    r = client.post("/api/v1/ai/chat", json={
        "session_id": "test",
        "messages": [],
    })
    # 应 400(空 messages)
    assert r.status_code in {400, 422}


def test_ai_chat_message_too_long():
    from backend.api.main import app
    client = TestClient(app)
    r = client.post("/api/v1/ai/chat", json={
        "session_id": "test",
        "messages": [{"role": "user", "content": "x" * 5000}],
    })
    assert r.status_code in {400, 422}
