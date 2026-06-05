"""admin routes 测试 — 9 tool dispatch + 8 endpoint 全覆盖。"""
from __future__ import annotations

import os
import time

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("LLM_OPENAI_API_KEY", "sk-test-fake-key-for-admin")
os.environ.setdefault("LLM_DEFAULT_BACKEND", "openai")

from backend.api.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_history_between_tests():
    """每个 test 之前清空 history,避免测试顺序耦合。"""
    client.delete("/api/v1/admin/history")
    yield
    client.delete("/api/v1/admin/history")

# --------------------------------------------------------------------------- #
# 9 tool dispatch — happy path(全 mock rca,不调真后端)
# --------------------------------------------------------------------------- #


def _patch_rca(monkeypatch, return_value):
    """patch rca.<func> 直接返固定 dict。"""
    from rca import tools as rca_tools

    def make_fake(_name):
        def fake(*args, **kwargs):
            return return_value
        return fake

    for fn in (
        "forecast", "diagnostics", "backtest", "risk", "scenarios",
        "monte_carlo", "data_provenance", "macro_data", "list_cities",
    ):
        monkeypatch.setattr(rca_tools, fn, make_fake(fn))


def test_tools_list_endpoint():
    """GET /api/v1/admin/tools → 9 tool metadata。"""
    r = client.get("/api/v1/admin/tools")
    assert r.status_code == 200
    data = r.json()
    assert "tools" in data
    assert len(data["tools"]) == 9
    names = {t["name"] for t in data["tools"]}
    assert "get_forecast" in names
    assert "get_list_cities" in names


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("get_forecast", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3}),
        ("get_diagnostics", {"scope": "city", "name": "shanghai", "indicator": "gdp"}),
        ("get_backtest", {"scope": "city", "name": "shenzhen", "indicator": "gdp"}),
        ("get_risk", {"scope": "city", "name": "guangzhou", "indicator": "gdp"}),
        ("get_scenarios", {"scope": "city", "name": "shenzhen", "indicator": "gdp"}),
        ("get_monte_carlo", {"scope": "city", "name": "hangzhou", "indicator": "gdp", "years": 3}),
        ("get_data_provenance", {"name": "shenzhen"}),
        ("get_macro_data", {}),
        ("get_list_cities", {}),
    ],
)
def test_9_tool_run_happy_path(monkeypatch, endpoint, payload):
    """POST /admin/tools/{name}/run → 调 rca.<func> 返 200。"""
    _patch_rca(monkeypatch, return_value={"data": {"fake": "ok"}})
    r = client.post(f"/api/v1/admin/tools/{endpoint}/run", json=payload)
    assert r.status_code == 200, f"{endpoint}: {r.text}"
    body = r.json()
    assert body["data"] == {"fake": "ok"}
    assert body["tool"] == endpoint
    assert body["duration_ms"] >= 0
    assert "id" in body


def test_tool_run_records_to_history(monkeypatch):
    """tool run 一次后,history 多一条记录。"""
    _patch_rca(monkeypatch, return_value={"data": {"x": 1}})
    client.delete("/api/v1/admin/history")  # 清空
    r = client.post("/api/v1/admin/tools/get_forecast/run", json={"scope": "city", "name": "shenzhen", "indicator": "gdp"})
    assert r.status_code == 200
    h = client.get("/api/v1/admin/history").json()
    assert len(h["items"]) == 1
    assert h["items"][0]["tool"] == "get_forecast"
    assert h["items"][0]["status"] == "ok"


def test_tool_run_unknown_tool_returns_404():
    r = client.post("/api/v1/admin/tools/nonexistent/run", json={})
    assert r.status_code == 404


def test_tool_run_validation_error_returns_400(monkeypatch):
    """tool 内部参数错(城市名不存在)→ rca 抛 ToolArgumentError → route 返 400。"""
    from rca import tools as rca_tools
    from rca.errors import ToolArgumentError

    def boom(*a, **kw):
        raise ToolArgumentError("Unknown city: atlantis")
    monkeypatch.setattr(rca_tools, "forecast", boom)
    r = client.post(
        "/api/v1/admin/tools/get_forecast/run",
        json={"scope": "city", "name": "atlantis", "indicator": "gdp"},
    )
    assert r.status_code == 400
    assert "atlantis" in r.json()["detail"]


# --------------------------------------------------------------------------- #
# config endpoint
# --------------------------------------------------------------------------- #


def test_config_get_returns_aiconfig():
    r = client.get("/api/v1/admin/config")
    assert r.status_code == 200
    data = r.json()
    assert "model" in data
    assert "fallback_chain" in data


def test_config_put_updates_model():
    from backend.api.admin_store import get_config_store

    original = get_config_store().get().model
    try:
        r = client.put("/api/v1/admin/config", json={"model": "deepseek-v3"})
        assert r.status_code == 200
        assert r.json()["model"] == "deepseek-v3"
        # 立刻 get 也返新值
        r2 = client.get("/api/v1/admin/config")
        assert r2.json()["model"] == "deepseek-v3"
    finally:
        get_config_store().update(model=original)


