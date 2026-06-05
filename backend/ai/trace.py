"""Trace 日志:agent 决策过程累积。

设计:
- Step 是不可变 dataclass,记录一步决策(type/round/model/tool/duration/error)
- TraceStore 累积 Step,max_steps 防内存爆炸
- to_dict() 序列化给 SSE done 事件透传
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Step:
    """单步 agent 决策。

    type 取值:
    - "llm_call"     一次 LLM 调用
    - "tool_call"    一次 tool dispatch
    - "tool_result"  tool 返值预览(目前合并到 tool_call,留扩展)
    - "fallback"     LLM 失败降级到下一项
    - "retry"        反射重试
    - "done"         agent 结束
    """
    round: int
    type: str
    model_used: str | None = None
    tool_name: str | None = None
    tool_args: dict | None = None
    tool_result_preview: str | None = None
    duration_ms: int = 0
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "type": self.type,
            "model_used": self.model_used,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "tool_result_preview": self.tool_result_preview,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": self.metadata,
        }


class TraceStore:
    """累积 Step 的 bounded queue。"""

    def __init__(self, max_steps: int = 200):
        self._max = max_steps
        self._steps: deque[Step] = deque(maxlen=max_steps)

    def append(self, step: Step) -> None:
        self._steps.append(step)

    def get_all(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._steps]

    def clear(self) -> None:
        self._steps.clear()
