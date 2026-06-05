"""rca.chat / rca.chat_stream 包装 — 调 backend.ai.chat_service,错误包装为 LLMUnavailableError。"""
import importlib
from unittest.mock import MagicMock, patch

import pytest

from backend.ai.fallback import FallbackError
from rca import chat  # chat 函数(从 rca/__init__.py 重导出)
from rca.errors import LLMUnavailableError

# 用 importlib 拿真正的 rca.chat 子模块(rca/__init__.py 把 chat 重导出为函数,遮盖子模块)
_chat_submodule = importlib.import_module("rca.chat")


def test_chat_returns_dict_on_success():
    """chat(session, msg) → backend chat_service.chat() 的 result。"""
    with patch.object(_chat_submodule, "_chat_service") as m_cs:
        m_cs.chat = MagicMock(return_value={"content": "深圳 GDP...", "tool_rounds": 1})
        result = chat(session_id="u1", user_message="深圳 GDP 多少?")
    assert result == {"content": "深圳 GDP...", "tool_rounds": 1}


def test_chat_wraps_fallback_error():
    """FallbackError → LLMUnavailableError(LLM 链全失败语义)。"""
    with patch.object(_chat_submodule, "_chat_service") as m_cs:
        m_cs.chat = MagicMock(side_effect=FallbackError("qwen-max: timeout\ndeepseek-v3: timeout"))
        with pytest.raises(LLMUnavailableError) as exc:
            chat(session_id="u1", user_message="x")
    assert "qwen-max" in str(exc.value)


def test_chat_stream_yields_events():
    """chat_stream() 透传 backend chat_service.chat_stream_with_trace 事件。"""
    with patch.object(_chat_submodule, "_chat_service") as m_cs:
        m_cs.chat_stream_with_trace = MagicMock(return_value=iter([
            {"type": "thinking"},
            {"type": "tool_call", "name": "get_forecast", "args": {"city": "shenzhen"}},
            {"type": "token", "content": "深圳 GDP"},
            {"type": "done", "finish_reason": "stop"},
        ]))
        from rca import chat_stream
        events = list(chat_stream(session_id="u1", user_message="x"))
    assert len(events) == 4
    assert events[0]["type"] == "thinking"
    assert events[1]["name"] == "get_forecast"
    assert events[2]["content"] == "深圳 GDP"
    assert events[3]["type"] == "done"


def test_chat_stream_yields_error_event_on_fallback_error():
    """chat_stream() 内部 LLM 错时,yield error event(不让 generator 半路抛)。"""
    with patch.object(_chat_submodule, "_chat_service") as m_cs:
        m_cs.chat_stream_with_trace = MagicMock(side_effect=FallbackError("all failed"))
        from rca import chat_stream
        events = list(chat_stream(session_id="u1", user_message="x"))
    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "all failed" in events[0]["message"]


# --------------------------------------------------------------------------- #
# config= 覆盖(支持 CLI --model / 用户自定义 AIConfig)
# --------------------------------------------------------------------------- #


def test_chat_accepts_config_override():
    """chat(..., config=cfg) → 用 cfg 而不是 _get_cfg()(后者会从 env 读)。"""
    custom_cfg = _build_custom_cfg(model="custom-model-xyz")
    with patch.object(_chat_submodule, "_chat_service") as m_cs:
        m_cs.chat = MagicMock(return_value={"content": "ok", "tool_rounds": 0})
        chat(session_id="u1", user_message="x", config=custom_cfg)
    # 验证传过去的是 custom_cfg
    call_args = m_cs.chat.call_args
    assert call_args[0][0] is custom_cfg


def test_chat_stream_accepts_config_override():
    """chat_stream(..., config=cfg) → 用 cfg 而不是 _get_cfg()。"""
    custom_cfg = _build_custom_cfg(model="custom-model-xyz")
    with patch.object(_chat_submodule, "_chat_service") as m_cs:
        m_cs.chat_stream_with_trace = MagicMock(return_value=iter([{"type": "done"}]))
        from rca import chat_stream
        events = list(chat_stream(session_id="u1", user_message="x", config=custom_cfg))
    call_args = m_cs.chat_stream_with_trace.call_args
    assert call_args[0][0] is custom_cfg
    assert events[0]["type"] == "done"


def test_chat_base_url_sets_environ(monkeypatch):
    """chat(..., base_url='...') → os.environ['LLM_OPENAI_BASE_URL'] 被设(后端读 env)。"""
    monkeypatch.delenv("LLM_OPENAI_BASE_URL", raising=False)
    with patch.object(_chat_submodule, "_chat_service") as m_cs:
        m_cs.chat = MagicMock(return_value={"content": "ok", "tool_rounds": 0})
        chat(
            session_id="u1", user_message="x",
            config=_build_custom_cfg(),
            base_url="https://my-gw.example.com/v1",
        )
    import os
    assert os.environ["LLM_OPENAI_BASE_URL"] == "https://my-gw.example.com/v1"


def test_chat_no_override_uses_cached_cfg(monkeypatch):
    """chat(不传 config) → 走 _get_cfg() 懒加载路径。"""
    import os

    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-test-fake-key")
    with patch.object(_chat_submodule, "_chat_service") as m_cs:
        m_cs.chat = MagicMock(return_value={"content": "ok", "tool_rounds": 0})
        chat(session_id="u1", user_message="x")
    # 第一个 positional arg 应该是从 _get_cfg() 拿的 AIConfig
    call_args = m_cs.chat.call_args
    from backend.ai.config import AIConfig

    assert isinstance(call_args[0][0], AIConfig)


def _build_custom_cfg(model: str = "test-model"):
    """构造测试用 AIConfig(不需要真 LLM key,只测传参)。"""
    from backend.ai.config import AIConfig

    return AIConfig(
        default_backend="openai", active_backend="openai", model=model,
        temperature=0.3, max_tokens=2000, max_tool_rounds=5, timeout_sec=60,
        available_backends=["openai"],
    )
