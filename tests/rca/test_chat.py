"""rca.chat / rca.chat_stream 包装 — 调 backend.ai.chat_service,错误包装为 LLMUnavailableError。"""
import importlib

import pytest
from unittest.mock import MagicMock, patch

from rca import chat  # chat 函数(从 rca/__init__.py 重导出)
from rca.errors import LLMUnavailableError
from backend.ai.fallback import FallbackError

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
