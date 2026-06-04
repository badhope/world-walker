import pytest


def test_chat_returns_response(monkeypatch):
    """LLM 不调 tool → 返回 content"""
    from backend.ai import llm_client
    from backend.ai.config import AIConfig

    class FakeResponse:
        def __init__(self):
            self.choices = [type("C", (), {"message": type("M", (), {
                "content": "Hello", "tool_calls": None
            })(), "finish_reason": "stop"})()]
            self.usage = type("U", (), {"prompt_tokens": 10, "completion_tokens": 5})()

    def fake_completion(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(llm_client.litellm, "completion", fake_completion)

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])
    resp = llm_client.chat(cfg, messages=[{"role": "user", "content": "hi"}], tools=None)
    assert resp.content == "Hello"
    assert resp.tool_calls == []


def test_chat_returns_tool_calls(monkeypatch):
    """LLM 调 tool → 返回 tool_calls list"""
    from backend.ai import llm_client
    from backend.ai.config import AIConfig

    class FakeToolCall:
        def __init__(self, name, args):
            self.id = "call_1"
            self.function = type("F", (), {"name": name, "arguments": str(args).replace("'", '"')})()

    class FakeResponse:
        def __init__(self):
            self.choices = [type("C", (), {"message": type("M", (), {
                "content": None, "tool_calls": [FakeToolCall("get_forecast", {"scope": "city", "name": "shenzhen"})]
            })(), "finish_reason": "tool_calls"})()]
            self.usage = type("U", (), {"prompt_tokens": 20, "completion_tokens": 10})()

    monkeypatch.setattr(llm_client.litellm, "completion", lambda *a, **k: FakeResponse())

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])
    resp = llm_client.chat(cfg, messages=[{"role": "user", "content": "深圳 GDP"}], tools=[{"type": "function", "function": {"name": "get_forecast"}}])
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "get_forecast"


def test_chat_handles_exception(monkeypatch):
    from backend.ai import llm_client
    from backend.ai.config import AIConfig
    def boom(*a, **k):
        raise RuntimeError("API down")
    monkeypatch.setattr(llm_client.litellm, "completion", boom)
    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])
    with pytest.raises(llm_client.LLMError):
        llm_client.chat(cfg, messages=[{"role": "user", "content": "x"}], tools=None)
