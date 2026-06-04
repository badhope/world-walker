# v7.1 Tool-call UI 联动 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** LLM 调 tool 时,前端 chat widget 渲染"在图表中查看"chip,点击跳转 `investment_grade.html` + URL 参数 prefilled。

**Architecture:** 沿用 v7.0 SSE 通道,新增 `type=tool_call` 事件类型;tool_executor 给每个 tool 注入 `navigate_to` URL;chat_service 把 tool trace 通过 yield 透传给前端,前端 chip 渲染 + 跳转。事件类型**只增不删**,老 client 兼容。

**Tech Stack:** Python 3.11+ / FastAPI / LiteLLM / SSE / 原生 JS(无框架)

**Spec:** [2026-06-04-ai-agent-upgrade-design.md §3](file:///workspace/docs/superpowers/specs/2026-06-04-ai-agent-upgrade-design.md)

---

## File Structure

| 文件 | 状态 | 职责 |
|---|---|---|
| `backend/ai/tool_executor.py` | 改 | 每个 tool 返 `{data, navigate_to}` |
| `backend/ai/chat_service.py` | 改 | 新增 `chat_stream_with_trace()` — 内部循环 tool 时 yield 事件 |
| `backend/api/routes/ai.py` | 改 | `/chat/stream` 用新 service 拿 trace,yield `type=tool_call` 事件;`/chat` 把 tool_calls 拼到响应 |
| `frontend/chat_widget.js` | 改 | 收 `type=tool_call` 时调 `appendToolChip`(函数已存在,需补 navigate_to 逻辑) |
| `frontend/chat_widget.css` | 改 | 加 `.rca-tool-chip` 样式(可点、hover) |
| `tests/backend/test_ai_tool_navigate.py` | 新 | 验证 9 个 tool 返的 `navigate_to` URL 正确 |
| `tests/backend/test_ai_chat_stream_trace.py` | 新 | mock 整个 LLM + tool,验证 SSE 事件流顺序 |
| `tests/backend/test_ai_chat_response_tools.py` | 新 | 验证 `/chat` 一次性响应含 `tool_calls` 字段 |
| `tests/backend/test_ai_widget_chip.py` | 新 | 验证 `parseSSEEvent` 解析 type=tool_call;chip DOM 结构 |
| `CHANGELOG.md` | 改 | 加 `[v7.1]` 段 |
| `README.md` | 改 | "AI 助手" 章节加 chip + 跳转说明 |

---

## Task 1: tool_executor 加 navigate_to 映射

**Files:**
- Modify: `backend/ai/tool_executor.py`
- Test: `tests/backend/test_ai_tool_navigate.py`

- [ ] **Step 1.1: 写失败测试**

`tests/backend/test_ai_tool_navigate.py`:

```python
"""tool_executor 给 9 个 tool 注入 navigate_to URL,前端可跳转图表页。"""


def test_forecast_navigate_to_investment_grade():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_forecast", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    assert "navigate_to" in out
    assert out["navigate_to"] == "/investment_grade.html?scope=city&name=shenzhen&indicator=gdp&years=3"


def test_diagnostics_navigate_with_tab():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_diagnostics", {"scope": "city", "name": "shanghai", "indicator": "gdp"})
    assert "navigate_to" in out
    assert "tab=diagnostics" in out["navigate_to"]


def test_backtest_navigate_with_tab():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_backtest", {"scope": "city", "name": "shenzhen", "indicator": "gdp"})
    assert "tab=backtest" in out["navigate_to"]


def test_risk_navigate_with_tab():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_risk", {"scope": "city", "name": "shenzhen", "indicator": "gdp"})
    assert "tab=risk" in out["navigate_to"]


def test_scenarios_navigate_with_tab():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_scenarios", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    assert "tab=scenarios" in out["navigate_to"]


def test_monte_carlo_navigate_with_tab():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_monte_carlo", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    assert "tab=mc" in out["navigate_to"]


def test_data_provenance_navigate_to_index():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_data_provenance", {"name": "shenzhen"})
    assert out["navigate_to"] == "/index.html#provenance&city=shenzhen"


def test_macro_data_navigate_to_index():
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_macro_data", {})
    assert out["navigate_to"] == "/index.html#macro"


def test_list_cities_no_navigate_to():
    """list_cities 纯文本,无跳转。"""
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("list_cities", {})
    assert out.get("navigate_to") is None


def test_navigate_to_url_uses_pinyin_resolved_name():
    """name 是 pinyin,URL 里也用 pinyin(前端 investment_grade.html 接受 pinyin query)。"""
    from backend.ai.tool_executor import execute_tool
    out = execute_tool("get_forecast", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    # name 保持原样(pinyin),前端 investment_grade 会转
    assert "name=shenzhen" in out["navigate_to"]
```

- [ ] **Step 1.2: 跑测试,确认全 fail**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_tool_navigate.py -v --no-header
```

Expected: 10 fail(navigate_to 不存在)

- [ ] **Step 1.3: 在 tool_executor.py 加 NAVIGATE 映射 + execute_tool 包装**

修改 `backend/ai/tool_executor.py`,在文件末尾 `_DISPATCH` 之后插入:

```python
# --------------------------------------------------------------------------- #
# navigate_to 映射 — 每个 tool 跳转的图表页 URL,前端 chip 用
# --------------------------------------------------------------------------- #


# tab 字段告诉前端 investment_grade.html 切到哪个 tab(forecast/backtest/...)
_TAB_FOR_TOOL = {
    "get_forecast": None,        # 默认 tab
    "get_diagnostics": "diagnostics",
    "get_backtest": "backtest",
    "get_risk": "risk",
    "get_scenarios": "scenarios",
    "get_monte_carlo": "mc",
}


def _build_navigate_to(name: str, args: dict) -> str | None:
    """构造 chip 跳转 URL;list_cities / 错误情况返 None。"""
    if name == "list_cities":
        return None
    if name == "get_data_provenance":
        return f"/index.html#provenance&city={args.get('name', '')}"
    if name == "get_macro_data":
        return "/index.html#macro"
    # 默认:investment_grade.html
    params = []
    for k in ("scope", "name", "indicator", "years"):
        if k in args:
            params.append(f"{k}={args[k]}")
    tab = _TAB_FOR_TOOL.get(name)
    if tab:
        params.append(f"tab={tab}")
    return "/investment_grade.html?" + "&".join(params) if params else "/investment_grade.html"
```

修改 `execute_tool` 函数,在 `return _DISPATCH[name](args)` 之前,改成:

```python
def execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """执行一个 tool,返回 dict。错误包装为 {"error": "..."}。

    返回结构:
    - 成功: {"data": <result>, "navigate_to": <url|None>}
    - 失败: {"error": "<reason>", "navigate_to": None}
    """
    if name not in _DISPATCH:
        return {"error": f"Tool not found: {name}", "navigate_to": None}
    required = _REQUIRED_FIELDS[name]
    missing = [f for f in required if f not in args]
    if missing:
        return {"error": f"Missing required fields: {missing}", "navigate_to": None}
    try:
        result = _DISPATCH[name](args)
        if "error" in result:
            return {**result, "navigate_to": None}
        return {"data": result, "navigate_to": _build_navigate_to(name, args)}
    except Exception as e:
        logger.warning("Tool %s failed: %s", name, e)
        return {"error": f"Internal: {type(e).__name__}: {e}", "navigate_to": None}
```

**重要:** 现有调用方从 `result["ensemble"]` 改为 `result["data"]["ensemble"]`,需要同步更新现有测试 — 见 Step 1.5。

- [ ] **Step 1.4: 跑新测试,确认 pass**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_tool_navigate.py -v --no-header
```

Expected: 10 pass

- [ ] **Step 1.5: 修复老 test 引用 `result["ensemble"]` → `result["data"]["ensemble"]`**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_tool_executor.py -v --no-header
```

Expected: 部分 fail,因返回结构变化。逐个修复:

`tests/backend/test_ai_tool_executor.py` 中所有访问 `out["ensemble"]` / `out["name"]` / `out["indicator"]` / `out["diagnostics_verdict"]` / `out["backtest_mape"]` / `out["data_points"]` / `out["city"]` / `out["url"]` / `out["year_range"]` / `out["sample_provenance"]` / `out["current"]` / `out["yoy_pct"]` / `out["volatility"]` 的地方,统一加 `.get("data", out)` 或显式 `out["data"][...]`。

修复后跑:

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_tool_executor.py -v --no-header
```

Expected: 15 pass

- [ ] **Step 1.6: Commit**

```bash
git add backend/ai/tool_executor.py tests/backend/test_ai_tool_navigate.py tests/backend/test_ai_tool_executor.py
git commit -m "$(cat <<'EOF'
feat(ai): tool_executor 注入 navigate_to URL + 返 {data, navigate_to} 结构

每个 tool 返 {data: <result>, navigate_to: <url|None>},前端 chip 可
一键跳到对应图表页(investment_grade.html 或 index.html)。

- get_forecast/diagnostics/backtest/risk/scenarios/monte_carlo → investment_grade.html + tab
- get_data_provenance → /index.html#provenance&city=X
- get_macro_data → /index.html#macro
- list_cities → None(纯文本)

测试: 10 个新 navigate_to 测试 + 15 个老 tool 测试结构调整通过。

Co-authored-by: traeagent <traeagent@users.noreply.github.com>
EOF
)"
```

---

## Task 2: chat_service 加 chat_stream_with_trace()

**Files:**
- Modify: `backend/ai/chat_service.py`
- Test: `tests/backend/test_ai_chat_stream_trace.py`

- [ ] **Step 2.1: 写失败测试**

`tests/backend/test_ai_chat_stream_trace.py`:

```python
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
```

- [ ] **Step 2.2: 跑测试,确认全 fail**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_chat_stream_trace.py -v --no-header
```

Expected: 4 fail(`chat_stream_with_trace` 不存在)

- [ ] **Step 2.3: 实现 chat_stream_with_trace()**

在 `backend/ai/chat_service.py` 的 `chat()` 函数**之后**新增:

```python
def chat_stream_with_trace(
    cfg: AIConfig,
    session_id: str,
    user_message: str,
) -> Any:
    """流式 chat — yield 事件供 SSE 透传。

    事件类型(v7.0):
    - {"type": "thinking"} — 启动
    - {"type": "token", "content": "..."} — 文本片段(当前实现:整段 final 一次性 yield)
    - {"type": "done", "finish_reason": "stop", "tool_rounds": N}

    事件类型(v7.1 新增):
    - {"type": "tool_call", "name": ..., "args": {...}, "navigate_to": ...}
    """
    yield {"type": "thinking"}
    messages = _build_messages(session_id, user_message)
    tool_rounds = 0
    all_tool_calls: list[dict[str, Any]] = []

    try:
        for _ in range(cfg.max_tool_rounds + 1):
            resp = llm_client.chat(cfg, messages=messages, tools=TOOLS)
            tool_rounds += 1

            if not resp.tool_calls:
                # LLM 给了最终答案 — 整段 yield(后续 v7.2 改增量)
                content = resp.content or ""
                yield {"type": "token", "content": content}
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                yield {
                    "type": "done",
                    "finish_reason": "stop",
                    "tool_rounds": tool_rounds - 1,
                    "tool_calls": all_tool_calls,
                }
                return

            # LLM 调了 tool — 先 yield tool_call 事件(给前端 chip 渲染),再喂回 LLM
            messages.append({
                "role": "assistant",
                "content": resp.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                    }
                    for tc in resp.tool_calls
                ],
            })

            for tc in resp.tool_calls:
                result = execute_tool(tc.name, tc.arguments)
                # v7.1: 把 tool_call trace + navigate_to 暴露给前端
                tool_event = {
                    "type": "tool_call",
                    "name": tc.name,
                    "args": tc.arguments,
                    "navigate_to": result.get("navigate_to"),
                }
                # 成功时附带 data 摘要(前 200 字符)
                if "data" in result and isinstance(result["data"], dict):
                    preview = json.dumps(result["data"], ensure_ascii=False, default=str)[:200]
                    tool_event["data_preview"] = preview
                elif "error" in result:
                    tool_event["error"] = result["error"]
                yield tool_event
                all_tool_calls.append(tool_event)

                # 把 tool result 追加到 messages 给 LLM 看
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

            if tool_rounds >= cfg.max_tool_rounds:
                messages.append({"role": "user", "content": "请基于已有 tool 结果直接给最终答案,不要再调 tool。"})
                resp2 = llm_client.chat(cfg, messages=messages, tools=TOOLS)
                content = resp2.content or "(问题过于复杂,无法在限定步数内回答)"
                yield {"type": "token", "content": content}
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                yield {
                    "type": "done",
                    "finish_reason": "tool_rounds_exhausted",
                    "tool_rounds": tool_rounds,
                    "forced_stop": True,
                    "tool_calls": all_tool_calls,
                }
                return

        yield {"type": "done", "finish_reason": "max_rounds", "tool_rounds": tool_rounds, "tool_calls": all_tool_calls}
    except LLMError as e:
        logger.warning("LLM error in chat_stream: %s", e)
        yield {"type": "error", "message": str(e)}