def test_config_put_sets_base_url_env(monkeypatch):
    monkeypatch.delenv("LLM_OPENAI_BASE_URL", raising=False)
    r = client.put("/api/v1/admin/config", json={"base_url": "https://my-gw.example.com/v1"})
    assert r.status_code == 200
    assert os.environ.get("LLM_OPENAI_BASE_URL") == "https://my-gw.example.com/v1"


def test_config_put_rejects_invalid_temperature():
    r = client.put("/api/v1/admin/config", json={"temperature": 5.0})  # > 2
    assert r.status_code == 422


# --------------------------------------------------------------------------- #
# history endpoint
# --------------------------------------------------------------------------- #


def test_history_list_and_filter(monkeypatch):
    _patch_rca(monkeypatch, return_value={"data": {}})
    client.delete("/api/v1/admin/history")
    client.post("/api/v1/admin/tools/get_forecast/run", json={"scope": "city", "name": "x", "indicator": "y"})
    client.post("/api/v1/admin/tools/get_diagnostics/run", json={"scope": "city", "name": "x", "indicator": "y"})
    client.post("/api/v1/admin/tools/get_forecast/run", json={"scope": "city", "name": "x", "indicator": "y"})

    r = client.get("/api/v1/admin/history")
    assert r.status_code == 200
    assert len(r.json()["items"]) == 3

    r2 = client.get("/api/v1/admin/history?tool=get_forecast")
    assert len(r2.json()["items"]) == 2

    r3 = client.get("/api/v1/admin/history?limit=1")
    assert len(r3.json()["items"]) == 1


def test_history_delete_clears_all(monkeypatch):
    _patch_rca(monkeypatch, return_value={"data": {}})
    client.post("/api/v1/admin/tools/get_forecast/run", json={"scope": "city", "name": "x", "indicator": "y"})
    assert len(client.get("/api/v1/admin/history").json()["items"]) == 1
    r = client.delete("/api/v1/admin/history")
    assert r.status_code == 200
    assert client.get("/api/v1/admin/history").json()["items"] == []


def test_history_get_by_id(monkeypatch):
    _patch_rca(monkeypatch, return_value={"data": {}})
    client.delete("/api/v1/admin/history")
    client.post("/api/v1/admin/tools/get_forecast/run", json={"scope": "city", "name": "x", "indicator": "y"})
    items = client.get("/api/v1/admin/history").json()["items"]
    rid = items[0]["id"]
    r = client.get(f"/api/v1/admin/history/{rid}")
    assert r.status_code == 200
    assert r.json()["id"] == rid


# --------------------------------------------------------------------------- #
# chat endpoint
# --------------------------------------------------------------------------- #


def test_chat_non_stream(monkeypatch):
    """POST /admin/chat → 调 rca.chat,返 content + tool_rounds。"""
    def fake_chat(session_id, user_message, **kw):
        return {"content": "深圳 2025 GDP 44202.90 亿元", "tool_rounds": 1}
    monkeypatch.setattr("backend.api.routes.admin._rca_chat", fake_chat)
    r = client.post("/api/v1/admin/chat", json={"session_id": "s1", "message": "深圳 GDP 2025?"})
    assert r.status_code == 200
    data = r.json()
    assert "44202" in data["content"]
    assert data["tool_rounds"] == 1


def test_chat_non_stream_llm_unavailable(monkeypatch):
    from rca.errors import LLMUnavailableError

    def boom(*a, **kw):
        raise LLMUnavailableError("all models down")
    monkeypatch.setattr("backend.api.routes.admin._rca_chat", boom)
    r = client.post("/api/v1/admin/chat", json={"session_id": "s1", "message": "x"})
    assert r.status_code == 502
    assert "all models down" in r.json()["detail"]


def test_chat_stream_sse(monkeypatch):
    """GET /admin/chat/stream → SSE 流式。"""
    def fake_stream(session_id, user_message, **kw):
        yield {"type": "thinking"}
        yield {"type": "token", "content": "你好"}
        yield {"type": "token", "content": ", "}
        yield {"type": "done", "tool_rounds": 1}
    monkeypatch.setattr("backend.api.routes.admin._rca_chat_stream", fake_stream)

    with client.stream("GET", "/api/v1/admin/chat/stream?session_id=s1&message=hi") as r:
        assert r.status_code == 200
        chunks = list(r.iter_text())
    # 4 个 event,每个 SSE 一行
    assert any("thinking" in c for c in chunks)
    assert any("token" in c and "你好" in c for c in chunks)
    assert any("done" in c for c in chunks)


def test_chat_stream_error_event(monkeypatch):
    """LLM 错时 SSE 里 yield error event。"""
    def fake_stream(session_id, user_message, **kw):
        yield {"type": "thinking"}
        yield {"type": "error", "message": "model dead", "trace": []}
    monkeypatch.setattr("backend.api.routes.admin._rca_chat_stream", fake_stream)

    with client.stream("GET", "/api/v1/admin/chat/stream?session_id=s1&message=hi") as r:
        chunks = list(r.iter_text())
    assert any("error" in c and "model dead" in c for c in chunks)
