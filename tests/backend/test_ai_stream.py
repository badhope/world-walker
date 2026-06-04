"""stream_chat 真流式 — 用 litellm.completion(stream=True) 增量 yield dict。"""
from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any

import litellm
import pytest


def test_stream_chat_yields_text_chunks(monkeypatch):
    """LLM 流式 → 每个 yield 是 {type: 'token', content: '...'} 增量。"""
    from backend.ai import llm_client
    from backend.ai.config import AIConfig

    class FakeDelta:
        def __init__(self, content):
            self.content = content

    class FakeChoice:
        def __init__(self, deltas):
            self.delta = deltas

    def fake_completion(*args, **kwargs):
        # 断言 stream=True 被传了
        assert kwargs.get("stream") is True
        return iter([
            type("R", (), {"choices": [FakeChoice(FakeDelta("你"))]})(),
            type("R", (), {"choices": [FakeChoice(FakeDelta("好"))]})(),
            type("R", (), {"choices": [FakeChoice(FakeDelta("。"))]})(),
        ])

    monkeypatch.setattr(llm_client.litellm, "completion", fake_completion)

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])
    chunks = list(llm_client.stream_chat(cfg, messages=[{"role": "user", "content": "hi"}]))
    assert chunks == [
        {"type": "token", "content": "你"},
        {"type": "token", "content": "好"},
        {"type": "token", "content": "。"},
    ]


def test_stream_chat_emits_done_marker(monkeypatch):
    """流式结束 → yield {type: 'done', finish_reason: ...}。"""
    from backend.ai import llm_client
    from backend.ai.config import AIConfig

    class FakeDelta:
        def __init__(self, content):
            self.content = content

    class FakeChoice:
        def __init__(self, deltas, finish_reason="stop"):
            self.delta = deltas
            self.finish_reason = finish_reason

    def fake_completion(*args, **kwargs):
        return iter([
            type("R", (), {"choices": [FakeChoice(FakeDelta("答"))]})(),
            type("R", (), {"choices": [FakeChoice(FakeDelta("案"), finish_reason="stop")]})(),
        ])

    monkeypatch.setattr(llm_client.litellm, "completion", fake_completion)

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])
    chunks = list(llm_client.stream_chat(cfg, messages=[{"role": "user", "content": "x"}]))
    assert chunks[-1]["type"] == "done"
    assert chunks[-1]["finish_reason"] == "stop"


def test_stream_chat_handles_exception(monkeypatch):
    """litellm 抛异常 → 包装 LLMError(不冒泡给上层 SSE 消费者)。"""
    from backend.ai import llm_client
    from backend.ai.config import AIConfig

    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(llm_client.litellm, "completion", boom)

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])
    chunks = list(llm_client.stream_chat(cfg, messages=[{"role": "user", "content": "x"}]))
    assert len(chunks) == 1
    assert chunks[0]["type"] == "error"
    assert "network down" in chunks[0]["message"]


def test_stream_chat_skips_empty_deltas(monkeypatch):
    """LLM 偶尔 yield content=None 的 delta(角色标记/空段)→ 跳过,不 yield 空 token。"""
    from backend.ai import llm_client
    from backend.ai.config import AIConfig

    class FakeDelta:
        def __init__(self, content):
            self.content = content

    class FakeChoice:
        def __init__(self, deltas, finish_reason="stop"):
            self.delta = deltas
            self.finish_reason = finish_reason

    def fake_completion(*args, **kwargs):
        return iter([
            type("R", (), {"choices": [FakeChoice(FakeDelta(None))]})(),  # role chunk
            type("R", (), {"choices": [FakeChoice(FakeDelta("实"))]})(),
            type("R", (), {"choices": [FakeChoice(FakeDelta("装"))]})(),
            type("R", (), {"choices": [FakeChoice(FakeDelta(""), finish_reason="stop")]})(),
        ])

    monkeypatch.setattr(llm_client.litellm, "completion", fake_completion)

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])
    chunks = list(llm_client.stream_chat(cfg, messages=[{"role": "user", "content": "x"}]))
    tokens = [c for c in chunks if c["type"] == "token"]
    assert tokens == [
        {"type": "token", "content": "实"},
        {"type": "token", "content": "装"},
    ]