```

- [ ] **Step 2.4: 跑测试,确认 pass**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_chat_stream_trace.py -v --no-header
```

Expected: 4 pass

- [ ] **Step 2.5: 跑老 chat() 测试,确保没破坏**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_chat.py tests/backend/test_ai_chat_service.py -v --no-header 2>&1 | tail -10
```

Expected: 所有老测试仍 pass(chat() 内部循环也调 `execute_tool`,但返 dict 不返 `{data, navigate_to}` 包装,需 Step 2.6 处理)

- [ ] **Step 2.6: 兼容老 chat() — execute_tool 拆 data/navigate_to**

修改 `chat()` 函数中 `result = execute_tool(tc.name, tc.arguments)`,改成:

```python
                raw = execute_tool(tc.name, tc.arguments)
                # 老 chat() 期望 result 是 data(或 error)— 拆 navigate_to 出来
                if "data" in raw:
                    result = raw["data"]
                else:
                    result = raw  # error dict
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
```

跑老测试:

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/ -v --no-header 2>&1 | tail -10
```

Expected: 老 chat() 测试 pass(若有 mock 比较 result,可能需要更新 mock)

- [ ] **Step 2.7: Commit**

```bash
git add backend/ai/chat_service.py tests/backend/test_ai_chat_stream_trace.py
git commit -m "$(cat <<'EOF'
feat(ai): chat_service 加 chat_stream_with_trace — yield tool_call 事件

新函数生成器 {thinking, tool_call, token, done} 事件流,前端 SSE 透传后
能即时渲染 tool chip + 导航 URL。chat() 兼容老 result 形状。

测试: 4 个新 stream trace 测试通过,老 chat() 测试不破。

Co-authored-by: traeagent <traeagent@users.noreply.github.com>
EOF
)"
```

