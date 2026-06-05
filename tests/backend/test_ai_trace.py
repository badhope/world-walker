"""Trace 日志:agent 决策过程(llm_call / tool_call / fallback / retry / done)的累积与序列化。"""

import pytest

from backend.ai.trace import Step, TraceStore


def test_step_to_dict_minimal():
    s = Step(round=1, type="llm_call")
    d = s.to_dict()
    assert d["round"] == 1
    assert d["type"] == "llm_call"
    assert d["model_used"] is None
    assert d["duration_ms"] == 0
    assert "metadata" in d


def test_step_to_dict_full():
    s = Step(
        round=2,
        type="tool_call",
        model_used="qwen-max",
        tool_name="get_forecast",
        tool_args={"scope": "city", "name": "shenzhen"},
        tool_result_preview='{"predictions": [...]}',
        duration_ms=150,
        error=None,
        metadata={"parallel_idx": 0},
    )
    d = s.to_dict()
    assert d["tool_name"] == "get_forecast"
    assert d["model_used"] == "qwen-max"
    assert d["duration_ms"] == 150
    assert d["metadata"]["parallel_idx"] == 0


def test_trace_store_append_and_get():
    ts = TraceStore()
    ts.append(Step(round=1, type="llm_call", model_used="qwen-max"))
    ts.append(Step(round=1, type="tool_call", tool_name="get_forecast"))
    all_steps = ts.get_all()
    assert len(all_steps) == 2
    assert all_steps[0]["type"] == "llm_call"
    assert all_steps[1]["type"] == "tool_call"
    assert all_steps[1]["tool_name"] == "get_forecast"


def test_trace_store_max_steps_truncates():
    ts = TraceStore(max_steps=3)
    for i in range(5):
        ts.append(Step(round=i+1, type="llm_call"))
    all_steps = ts.get_all()
    assert len(all_steps) == 3
    # 保留最新 3 步(round 3, 4, 5)
    assert all_steps[0]["round"] == 3
    assert all_steps[2]["round"] == 5


def test_trace_store_clear():
    ts = TraceStore()
    ts.append(Step(round=1, type="llm_call"))
    ts.clear()
    assert len(ts.get_all()) == 0
