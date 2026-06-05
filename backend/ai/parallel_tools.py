"""并行 tool 执行 — ThreadPoolExecutor 包装。

设计:
- 默认 max_workers=5(9 个 tool 不会一次全调)
- 顺序保持(用 enumerate 索引)
- 异常隔离(单个失败不影响其他,异常包装成 {"error": "..."})
- tool_timeout_sec 单 tool 超时(从 cfg 读,默认 30s)
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import Any

from backend.ai.llm_client import ToolCall
from backend.ai.tool_executor import execute_tool

logger = logging.getLogger(__name__)


def execute_tools_parallel(
    tool_calls: list[ToolCall],
    max_workers: int = 5,
    tool_timeout_sec: int = 30,
) -> list[dict[str, Any]]:
    """并行执行 tool_call 列表,返与入参同序的 result dict 列表。"""
    if not tool_calls:
        return []

    results: list[dict[str, Any] | None] = [None] * len(tool_calls)
    executor = ThreadPoolExecutor(max_workers=min(max_workers, len(tool_calls)))

    def _run(idx: int, tc: ToolCall) -> None:
        try:
            results[idx] = execute_tool(tc.name, tc.arguments)
        except Exception as e:
            logger.warning("tool %s failed in parallel: %s", tc.name, e)
            results[idx] = {
                "error": f"{tc.name}: {type(e).__name__}: {e}",
                "navigate_to": None,
            }

    futures = [executor.submit(_run, i, tc) for i, tc in enumerate(tool_calls)]
    # 等全部完成(带超时)
    for i, future in enumerate(futures):
        try:
            future.result(timeout=tool_timeout_sec)
        except FuturesTimeoutError:
            logger.warning("tool %s timeout after %ss", tool_calls[i].name, tool_timeout_sec)
            results[i] = {
                "error": f"{tool_calls[i].name}: timeout after {tool_timeout_sec}s",
                "navigate_to": None,
            }
        except Exception as e:
            # _run 已捕获,但 double-check
            if results[i] is None:
                results[i] = {"error": f"{tool_calls[i].name}: {e}", "navigate_to": None}

    executor.shutdown(wait=True)
    return results  # type: ignore[return-value]
