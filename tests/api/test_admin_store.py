"""admin_store 单元测试 — HistoryStore FIFO + ConfigStore hot-swap。"""
from __future__ import annotations

import os
import threading
import time
import uuid

import pytest

# 必须先设 env(在 import rca._config 之前)
os.environ.setdefault("LLM_OPENAI_API_KEY", "sk-test-fake-key-for-admin-store")
os.environ.setdefault("LLM_DEFAULT_BACKEND", "openai")

from backend.api.admin_store import (  # noqa: E402
    ConfigStore,
    HistoryStore,
    QueryRecord,
)

# --------------------------------------------------------------------------- #
# HistoryStore
# --------------------------------------------------------------------------- #


def test_history_add_and_list():
    h = HistoryStore(maxlen=10)
    rec = QueryRecord(
        id="q1", ts=time.time(), tool="get_forecast",
        params={"city": "shenzhen"}, result_summary={"pred0": 1234.5},
        duration_ms=42, status="ok",
    )
    h.add(rec)
    items = h.list()
    assert len(items) == 1
    assert items[0]["id"] == "q1"
    assert items[0]["tool"] == "get_forecast"


def test_history_fifo_eviction_at_maxlen():
    h = HistoryStore(maxlen=3)
    for i in range(5):
        h.add(QueryRecord(
            id=f"q{i}", ts=float(i), tool="get_forecast", params={},
            result_summary={}, duration_ms=0, status="ok",
        ))
    items = h.list()
    assert len(items) == 3
    # FIFO:q0 q1 被踢,留下 q2 q3 q4(按时间倒序,最新 q4 在前)
    assert [r["id"] for r in items] == ["q4", "q3", "q2"]


def test_history_filter_by_tool():
    h = HistoryStore(maxlen=100)
    h.add(QueryRecord(id="q1", ts=1.0, tool="get_forecast", params={}, result_summary={}, duration_ms=0, status="ok"))
    h.add(QueryRecord(id="q2", ts=2.0, tool="get_diagnostics", params={}, result_summary={}, duration_ms=0, status="ok"))
    h.add(QueryRecord(id="q3", ts=3.0, tool="get_forecast", params={}, result_summary={}, duration_ms=0, status="ok"))
    fc = h.list(tool="get_forecast")
    assert len(fc) == 2
    assert all(r["tool"] == "get_forecast" for r in fc)
    # 时间倒序(最新在前)
    assert fc[0]["id"] == "q3"


def test_history_list_with_limit():
    h = HistoryStore(maxlen=100)
    for i in range(10):
        h.add(QueryRecord(id=f"q{i}", ts=float(i), tool="t", params={}, result_summary={}, duration_ms=0, status="ok"))
    items = h.list(limit=3)
    assert len(items) == 3
    # 最新 3 个:q9 q8 q7(时间倒序)
    assert [r["id"] for r in items] == ["q9", "q8", "q7"]


def test_history_get_by_id():
    h = HistoryStore(maxlen=10)
    h.add(QueryRecord(id="q1", ts=1.0, tool="t", params={}, result_summary={}, duration_ms=0, status="ok"))
    rec = h.get("q1")
    assert rec is not None
    assert rec["id"] == "q1"
    assert h.get("nonexistent") is None


def test_history_clear():
    h = HistoryStore(maxlen=10)
    h.add(QueryRecord(id="q1", ts=1.0, tool="t", params={}, result_summary={}, duration_ms=0, status="ok"))
    assert len(h.list()) == 1
    h.clear()
    assert len(h.list()) == 0


def test_history_thread_safety():
    """并发 add 不丢、不破。"""
    h = HistoryStore(maxlen=1000)
    n_threads = 10
    per_thread = 100

    def worker(tid):
        for i in range(per_thread):
            h.add(QueryRecord(
                id=f"q{tid}-{i}", ts=time.time(), tool="t",
                params={}, result_summary={}, duration_ms=0, status="ok",
            ))

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # 1000 条全在(没超 maxlen)
    assert len(h.list()) == n_threads * per_thread


# --------------------------------------------------------------------------- #
# ConfigStore
# --------------------------------------------------------------------------- #


def test_config_get_returns_aiconfig():
    c = ConfigStore()
    from backend.ai.config import AIConfig
    cfg = c.get()
    assert isinstance(cfg, AIConfig)


def test_config_update_changes_model():
    c = ConfigStore()
    original_model = c.get().model
    try:
        new_cfg = c.update(model="deepseek-v3")
        assert new_cfg.model == "deepseek-v3"
        # 立刻再 get 拿到新 cfg
        assert c.get().model == "deepseek-v3"
        assert c.get().model != original_model or original_model == "deepseek-v3"
    finally:
        # 还原
        c.update(model=original_model)


def test_config_update_sets_base_url_env(monkeypatch):
    monkeypatch.delenv("LLM_OPENAI_BASE_URL", raising=False)
    c = ConfigStore()
    original_model = c.get().model
    try:
        c.update(base_url="https://my-gw.example.com/v1")
        assert os.environ["LLM_OPENAI_BASE_URL"] == "https://my-gw.example.com/v1"
    finally:
        c.update(model=original_model)
        monkeypatch.delenv("LLM_OPENAI_BASE_URL", raising=False)


def test_config_update_preserves_other_fields():
    """改 model 不影响 temperature / max_tokens / fallback_chain。"""
    c = ConfigStore()
    base = c.get()
    new_cfg = c.update(model="x")
    assert new_cfg.temperature == base.temperature
    assert new_cfg.max_tokens == base.max_tokens
    assert new_cfg.fallback_chain == base.fallback_chain


def test_config_update_thread_safety():
    """并发 update 不 race(后写的赢)。"""
    c = ConfigStore()
    base = c.get().model
    try:
        def worker(name):
            c.update(model=name)

        t1 = threading.Thread(target=worker, args=("model-a",))
        t2 = threading.Thread(target=worker, args=("model-b",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        # 终态是 a 或 b
        assert c.get().model in ("model-a", "model-b")
    finally:
        c.update(model=base)