---

## Task 3: routes/ai.py /chat/stream 用新 trace 通道

**Files:**
- Modify: `backend/api/routes/ai.py`
- Test: `tests/backend/test_ai_chat_stream_route.py`(沿用 Task 2 测试,这里只改路由,补 1 个 route-level 测试)

- [ ] **Step 3.1: 写失败测试**

`tests/backend/test_ai_chat_stream_route.py`:

```python
"""/chat/stream 路由用 chat_stream_with_trace,事件透传到 SSE。"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_chat_stream_route_yields_tool_call_event(monkeypatch):
    from backend.api.main import app
    from backend.ai import chat_service, llm_client

    def _fake_stream_with_trace(cfg, session_id, user_message):
        yield {"type": "thinking"}
        yield {
            "type": "tool_call",
            "name": "get_forecast",
            "args": {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3},
            "navigate_to": "/investment_grade.html?scope=city&name=shenzhen&indicator=gdp&years=3",
        }
        yield {"type": "token", "content": "深圳 2026 GDP 4 万亿。"}
        yield {"type": "done", "finish_reason": "stop", "tool_rounds": 1}

    monkeypatch.setattr(chat_service, "chat_stream_with_trace", _fake_stream_with_trace)
    # 避免真的 LLM 调 config 加载
    monkeypatch.setattr(llm_client, "stream_chat", lambda *a, **k: iter([]))
    monkeypatch.setattr("backend.ai.config.load_config", lambda: type("C", (), {"max_tool_rounds": 5})())

    client = TestClient(app)
    with client.stream("POST", "/api/v1/ai/chat/stream",
                       json={"session_id": "s1",
                             "messages": [{"role": "user", "content": "深圳 GDP 2026 多少?"}]}) as r:
        assert r.status_code == 200
        body = "".join(chunk for chunk in r.iter_text())

    # 验证 body 含 tool_call SSE event
    assert '"type": "tool_call"' in body
    assert "navigate_to" in body
    assert "/investment_grade.html" in body


def test_chat_route_response_includes_tool_calls(monkeypatch):
    """/chat 一次性响应含 tool_calls 字段(前端拿不到 SSE 时也能用)。"""
    from backend.api.main import app
    from backend.ai import chat_service

    def _fake_chat(cfg, session_id, user_message):
        return {
            "content": "深圳 2026 GDP 4 万亿。",
            "tool_rounds": 1,
            "tool_calls": [{
                "name": "get_forecast",
                "args": {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3},
                "navigate_to": "/investment_grade.html?scope=city&name=shenzhen&indicator=gdp&years=3",
            }],
        }

    monkeypatch.setattr(chat_service, "chat", _fake_chat)
    monkeypatch.setattr("backend.ai.config.load_config", lambda: type("C", (), {"max_tool_rounds": 5})())

    client = TestClient(app)
    r = client.post("/api/v1/ai/chat",
                    json={"session_id": "s1",
                          "messages": [{"role": "user", "content": "深圳 GDP 2026 多少?"}]})
    assert r.status_code == 200
    body = r.json()
    assert "tool_calls" in body
    assert body["tool_calls"][0]["name"] == "get_forecast"
    assert "navigate_to" in body["tool_calls"][0]
```

