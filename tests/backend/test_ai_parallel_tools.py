"""并行 tool 执行:多个 tool_call 一次返回时,并行执行,顺序保持。"""

import time
from unittest.mock import patch

import pytest

from backend.ai.llm_client import ToolCall
from backend.ai.parallel_tools import execute_tools_parallel


def _tc(name: str, args: dict, tc_id: str = "1") -> ToolCall:
    return ToolCall(id=tc_id, name=name, arguments=args)


def test_parallel_execution_3_tools():
    """3 个 tool 并行执行(总时间 ≈ 单个 tool 时间,不是 3 倍)。"""
    def fake_execute(name, args):
        time.sleep(0.1)  # 模拟 IO
        return {"data": {"name": name, "args": args}, "navigate_to": f"/x/{name}"}

    with patch("backend.ai.parallel_tools.execute_tool", side_effect=fake_execute) as m:
        tcs = [_tc(f"tool_{i}", {"i": i}, tc_id=str(i)) for i in range(3)]
        t0 = time.perf_counter()
        results = execute_tools_parallel(tcs, max_workers=3)
        elapsed = time.perf_counter() - t0
    # 顺序保持
    assert len(results) == 3
    assert results[0]["data"]["name"] == "tool_0"
    assert results[2]["data"]["name"] == "tool_2"
    # 并行(单 tool 0.1s,3 个并行应 < 0.25s,串行会 ~0.3s)
    assert elapsed < 0.25, f"应该并行,但耗时 {elapsed:.2f}s"


def test_parallel_one_tool_failure_does_not_affect_others():
    """1 个 tool 抛异常,其他 tool 仍正常返,异常被包装成 error dict。"""
    def fake_execute(name, args):
        if name == "boom":
            raise RuntimeError("tool crashed")
        return {"data": {"ok": True}, "navigate_to": f"/x/{name}"}

    with patch("backend.ai.parallel_tools.execute_tool", side_effect=fake_execute):
        tcs = [_tc("a", {}, "1"), _tc("boom", {}, "2"), _tc("c", {}, "3")]
        results = execute_tools_parallel(tcs, max_workers=3)
    assert results[0]["data"]["ok"] is True
    assert "error" in results[1]
    assert "boom" in results[1]["error"]
    assert results[2]["data"]["ok"] is True


def test_parallel_order_preserved():
    """返回顺序与入参顺序一致(用不同延迟验证)。"""
    def fake_execute(name, args):
        # 故意让第二个最慢,验证不会乱序
        delay = 0.05 if name != "slow" else 0.2
        time.sleep(delay)
        return {"data": {"name": name}, "navigate_to": None}

    with patch("backend.ai.parallel_tools.execute_tool", side_effect=fake_execute):
        tcs = [_tc("fast1", {}), _tc("slow", {}), _tc("fast2", {})]
        results = execute_tools_parallel(tcs, max_workers=3)
    assert results[0]["data"]["name"] == "fast1"
    assert results[1]["data"]["name"] == "slow"
    assert results[2]["data"]["name"] == "fast2"
