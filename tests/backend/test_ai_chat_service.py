import pytest


def test_chat_single_turn_no_tool(monkeypatch):
    """LLM 不调 tool → 直接返回 content"""
    from backend.ai import chat_service
    from backend.ai.config import AIConfig
    from backend.ai.llm_client import LLMResponse

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])

    def fake_chat(*args, **kwargs):
        return LLMResponse(content="Hello back", tool_calls=[])

    monkeypatch.setattr(chat_service.llm_client, "chat", fake_chat)
    monkeypatch.setattr(chat_service, "execute_tool", lambda n, a: {})

    result = chat_service.chat(cfg, session_id="test1", user_message="hi")
    assert result["content"] == "Hello back"
    assert result["tool_rounds"] == 0


def test_chat_with_one_tool_round(monkeypatch):
    """LLM 调 tool → execute_tool → 再调 LLM → 返回最终"""
    from backend.ai import chat_service
    from backend.ai.config import AIConfig
    from backend.ai.llm_client import LLMResponse, ToolCall

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])

    call_count = {"n": 0}

    def fake_chat(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return LLMResponse(
                content=None,
                tool_calls=[ToolCall(id="c1", name="get_forecast", arguments={"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})],
            )
        return LLMResponse(content="深圳 GDP 2026 预测 40,100 亿元。", tool_calls=[])

    monkeypatch.setattr(chat_service.llm_client, "chat", fake_chat)
    monkeypatch.setattr(chat_service, "execute_tool", lambda n, a: {"ensemble": {"predictions": [40100, 41700, 43200]}})

    result = chat_service.chat(cfg, session_id="test2", user_message="深圳 GDP 2026 多少?")
    assert "40,100" in result["content"]
    assert result["tool_rounds"] == 1
    assert call_count["n"] == 2


def test_chat_max_tool_rounds_exceeded(monkeypatch):
    """LLM 一直调 tool → 超过 max_tool_rounds → 强制结束"""
    from backend.ai import chat_service
    from backend.ai.config import AIConfig
    from backend.ai.llm_client import LLMResponse, ToolCall

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])

    def fake_chat(*args, **kwargs):
        return LLMResponse(
            content=None,
            tool_calls=[ToolCall(id="c1", name="get_forecast", arguments={"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})],
        )

    monkeypatch.setattr(chat_service.llm_client, "chat", fake_chat)
    monkeypatch.setattr(chat_service, "execute_tool", lambda n, a: {"x": 1})

    result = chat_service.chat(cfg, session_id="test3", user_message="loop")
    assert result["tool_rounds"] == 5
    assert "复杂" in result["content"] or "太多" in result["content"]


def test_chat_llm_error_returns_error(monkeypatch):
    from backend.ai import chat_service
    from backend.ai.config import AIConfig
    from backend.ai.llm_client import LLMError

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])

    def boom(*a, **k):
        raise LLMError("API key invalid")

    monkeypatch.setattr(chat_service.llm_client, "chat", boom)

    result = chat_service.chat(cfg, session_id="test4", user_message="x")
    assert "error" in result
    assert "API key" in result["error"] or "config" in result["content"].lower() or "不可用" in result["content"]