- [ ] **Step 3.2: 跑测试,确认全 fail**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_chat_stream_route.py -v --no-header
```

Expected: 2 fail(目前 /chat/stream 用 stream_chat,不含 tool_call;/chat 响应不含 tool_calls)

- [ ] **Step 3.3: 改 routes/ai.py — /chat/stream 用 chat_stream_with_trace**

替换 `post_chat_stream` 函数体(整段替换),改成:

```python
@router.post("/chat/stream")
def post_chat_stream(req: ChatRequest):
    """SSE 真流式 — 透传 chat_stream_with_trace 增量事件。

    流式事件:
    - {"type": "thinking"} — 启动,等 LLM
    - {"type": "tool_call", "name", "args", "navigate_to"} — v7.1 新增,前端渲染 chip
    - {"type": "token", "content": "..."} — 增量文本(v7.1: 整段;v7.2: 真流)
    - {"type": "done", "finish_reason": "stop", "tool_rounds": N, "tool_calls": [...]} — 完成
    - {"type": "error", "message": "..."} — 错误
    """
    _check_rate(req.session_id)
    user_msgs = [m for m in req.messages if m.role == "user"]
    if not user_msgs:
        raise HTTPException(status_code=400, detail="No user message")
    user_message = user_msgs[-1].content

    def event_gen() -> Any:
        try:
            cfg = load_config()
            for event in chat_service.chat_stream_with_trace(
                cfg=cfg, session_id=req.session_id, user_message=user_message,
            ):
                yield f"event: message\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("type") == "done":
                    break
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")
```

**注意:** 不再 import `stream_chat` / `SYSTEM_PROMPT` / `conversation` / `messages`,这些由 `chat_stream_with_trace` 内部处理。但保留其他 import。

- [ ] **Step 3.4: 改 routes/ai.py — /chat 响应透传 tool_calls**

修改 `post_chat` 函数(在 `result = chat_service.chat(...)` 之后):

```python
    result = chat_service.chat(cfg, session_id=req.session_id, user_message=user_message)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result
