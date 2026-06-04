"""
Conversation store — 短期 session 级对话历史(内存 dict)。

设计:
- session_id -> list of messages
- TTL 30 分钟(滑动)
- 超过 30 轮自动截断最早(system 保留)
"""
from __future__ import annotations

import threading
import time
from typing import Any

_TTL_SEC = 30 * 60
_MAX_TURNS = 30

_store: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_lock = threading.Lock()


def get_history(session_id: str) -> list[dict[str, Any]]:
    """读取 + 续 TTL(滑动)。不存在返回空 list。"""
    now = time.time()
    with _lock:
        if session_id not in _store:
            return []
        last_ts, msgs = _store[session_id]
        if now - last_ts > _TTL_SEC:
            del _store[session_id]
            return []
        # 续 TTL
        _store[session_id] = (now, msgs)
        return list(msgs)


def append_message(session_id: str, message: dict[str, Any]) -> None:
    """追加一条消息,超过 max turns 截断最早。"""
    with _lock:
        if session_id not in _store:
            _store[session_id] = (time.time(), [])
        _, msgs = _store[session_id]
        msgs.append(message)
        # 截断:保留 system + 最近 30 轮
        system = [m for m in msgs if m.get("role") == "system"]
        non_system = [m for m in msgs if m.get("role") != "system"]
        non_system = non_system[-(_MAX_TURNS * 2):]  # 每轮 = user + assistant
        msgs.clear()
        msgs.extend(system + non_system)
        _store[session_id] = (time.time(), msgs)


def clear_session(session_id: str) -> None:
    with _lock:
        _store.pop(session_id, None)


def cleanup_expired() -> int:
    """清理过期 session(可由定时任务调用)。"""
    now = time.time()
    removed = 0
    with _lock:
        for sid in list(_store.keys()):
            if now - _store[sid][0] > _TTL_SEC:
                del _store[sid]
                removed += 1
    return removed
