"""Admin store — HistoryStore(ring buffer)+ ConfigStore(hot-swap AIConfig)。

设计:
- 单进程 in-memory(uvicorn 单 worker 够用)
- threading.Lock 保护并发写(history 多线程添加,config 多线程 hot-swap)
- 1000 条 history ring buffer(FIFO 出队)
- AIConfig 是 frozen dataclass → update 时构造新对象,原子 swap
- base_url 不在 AIConfig 里 → 走 os.environ(后端 llm_client 实时读)
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from collections import deque
from typing import Any, Optional, TypedDict

from backend.ai.config import AIConfig

from rca._config import load_config


class QueryRecord(TypedDict):
    """单条 history 记录 — 调一次 tool / chat 的完整 trace 摘要。"""
    id: str
    ts: float
    tool: str  # 调用的 tool 名(chat 时是 "chat")
    params: dict[str, Any]
    result_summary: dict[str, Any]  # 不存全 result,只存摘要(防 history 膨胀)
    duration_ms: int
    status: str  # "ok" / "error"
    error: Optional[str]  # status=error 时填


class HistoryStore:
    """线程安全的 ring buffer,最多 maxlen 条记录。"""

    def __init__(self, maxlen: int = 1000) -> None:
        self._maxlen = maxlen
        self._lock = threading.Lock()
        self._buf: deque[QueryRecord] = deque(maxlen=maxlen)

    def add(self, record: QueryRecord) -> None:
        with self._lock:
            self._buf.append(record)

    def list(
        self, tool: Optional[str] = None, limit: Optional[int] = None,
    ) -> list[QueryRecord]:
        with self._lock:
            items = list(self._buf)
        # 时间倒序(最新在前)
        items.reverse()
        if tool is not None:
            items = [r for r in items if r["tool"] == tool]
        if limit is not None:
            items = items[:limit]
        return items

    def get(self, record_id: str) -> Optional[QueryRecord]:
        with self._lock:
            for r in self._buf:
                if r["id"] == record_id:
                    return r
        return None

    def clear(self) -> None:
        with self._lock:
            self._buf.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._buf)


class ConfigStore:
    """线程安全的 AIConfig hot-swap 存储。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cfg: AIConfig = load_config()

    def get(self) -> AIConfig:
        # 读不需要锁(atomic ref swap 由 GIL 保证)
        return self._cfg

    def update(
        self,
        *,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_tool_rounds: Optional[int] = None,
        timeout_sec: Optional[int] = None,
    ) -> AIConfig:
        """构造新 AIConfig(只改传入字段),原子 swap。

        base_url 不在 AIConfig 里,走 os.environ(后端 llm_client 实时读)。
        """
        with self._lock:
            base = self._cfg
            new_cfg = AIConfig(
                default_backend=base.default_backend,
                active_backend=base.active_backend,
                model=model if model is not None else base.model,
                temperature=temperature if temperature is not None else base.temperature,
                max_tokens=max_tokens if max_tokens is not None else base.max_tokens,
                max_tool_rounds=(
                    max_tool_rounds if max_tool_rounds is not None else base.max_tool_rounds
                ),
                timeout_sec=timeout_sec if timeout_sec is not None else base.timeout_sec,
                available_backends=base.available_backends,
                fallback_chain=base.fallback_chain,
                tool_timeout_sec=base.tool_timeout_sec,
                parallel_max_workers=base.parallel_max_workers,
            )
            self._cfg = new_cfg
        if base_url is not None:
            os.environ["LLM_OPENAI_BASE_URL"] = base_url
        return new_cfg

    def reload_from_env(self) -> AIConfig:
        """从 env 重新 load(用于"恢复默认"按钮)。"""
        with self._lock:
            self._cfg = load_config()
        return self._cfg


# --------------------------------------------------------------------------- #
# module-level 单例 — 整个 FastAPI app 共享
# --------------------------------------------------------------------------- #

_history = HistoryStore(maxlen=1000)
_config = ConfigStore()


def get_history() -> HistoryStore:
    return _history


def get_config_store() -> ConfigStore:
    return _config


def new_query_id() -> str:
    return f"q-{uuid.uuid4().hex[:8]}-{int(time.time() * 1000)}"