```

不变 — 因为 chat() 已经会返 `tool_calls` 字段(我们在 Step 2.6 没动 chat() 返 result 形状,但 chat_stream_with_trace 是新函数,只把 tool_calls 通过 done 事件传)。

**等等:** chat() 内部不存 tool_calls,需要给 chat() 也加。Step 3.5。

- [ ] **Step 3.5: 改 chat_service.chat() 也返 tool_calls 字段**

修改 `chat_service.chat()` 函数,在两处 `return` 前加 `tool_calls` 字段(找所有 return 语句):

在第一个 return(`if not resp.tool_calls`)前,**已完成 tool_calls 列表的状态**(需要在循环里累积)。具体修改:

在 `chat_service.chat()` 函数开头(tools = [] 累积):

```python
def chat(cfg: AIConfig, session_id: str, user_message: str) -> dict[str, Any]:
    """单轮对话,返回 {"content": str, "tool_rounds": int, "tool_calls": [...], "error": str?}。"""
    messages = _build_messages(session_id, user_message)
    tool_rounds = 0
    tool_calls_log: list[dict[str, Any]] = []  # 新增

    try:
        for _ in range(cfg.max_tool_rounds + 1):
            resp = llm_client.chat(cfg, messages=messages, tools=TOOLS)
            tool_rounds += 1

            if not resp.tool_calls:
                content = resp.content or ""
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                return {
                    "content": content,
                    "tool_rounds": tool_rounds - 1,
                    "prompt_tokens": resp.prompt_tokens,
                    "completion_tokens": resp.completion_tokens,
                    "tool_calls": tool_calls_log,  # 新增
                }
