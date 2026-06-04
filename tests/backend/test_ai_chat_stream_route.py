"""/chat/stream 路由用 chat_stream_with_trace,事件透传到 SSE; /chat 响应含 tool_calls。"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_chat_stream_route_yields_tool_call_event(monkeypatch):
    from backend.api.main import app
    from backend.ai import chat_service, llm_client

    def _fake_stream_with_trace(cfg, session_id, user_message):
        yield {"type": "thinking"}
        yield {
            "type": "tool_call",
            "name": "get_forecast",
            "args": {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3},
            "navigate_to": "/investment_grade.html?scope=city&name=shenzhen&indicator=gdp&years=3",
        }
        yield {"type": "token", "content": "深圳 2026 GDP 4 万亿。"}
        yield {"type": "done", "finish_reason": "stop", "tool_rounds": 1, "tool_calls": []}

    monkeypatch.setattr(chat_service, "chat_stream_with_trace", _fake_stream_with_trace)
    monkeypatch.setattr(llm_client, "stream_chat", lambda *a, **k: iter([]))
    from backend.api.routes import ai as ai_routes
    monkeypatch.setattr(ai_routes, "load_config", lambda: type("C", (), {"max_tool_rounds": 5})())

    client = TestClient(app)
    with client.stream(
        "POST",
        "/api/v1/ai/chat/stream",
        json={"session_id": "s1", "messages": [{"role": "user", "content": "深圳 GDP 2026 多少?"}]},
    ) as r:
        assert r.status_code == 200
        body = "".join(chunk for chunk in r.iter_text())

    # 验证 body 含 tool_call SSE event
    assert '"type": "tool_call"' in body
    assert "navigate_to" in body
    assert "/investment_grade.html" in body


def test_chat_route_response_includes_tool_calls(monkeypatch):
    """/chat 一次性响应含 tool_calls 字段(老 client 也拿得到导航 URL)。"""
    from backend.api.main import app
    from backend.ai import chat_service

    def _fake_chat(cfg, session_id, user_message):
        return {
            "content": "深圳 2026 GDP 4 万亿。",
            "tool_rounds": 1,
            "tool_calls": [{
                "name": "get_forecast",
                "args": {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3},
                "navigate_to": "/investment_grade.html?scope=city&name=shenzhen&indicator=gdp&years=3",
            }],
        }

    monkeypatch.setattr(chat_service, "chat", _fake_chat)
    from backend.api.routes import ai as ai_routes
    monkeypatch.setattr(ai_routes, "load_config", lambda: type("C", (), {"max_tool_rounds": 5})())

    client = TestClient(app)
    r = client.post(
        "/api/v1/ai/chat",
        json={"session_id": "s1", "messages": [{"role": "user", "content": "深圳 GDP 2026 多少?"}]},
    )
    assert r.status_code == 200
    body = r.json()
    assert "tool_calls" in body
    assert body["tool_calls"][0]["name"] == "get_forecast"
    assert "navigate_to" in body["tool_calls"][0]
