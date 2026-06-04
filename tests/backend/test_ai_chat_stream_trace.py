"""chat_service.chat_stream_with_trace — yield {type: thinking, tool_call, token, done} 序列。"""
from __future__ import annotations

import json
from typing import Any

import pytest


class _FakeToolCall:
    def __init__(self, id_, name, arguments):
        self.id = id_
        self.name = name
        self.arguments = arguments


class _FakeResponse:
    def __init__(self, content="", tool_calls=None, finish_reason="stop"):
        self.content = content
        self.tool_calls = tool_calls or []
        self.finish_reason = finish_reason
        self.prompt_tokens = 100
        self.completion_tokens = 20


class _FakeLLM:
    """模拟 LLM:第一次调 → tool_call, 第二次调 → final 文本。"""

    def __init__(self):
        self.call_count = 0

    def chat(self, cfg, messages, tools=None):
        self.call_count += 1
        if self.call_count == 1:
            return _FakeResponse(
                content="",
                tool_calls=[_FakeToolCall("tc-1", "get_forecast",
                                          {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})],
            )
        return _FakeResponse(content="深圳 GDP 2026 预测为 4 万亿。")


def test_chat_stream_with_trace_yields_thinking_first(monkeypatch):
    from backend.ai import chat_service
    fake = _FakeLLM()
    monkeypatch.setattr(chat_service.llm_client, "chat", fake.chat)
    monkeypatch.setattr("backend.ai.conversation.get_history", lambda sid: [])
    monkeypatch.setattr("backend.ai.conversation.append_message", lambda sid, m: None)

    gen = chat_service.chat_stream_with_trace(
        cfg=None, session_id="t1", user_message="深圳 GDP 2026 多少?"
    )
    events = list(gen)
    assert events[0]["type"] == "thinking"
    assert all(e["type"] != "thinking" or i == 0 for i, e in enumerate(events))


def test_chat_stream_with_trace_yields_tool_call_after_thinking(monkeypatch):
    from backend.ai import chat_service
    fake = _FakeLLM()
    monkeypatch.setattr(chat_service.llm_client, "chat", fake.chat)
    monkeypatch.setattr("backend.ai.conversation.get_history", lambda sid: [])
    monkeypatch.setattr("backend.ai.conversation.append_message", lambda sid, m: None)

    events = list(chat_service.chat_stream_with_trace(
        cfg=None, session_id="t2", user_message="深圳 GDP 2026 多少?"
    ))
    tool_events = [e for e in events if e["type"] == "tool_call"]
    assert len(tool_events) == 1
    e = tool_events[0]
    assert e["name"] == "get_forecast"
    assert e["args"] == {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3}
    assert "navigate_to" in e
    assert e["navigate_to"].startswith("/investment_grade.html")


def test_chat_stream_with_trace_yields_done_at_end(monkeypatch):
    from backend.ai import chat_service
    fake = _FakeLLM()
    monkeypatch.setattr(chat_service.llm_client, "chat", fake.chat)
    monkeypatch.setattr("backend.ai.conversation.get_history", lambda sid: [])
    monkeypatch.setattr("backend.ai.conversation.append_message", lambda sid, m: None)

    events = list(chat_service.chat_stream_with_trace(
        cfg=None, session_id="t3", user_message="x"
    ))
    assert events[-1]["type"] == "done"
    assert events[-1]["tool_rounds"] == 1


def test_chat_stream_with_trace_handles_no_tool_call(monkeypatch):
    """LLM 直接答(不调 tool)— 应只有 thinking + done。"""
    from backend.ai import chat_service

    class _NoToolLLM:
        def chat(self, cfg, messages, tools=None):
            return _FakeResponse(content="直接回答")

    monkeypatch.setattr(chat_service.llm_client, "chat", _NoToolLLM().chat)
    monkeypatch.setattr("backend.ai.conversation.get_history", lambda sid: [])
    monkeypatch.setattr("backend.ai.conversation.append_message", lambda sid, m: None)

    events = list(chat_service.chat_stream_with_trace(
        cfg=None, session_id="t4", user_message="hi"
    ))
    types = [e["type"] for e in events]
    assert "tool_call" not in types
    assert "done" in types
    assert events[-1]["tool_rounds"] == 0


def test_chat_stream_with_trace_yields_token_with_content(monkeypatch):
    """done 之前的 token event 必须含 final content。"""
    from backend.ai import chat_service
    fake = _FakeLLM()
    monkeypatch.setattr(chat_service.llm_client, "chat", fake.chat)
    monkeypatch.setattr("backend.ai.conversation.get_history", lambda sid: [])
    monkeypatch.setattr("backend.ai.conversation.append_message", lambda sid, m: None)

    events = list(chat_service.chat_stream_with_trace(
        cfg=None, session_id="t5", user_message="x"
    ))
    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) >= 1
    full_text = "".join(e["content"] for e in token_events)
    assert "深圳 GDP 2026" in full_text