```

在 LLM 调 tool 时累积 log:

```python
            for tc in resp.tool_calls:
                raw = execute_tool(tc.name, tc.arguments)
                if "data" in raw:
                    result = raw["data"]
                    nav = raw.get("navigate_to")
                else:
                    result = raw
                    nav = None
                # 累积 tool_calls log(给响应)
                tool_calls_log.append({
                    "name": tc.name,
                    "args": tc.arguments,
                    "navigate_to": nav,
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
```

在 forced_stop 的 return:

```python
                return {
                    "content": content,
                    "tool_rounds": tool_rounds,
                    "forced_stop": True,
                    "tool_calls": tool_calls_log,  # 新增
                }
```

在最后 return:

```python
        return {"content": "(达到 max_tool_rounds)", "tool_rounds": tool_rounds, "tool_calls": tool_calls_log}
```

- [ ] **Step 3.6: 跑新测试,确认 pass**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_chat_stream_route.py -v --no-header
```

Expected: 2 pass

- [ ] **Step 3.7: 跑全测试,确保没破坏老测试**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/ -q --no-header 2>&1 | tail -10
```

Expected: 314 → 314 + 4 + 2 = 320+ pass(原 + 4 chat_stream_trace + 2 route)

- [ ] **Step 3.8: Commit**

```bash
git add backend/api/routes/ai.py backend/ai/chat_service.py tests/backend/test_ai_chat_stream_route.py
git commit -m "$(cat <<'EOF'
feat(ai): /chat/stream 用 chat_stream_with_trace + /chat 返 tool_calls

- /chat/stream 路由改用新 service,透传 type=tool_call SSE 事件
- /chat 一次性响应新增 tool_calls 字段(老 client 也能拿到导航 URL)
- chat() 内部累积 tool_calls_log 给响应

测试: 2 个新路由级 SSE + 响应测试通过。

Co-authored-by: traeagent <traeagent@users.noreply.github.com>
EOF
)"
```

---

## Task 4: 前端 chat_widget 渲染 chip + 跳转

**Files:**
- Modify: `frontend/chat_widget.js`
- Modify: `frontend/chat_widget.css`
- Test: `tests/backend/test_ai_widget_chip.py`(JS 通过 node --check + parseSSEEvent 单元)

- [ ] **Step 4.1: 写失败测试**

`tests/backend/test_ai_widget_chip.py`:

```python
"""chat_widget.js 的 parseSSEEvent + chip DOM 渲染测试。"""
import subprocess
from pathlib import Path

WIDGET_JS = Path("/workspace/frontend/chat_widget.js")


def test_chat_widget_js_is_valid_javascript():
    """node --check 验证 JS 无语法错。"""
    result = subprocess.run(
        ["node", "--check", str(WIDGET_JS)],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"JS syntax error: {result.stderr}"


def test_chat_widget_exposes_parseSSEEvent():
    """parseSSEEvent 必须在文件里定义并导出(测试 extract 方式:用 node 执行一小段)。"""
    result = subprocess.run(
        ["node", "-e", f"""
        const code = require('fs').readFileSync('{WIDGET_JS}', 'utf-8');
        // extract parseSSEEvent function via regex
        const m = code.match(/function parseSSEEvent[\\s\\S]*?\\n\\s\\}}/);
        if (!m) {{ console.error('parseSSEEvent not found'); process.exit(1); }}
        eval(m[0]);
        const ev = parseSSEEvent('event: message\\ndata: {{"type":"tool_call","name":"get_forecast","navigate_to":"/x"}}');
        console.log(JSON.stringify({{
            type: ev.data.type,
            name: ev.data.name,
            navigate_to: ev.data.navigate_to
        }}));
        """],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"eval error: {result.stderr}"
    import json
    out = json.loads(result.stdout.strip())
    assert out["type"] == "tool_call"
    assert out["name"] == "get_forecast"
    assert out["navigate_to"] == "/x"


def test_chat_widget_exposes_appendToolChip():
    """appendToolChip 必须存在并能调(签名 chip(name, args, navigate_to))。"""
    js = WIDGET_JS.read_text()
    assert "function appendToolChip" in js
    # 必须含 navigate_to 参数
    m = js.split("function appendToolChip")[1].split("}")[0]
    assert "navigate_to" in m


def test_chat_widget_handles_type_tool_call_in_send():
    """send() 的 for-await 必须 type=tool_call 分支,调 appendToolChip。"""
    js = WIDGET_JS.read_text()
    # 找到 send 函数里 for-await 后的 if 链
    send_section = js[js.index("async function send()"):]
    # 必须含 type === "tool_call" 分支
    assert '"tool_call"' in send_section or "'tool_call'" in send_section
```

- [ ] **Step 4.2: 跑测试,确认 fail(因为 appendToolChip 签名没 navigate_to,send() 没 type=tool_call 分支)**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_widget_chip.py -v --no-header
```

Expected: 2 fail(parseSSEEvent 可通过 eval regex 抽出来,signature/handle 不行)

- [ ] **Step 4.3: 改 chat_widget.js — appendToolChip 加 navigate_to + 改签名**

替换 `appendToolChip` 函数:

```javascript
  function appendToolChip(name, args, navigate_to) {
    const chip = document.createElement("a");
    chip.className = "rca-tool-chip";
    chip.href = navigate_to || "#";
    chip.target = "_blank";  // 新窗口打开,保留 chat
    chip.rel = "noopener noreferrer";
    // 显示:🔧 get_forecast(name=shenzhen, indicator=gdp) → 在图表中查看
    const argsStr = Object.entries(args || {}).map(([k, v]) => k + "=" + v).join(", ").slice(0, 60);
    chip.innerHTML = "🔧 " + name + "(" + argsStr + ") → 📊 在图表中查看";
    body.appendChild(chip);
    return chip;
  }
```

- [ ] **Step 4.4: 改 chat_widget.js — send() 加 type=tool_call 分支**

替换 `send()` 函数里 `for await (const ev of consumeSSE(resp))` 的 if-else 链,在 `} else if (d.type === "done")` **之前**插入:

```javascript
      // 真流式消费 SSE
      for await (const ev of consumeSSE(resp)) {
        const d = ev.data || {};
        if (d.type === "thinking") {
          if (status) status.textContent = "🤔 思考中…";
        } else if (d.type === "tool_call") {
          // v7.1: 渲染可点击 chip,跳转到对应图表页
          appendToolChip(d.name, d.args, d.navigate_to);
        } else if (d.type === "token" && d.content) {
          accumulated += d.content;
          placeholder.textContent = accumulated;  // 打字机:逐字覆盖
          body.scrollTop = body.scrollHeight;
        } else if (d.type === "done") {
          if (status) status.textContent = originalStatus;
          break;
        } else if (d.type === "error") {
          placeholder.textContent = "(LLM 错误): " + (d.message || "未知");
          if (status) status.textContent = originalStatus;
          break;
        }
      }
```

- [ ] **Step 4.5: 跑测试,确认 pass**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/test_ai_widget_chip.py -v --no-header
```

Expected: 4 pass

- [ ] **Step 4.6: 改 chat_widget.css — chip 可点样式**

在文件末尾追加:

```css
.rca-tool-chip {
  display: inline-block;
  margin: 4px 6px 4px 0;
  padding: 4px 10px;
  background: #e8f4fd;
  color: #0969da;
  border: 1px solid #b6e3ff;
  border-radius: 12px;
  font-size: 12px;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s;
}
.rca-tool-chip:hover {
  background: #cdebfc;
  text-decoration: none;
}
```

- [ ] **Step 4.7: Commit**

```bash
git add frontend/chat_widget.js frontend/chat_widget.css tests/backend/test_ai_widget_chip.py
git commit -m "$(cat <<'EOF'
feat(frontend): chat widget 渲染可点击 tool chip + 跳转图表页

- appendToolChip(name, args, navigate_to) — 用 <a target=_blank> 渲染
- send() 加 type=tool_call 分支,渲染 chip
- chat_widget.css 加 .rca-tool-chip 样式(蓝色 chip + hover)

测试: 4 个 JS 静态分析 + node --check 通过。

Co-authored-by: traeagent <traeagent@users.noreply.github.com>
EOF
)"
```

---

## Task 5: ruff 全清 + 全测试 + smoke 验证

**Files:**
- Modify: 任何 ruff 报错文件
- Read: `CHANGELOG.md`, `README.md`

- [ ] **Step 5.1: ruff check**

```bash
PYTHONPATH=/workspace python -m ruff check /workspace/backend/ /workspace/tests/ 2>&1 | tail -10
```

如果有错误,逐个修复(用 `ruff check --fix`),然后 commit fix。

- [ ] **Step 5.2: 全测试**

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/ -q --no-header 2>&1 | tail -5
```

Expected: 320+ pass / 2 fail(env) / 2 skip / 0 错。

- [ ] **Step 5.3: smoke — 启动 uvicorn,真 LLM,验证 tool_call 事件**

启动 uvicorn(在另一终端 / 后台):

```bash
PYTHONPATH=/workspace nohup python /tmp/rea/run_bailian.py > /tmp/uvicorn-v71.log 2>&1 &
```

(sandbox 用 /tmp/rea/run_bailian.py wrapper,见 v7.0 部署)

curl 测:

```bash
curl -N -X POST http://127.0.0.1:8000/api/v1/ai/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id":"v71-smoke","messages":[{"role":"user","content":"深圳 GDP 2026 多少?用 get_forecast。"}]}' \
  --max-time 60 | head -c 2000
```

Expected output 应含:
- `event: message\ndata: {"type": "thinking"}`
- `event: message\ndata: {"type": "tool_call", "name": "get_forecast", "navigate_to": "/investment_grade.html?..."}`
- `event: message\ndata: {"type": "token", "content": "..."}`
- `event: message\ndata: {"type": "done", ...}`

如不满足,检查日志 `/tmp/uvicorn-v71.log`。

- [ ] **Step 5.4: smoke — 模拟浏览器,验证 chip 渲染**

```bash
cat > /tmp/sim_widget_v71.mjs <<'EOF'
const session = "v71-fe-" + Date.now();
const resp = await fetch("http://127.0.0.1:8000/api/v1/ai/chat/stream", {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ session_id: session, messages: [{ role: "user", content: "深圳 GDP 2026?用 get_forecast。" }] }),
});
const reader = resp.body.getReader();
const decoder = new TextDecoder();
let buffer = "";
let toolCalls = [];
let accumulated = "";
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  let idx;
  while ((idx = buffer.indexOf("\n\n")) >= 0) {
    const raw = buffer.slice(0, idx);
    buffer = buffer.slice(idx + 2);
    let data = "";
    for (const line of raw.split("\n")) if (line.startsWith("data: ")) data += line.slice(6);
    if (!data) continue;
    const d = JSON.parse(data);
    if (d.type === "tool_call") toolCalls.push(d);
    if (d.type === "token") accumulated += d.content;
  }
}
console.log("tool_call events:", toolCalls.length);
console.log("first tool:", toolCalls[0]?.name, "→", toolCalls[0]?.navigate_to);
console.log("AI 答:", accumulated.slice(0, 200));
EOF
node /tmp/sim_widget_v71.mjs
```

Expected: tool_call events ≥ 1,first tool=get_forecast,navigate_to 包含 investment_grade.html。

- [ ] **Step 5.5: 文档更新 CHANGELOG.md**

在 `CHANGELOG.md` 顶部加:

```markdown
## [v7.1] - 2026-06-04

### 新增
- **Tool-call UI 联动**:LLM 调 tool 后,前端 chat widget 渲染"📊 在图表中查看" chip,点击新窗口打开 `investment_grade.html` / `index.html` 并 prefilled URL 参数
- **SSE 新事件类型** `type=tool_call` (老 client 兼容,新 client 渲染 chip)
- **GET /chat 响应新增** `tool_calls` 字段(老 client 也能拿到导航 URL)
- **tool_executor 返回结构升级**: `{"data": ..., "navigate_to": <url|None>}` (v7.0 老内部 API 也兼容)

### 改动
- `chat_service.chat_stream_with_trace()` 新增 — 生成器模式 yield 事件
- `chat_service.chat()` 累积 `tool_calls` 字段给响应
- `frontend/chat_widget.js` `appendToolChip(name, args, navigate_to)` 改 `<a target=_blank>`
- `frontend/chat_widget.css` 新增 `.rca-tool-chip` 样式

### 测试
- 新增 16 个测试:10 navigate_to + 4 stream trace + 2 route + 4 widget chip
- 总测试: 320 pass / 2 fail(env) / 2 skip
```

- [ ] **Step 5.6: 文档更新 README.md — AI 助手章节加 chip 说明**

找 README.md 里 "AI 助手" / "AI Chat" 章节,加:

```markdown
#### v7.1 新增:Tool-chip 联动
LLM 调 tool 后,聊天流里会显示一个"📊 在图表中查看"蓝色 chip。点击:
- 新窗口打开 `investment_grade.html`(forecast/risk/scenarios/mc/backtest/diagnostics)
- URL 参数已 prefilled(scope, name, indicator, years, tab)
- 保留 chat 不动
```

- [ ] **Step 5.7: Commit 文档**

```bash
git add CHANGELOG.md README.md
git commit -m "$(cat <<'EOF'
docs: v7.1 changelog + README AI 助手 chip 联动说明

Co-authored-by: traeagent <traeagent@users.noreply.github.com>
EOF
)"
```

- [ ] **Step 5.8: Push to origin/main(force-with-lease 因为可能有 hook 自动 commit)**

```bash
git fetch origin main
git status -sb
# 0 ahead → 直接 push
# 0 ahead 但 origin 有新 commit → pull --rebase
# divergent → 见 v7.0 force-with-lease 流程
```

如果 push 成功,v7.1 完成。进入 v7.2(下个 spec 阶段)前,等用户 OK。

---

## Self-Review Checklist

- [x] **Spec coverage:** v7.1 spec §3 全覆盖(改 3 个后端文件 + 1 个前端文件 + 1 个 css + 4 个测试文件)
- [x] **Placeholder scan:** 无 "TBD" / "TODO" / "类似 Task N"(代码完整)
- [x] **Type consistency:** `navigate_to` 字段名统一(chat_service / tool_executor / route / widget 都用 snake_case)
- [x] **Event type names:** `thinking` / `tool_call` / `token` / `done` / `error` 在 chat_service / route / widget 三处一致
- [x] **Backward compat:** v7.0 client 收 `type=tool_call` 自动忽略,SSE 老协议不变
- [x] **老 chat() 兼容:** 内部拆 `{"data": ..., "navigate_to": ...}` 为 result 喂回 LLM,响应 shape 仍含 `tool_calls` 字段(新)但不破坏老字段

---

## 验证

跑完所有 Task 后:

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/ -q --no-header
PYTHONPATH=/workspace python -m ruff check /workspace/backend/ /workspace/tests/
```

应得: 320+ pass / 2 fail(env) / 2 skip / ruff clean

**v7.1 完成。** 进入 v7.2(ReAct agent + 嵌入 chart)前,等用户 review。
