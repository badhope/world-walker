# AI Agent 升级设计 / AI Agent Upgrade Design (v7.1 → v8.0)

> **For agentic workers:** 这是设计文档(spec),不是实施计划(plan)。实施时调用 `writing-plans` skill 转 plan。
>
> **继承:** [2026-06-04-ai-chat-assistant-design.md](file:///workspace/docs/superpowers/specs/2026-06-04-ai-chat-assistant-design.md) (v7.0 LLM 助手) 的所有功能保持,本 spec 仅做增量升级。

**日期**: 2026-06-04
**作者**: Claude (brainstorming skill)
**状态**: Approved (用户 2026-06-04: "全部按顺序来,而且严格进行全部实现")
**版本路线**: v7.0 (chat 助手) → **v7.1 (A: UI 联动)** → **v7.2 (B: ReAct agent + 嵌入 chart)** → **v8.0 (C: agent + test/benchmark)**

---

## 0. 增量目标 / Incremental Goal

把 v7.0 的"单 tool 调用 + 文字回答"助手,升级成**真 AI Agent**,并最终做成**带自检的宏观数据测试平台**:

| 阶段 | 目标 | 用户价值 |
|---|---|---|
| **v7.1 = 方案 A** | Tool-call 结果可点击跳转图表页 | LLM 答了 → 一键看图 |
| **v7.2 = 方案 B** | ReAct 多步推理 + 聊天内嵌 mini chart | 真 agent,自己 plan,答里带图 |
| **v8.0 = 方案 C** | Agent 自检/对照 baseline/回归测试 | 项目从"AI 助手"升级为"AI 驱动 + 可验证"研究平台 |

**3 阶段按顺序、严格实施,每阶段独立 spec → plan → 实施 → 验证 → commit → 进入下一阶段。**

---

## 1. 现状 / Current State (v7.0 已完成)

| 组件 | 现状 | 文件 |
|---|---|---|
| 浮动 chat widget | 纯文本对话,SSE 流式 | [chat_widget.html](file:///workspace/frontend/chat_widget.html), [chat_widget.js](file:///workspace/frontend/chat_widget.js) |
| LLM chat 端点 | `POST /api/v1/ai/chat` (一次性) / `POST /api/v1/ai/chat/stream` (SSE) | [ai.py](file:///workspace/backend/api/routes/ai.py) |
| Chat service | 1 轮 tool call + final 回答 | [chat_service.py](file:///workspace/backend/ai/chat_service.py) |
| Tool executor | 9 个 tool,返 `dict`,无 chart 关联 | [tool_executor.py](file:///workspace/backend/ai/tool_executor.py) |
| 前端图表页 | 3 页:index / investment_grade / province_forecast,echarts | [frontend/](file:///workspace/frontend/) |
| LLM backends | openai / ollama / mock,`qwen-flash` 已验证可调 | [llm_client.py](file:///workspace/backend/ai/llm_client.py) |
| 测试 | 314 pass / 2 fail(env) / 2 skip | `tests/backend/test_ai_*.py` |

**核心痛点:** LLM 调 tool 后只吐文字,前端图表页**不会联动**;chat 不会**多步推理**;没有**自检/回归**能力。

---

## 2. 架构总览 / Architecture Overview

### 2.1 v7.0 (现状)

```
[User] → chat_widget → POST /chat/stream → chat_service
                                              ↓
                                       [1 tool call] → tool_executor → API
                                              ↓
                                       [LLM 写 final 回答] → SSE → widget 渲染文字
```

### 2.2 v7.1 (A: 轻量 UI 联动)

```
[User] → chat_widget → POST /chat/stream → chat_service
                                              ↓
                                       [1 tool call] → tool_executor → {data, navigate_to}
                                              ↓
                                       [LLM 写 final 回答] + tool_call 事件
                                              ↓
                                       SSE: {type: "token"} ... {type: "tool_call", name, args, navigate_to}
                                              ↓
                                       widget 渲染文字 + "📊 在图表中查看" 按钮
                                              ↓
                                       [User 点击] → window.open('/investment_grade.html?city=shenzhen&indicator=gdp')
```

### 2.3 v7.2 (B: ReAct + 嵌入 chart)

```
[User] → chat_widget → POST /chat/stream → chat_service (ReAct loop, max 5 轮)
                                              ↓
                                       [轮 1: Thought → Action(get_forecast) → Observation]
                                              ↓
                                       [轮 2: Thought → Action(get_diagnostics) → Observation]
                                              ↓
                                       [轮 3: Thought → Final 回答]
                                              ↓
                                       SSE: {type: "thinking"} + {type: "tool_call", chart_hint} + {type: "chart", spec} + {type: "token"}...
                                              ↓
                                       widget 渲染文字 + 嵌入 mini echarts(在消息流里)
```

### 2.4 v8.0 (C: Agent + Test/Benchmark)

```
[CI/Manual trigger] → /api/v1/agent/run_suite → agent_runner
                                              ↓
                                       [对每个 test case]
                                       test_case = {name, scope, name, indicator, expected_range, expected_sign}
                                              ↓
                                       agent_runner(ReAct) → 调 tool → 拿结果
                                              ↓
                                       verifier.compare(result, expected) → {pass, drift_pct, notes}
                                              ↓
                                       返回 regression report
                                              ↓
                                       写入 agent_history.jsonl(可审计)
```

---

## 3. 阶段 A: v7.1 轻量 UI 联动

### 3.1 目标
LLM 调 tool 后,前端 chat widget 渲染"在图表中查看"按钮,点击跳转对应页 + URL 参数 prefilled。

### 3.2 改动清单

#### 3.2.1 `backend/ai/tool_executor.py` (改)
每个 tool 的返回 dict 增加 `navigate_to` 字段(可选),映射到前端页面 + 查询参数。

| Tool | navigate_to |
|---|---|
| `get_forecast` | `/investment_grade.html?scope=city&name={name}&indicator={indicator}&years={years}` |
| `get_diagnostics` | `/investment_grade.html?scope=city&name={name}&indicator={indicator}&tab=diagnostics` |
| `get_backtest` | `/investment_grade.html?...&tab=backtest` |
| `get_risk` | `/investment_grade.html?...&tab=risk` |
| `get_scenarios` | `/investment_grade.html?...&tab=scenarios` |
| `get_monte_carlo` | `/investment_grade.html?...&tab=mc` |
| `get_data_provenance` | `/index.html#provenance&city={name}` |
| `get_macro_data` | `/index.html#macro` |
| `list_cities` | (无 — 纯文本列表) |

**实现:** 在 `execute_tool` 包装一层,根据 name 注入 `navigate_to`。

#### 3.2.2 `backend/api/routes/ai.py` (改)
- `/chat/stream` 改:tool result 不再合并到 LLM final prompt,而是 yield 一个**独立 SSE event**:
  ```
  event: message
  data: {"type": "tool_call", "name": "get_forecast", "args": {...}, "result_preview": {"ensemble": {...}}, "navigate_to": "/investment_grade.html?..."}
  ```
- 该事件**在** final token 流**之前** yield,前端可立即渲染按钮,不需等 final。
- `/chat` (一次性端点) 同样:把 tool_call events 拼到响应 JSON 的 `tool_calls: [...]` 字段。

#### 3.2.3 `frontend/chat_widget.js` (改)
- 收到 `type=tool_call` 事件时,在聊天流里**插入一个 chip**:
  ```html
  <div class="tool-chip" data-navigate="...">
    📊 get_forecast(shenzhen, gdp) → 在图表中查看
  </div>
  ```
- chip 点击 → `window.open(data-navigate, '_blank')`(新窗口,用户可保留 chat)

#### 3.2.4 测试
- `tests/backend/test_ai_tool_call_event.py`:验证 tool_executor 返的 dict 含 `navigate_to`;验证 mock 路由在 tool 后 yield 1 个 tool_call event
- `tests/backend/test_ai_widget_chip.py`:验证 parseSSEEvent 解析 type=tool_call;验证 chip DOM 结构

### 3.3 成功标准
- 用户问"深圳 GDP 2026 多少?"→ LLM 答完文字 + 出现 1 个 chip → 点击 chip → 新窗口打开 investment_grade.html 且 URL 已 prefilled
- 不破坏现有 314 测试
- ruff clean

### 3.4 不做
- 不改 investment_grade.html 让其读 URL 参数(留给 v7.2 — 那是图表嵌入)
- 不改 LLM 行为(还是 1 轮 tool + final)— ReAct 留给 v7.2

---

## 4. 阶段 B: v7.2 ReAct Agent + 嵌入 chart

### 4.1 目标
LLM 升级成 ReAct agent:**Thought → Action → Observation** 循环,最多 5 轮,自主多步推理;tool 结果可附带 `chart_hint` 触发 widget 内嵌 echarts mini chart。

### 4.2 改动清单

#### 4.2.1 `backend/ai/agent.py` (新文件)
- `class ReActAgent`:封装 LLM + tool loop
  - `run(user_message, history) -> Iterator[dict]`
  - 内部循环:`max_iterations=5`
  - 每轮:LiteLLM completion 带 `tools=` → 解析 `tool_calls` → 调 `tool_executor.execute_tool` → 把 result 追加到 messages → 继续
  - 当 LLM 不再发 tool_call(返回 `finish_reason="stop"`)→ 写 final 回答
  - 每轮 yield `{"type": "step", "iteration": i, "thought": "...", "action": "...", "observation": "..."}`
- `class ChartHint`:tool_executor 返 `{data, chart_hint: "forecast"|"risk"|"scenarios"|"mc"|"backtest"|None}`
- `class AgentConfig`:from env(YAML/ENV, 跟 `chat_service` 复用)

#### 4.2.2 `backend/ai/chat_service.py` (改)
- 改用 `ReActAgent`;保留 SSE yield 协议,加 step 事件
- 终态:`{"type": "done", "iterations": N, "finish_reason": "..."}`

#### 4.2.3 `backend/ai/tool_executor.py` (改)
- 每个 `_call_*` 函数返回:
  ```python
  {
      "data": {...},                    # 现有 result
      "chart_hint": "forecast",         # 新增:None / "forecast" / "risk" / ...
      "navigate_to": "..."              # v7.1 已加
  }
  ```

#### 4.2.4 `backend/api/routes/ai.py` (改)
- `/chat/stream` 路由:
  - SSE event types: `thinking` / `step` / `tool_call` / `chart` / `token` / `done` / `error`
  - `chart` event: `{"type": "chart", "chart_hint": "forecast", "spec": {"x": [...], "y": [...], "y_upper": [...], "y_lower": [...]}}` — 仅 forecast 算 spec 透传,其他给个简单 spec
- 性能:`max_iterations=5`,timeout=120s(单请求)

#### 4.2.5 `frontend/chat_widget.js` (改)
- 收到 `type=chart` 时,在消息流里**就地画 echarts mini**:
  - `import * as echarts from '...';`(已用 CDN)
  - `echarts.init(div, ..., {renderer: 'svg'})`(svg 渲染,小尺寸快)
  - option 来自 spec
- 收到 `type=step` 时,折叠显示一个 `<details>` 让用户展开看推理过程(可选开关)
- 收到 `type=tool_call` 仍渲染 chip(继承 v7.1)

#### 4.2.6 测试
- `tests/backend/test_ai_react.py`:mock LLM 模拟多轮 tool call;验证迭代次数、最终 done
- `tests/backend/test_ai_chart_spec.py`:验证 4 种 chart_hint 对应的 spec 生成
- `tests/backend/test_ai_widget_chart.py`:验证 `type=chart` 事件被 parseSSEEvent 正确解析

### 4.3 成功标准
- 用户问"深圳 GDP 增长趋势?波动率?" → LLM 多步: 调 get_forecast + get_risk → widget 文字答里嵌 1 个 forecast mini chart + 1 个 risk mini chart
- "step" 折叠区可展开看 Thought/Action/Observation
- SSE 协议向后兼容(老 client 收到 `type=step/chart` 会忽略)
- ruff clean,新测试 pass

### 4.4 不做
- 不做多 agent 协作(留给 v9.0 考虑)
- 不做 chart spec 复杂化(仅 line/area/confidence-band;不做交互)

---

## 5. 阶段 C: v8.0 Agent + Test/Benchmark 框架

### 5.1 目标
项目从"AI 助手"升级为"**带自检的宏观数据 AI 测试平台**":
- 预定义 macro 指标 test suite(8-15 个 case)
- agent 自动跑 suite,对照 baseline / expected range
- 输出 regression report(可写 artifact 给 CI)
- 写 `agent_history.jsonl`(审计 trail)
- 提供 `POST /api/v1/agent/run_suite` 端点
- 提供 `POST /api/v1/agent/verify` 端点(单 tool 结果校验)

### 5.2 改动清单

#### 5.2.1 `backend/agent/verifier.py` (新文件)
- `class Verifier`:
  - `verify(tool_name, result) -> VerifyResult`
  - 校验规则(可配置 YAML):
    - `forecast.ensemble.predictions` 必须是 list[float] 长度 == years
    - `forecast.predictions[0]` 不能 < 0
    - `risk.var_95.var_pct` 必须在 `[-30%, -0.1%]`(单年损失不会超 30% 也不应<0.1%)
    - `backtest.mape` 应 < 15%(ARIMA 季度精度基线)
    - `data_provenance.year_range[0] >= 2000`
    - `macro_data.current.national_gdp` 同比在 `[2%, 10%]`(中国实际)
- `class VerifyResult`: `{pass: bool, checks: [{name, pass, expected, actual, drift_pct}], notes: str}`

#### 5.2.2 `backend/agent/test_suite.py` (新文件)
- `class TestCase`:
  ```python
  @dataclass
  class TestCase:
      name: str
      tool: str
      args: dict
      expected: dict       # e.g. {"ensemble_year_1_range": (3e12, 5e12)}
      description: str
  ```
- `class TestSuite`:从 YAML 加载,内置 12 个 macro test case
  ```yaml
  cases:
    - name: shenzhen_gdp_2026_reasonable
      tool: get_forecast
      args: {scope: city, name: shenzhen, indicator: gdp, years: 1}
      expected:
        ensemble_year_1_range: [3.0e12, 5.0e12]
        diagnostics_verdict: [PASS, FAIL]
    - name: shanghai_risk_var_sane
      tool: get_risk
      args: {scope: city, name: shanghai, indicator: gdp}
      expected:
        var_95_var_pct_range: [-0.30, -0.001]
    - name: macro_data_2025_growth_sane
      tool: get_macro_data
      args: {}
      expected:
        national_gdp_yoy_range: [0.02, 0.10]
    # ... 9 more
  ```

#### 5.2.3 `backend/agent/runner.py` (新文件)
- `class AgentRunner`:
  - `run_suite(suite_name) -> SuiteReport`
  - 对每个 case:调 ReActAgent(或直接调 tool_executor)→ 调 Verifier.verify → 累计
  - 返回 `SuiteReport`:`{suite, run_at, n_cases, n_pass, n_fail, cases: [{name, pass, drift_pct, notes}]}`
- `class HistoryWriter`:每跑完一个 case 追加一行 JSONL 到 `data/agent_history/`

#### 5.2.4 `backend/api/routes/agent.py` (新文件)
- `POST /api/v1/agent/run_suite`:body `{"suite_name": "default"}` → 返 SuiteReport
- `POST /api/v1/agent/verify`:body `{"tool": "get_forecast", "result": {...}}` → 返 VerifyResult
- `GET /api/v1/agent/history?limit=20`:返最近 N 条 history

#### 5.2.5 `config/agent_suite.yaml` (新文件)
预定义 12 个 test case(具体值见 `test_suite.py` 默认)。

#### 5.2.6 `frontend/agent_dashboard.html` (新文件,可选)
- "Agent 测试" 入口页:跑 suite → 显示通过率/失败详情/历史
- echarts 画 7 天/30 天 pass rate trend

#### 5.2.7 CI 集成
- `.github/workflows/agent_regression.yml` (新建):每周/每次 forecast_engine 改动触发 run_suite,失败 → 通知

#### 5.2.8 测试
- `tests/backend/test_agent_verifier.py`:验证 8 条校验规则
- `tests/backend/test_agent_suite.py`:跑默认 12 case(用 mock tool_executor)
- `tests/backend/test_agent_runner.py`:验证 history 写入
- `tests/backend/test_agent_api.py`:验证 3 个新 API endpoint

### 5.3 成功标准
- 12 个 test case 全 pass(对当前真实数据)
- agent 跑完 < 30s
- 任何 forecast_engine 改动触发回归失败时,dev 能拿到含 `drift_pct` 的报告
- 全部历史可在 dashboard 查
- ruff clean,新测试 pass,**老测试不挂**

### 5.4 不做
- 不做外部数据 baseline(只对当前数据 + 简单区间)
- 不做 agent 自动重训练 / 模型选择
- 不做分布式跑 suite

---

## 6. 整体数据流 / Cross-Stage Data Flow

```
[User Input]
   ↓
chat_widget.js  ←  SSE 事件流 (类型化)
   ↓ types: thinking, step, tool_call, chart, token, done, error
/chat/stream
   ↓
agent.py / chat_service.py (v7.2 起 = ReActAgent)
   ↓ 循环
tool_executor.execute_tool(name, args)
   ↓
{data, chart_hint, navigate_to}  ← 三段信息
   ↓
verifier.verify(...)  ← v8.0 新增
   ↓
{pass, drift_pct, ...}
   ↓
history_writer.append(...)  ← v8.0 新增
   ↓
SSE event: chart / tool_call
   ↓
chat_widget.js 渲染 chip / 嵌入 mini chart
```

---

## 7. 版本号 / Versioning

| 版本 | 阶段 | 主功能 | 状态 |
|---|---|---|---|
| v7.0 | — | LLM 助手(单 tool + 文字) | ✓ 已发 |
| **v7.1** | A | Tool-call UI 联动(chip + 跳转) | TODO |
| **v7.2** | B | ReAct agent + 嵌入 chart | TODO |
| **v8.0** | C | Agent + test/benchmark 框架 | TODO |

每个版本独立 commit、独立 plan、独立测试集。

---

## 8. 风险 / Risks

| 风险 | 缓解 |
|---|---|
| ReAct loop 死循环 / 超时 | `max_iterations=5` + 120s timeout + 监控 token usage |
| Tool schema 变更破坏老 client | SSE 事件类型**只增不删**,老 client 忽略未知 type |
| chart spec 大 / 渲染慢 | 仅 4 种 chart_hint + SVG renderer + 限制数据点 ≤ 50 |
| Agent test suite 假阳性 | expected range 用**宽区间**,加漂移百分比显示 |
| 阿里百炼 API 限流 | 默认 backoff + LLM 调用 retry 3 次 |

---

## 9. 测试 / Testing

每阶段新增 5-10 个测试,总数从 314 → 预计 350+ (A: +5, B: +10, C: +15)。每阶段:

```bash
PYTHONPATH=/workspace python -m pytest tests/backend/ -q --no-header
PYTHONPATH=/workspace python -m ruff check /workspace/backend/ /workspace/tests/
```

每阶段独立 commit,跑通才进下一阶段。

---

## 10. 文档 / Documentation

每阶段完成需更新:

| 文档 | 更新点 |
|---|---|
| `CHANGELOG.md` | 新增 `[v7.1]` / `[v7.2]` / `[v8.0]` 段 |
| `README.md` | "AI 助手"章节扩展(各阶段功能) |
| `ROADMAP.md` | v7.1/7.2/8.0 状态更新 |
| `METHODOLOGY.md` | §11 AI 增加各阶段原理 |
| `FAQ.md` | 增加"为什么 ReAct?""回归测试怎么用?"问答 |
| `docs/superpowers/specs/2026-06-04-ai-agent-upgrade-design.md` | 本 spec,版本更新 |

---

## 11. 实施流程 / Implementation Flow

每阶段:
1. 调用 `writing-plans` skill,基于本 spec 写 plan
2. 用户 review plan
3. TDD:写失败测试 → 实现 → 通过
4. 跑 ruff + 全测试
5. commit(独立 commit)
6. smoke test(用真实 LLM key,如果用户借)
7. 进入下一阶段

**3 阶段顺序、严格,不能跳。**

---

## 12. 不做 / Out of Scope (YAGNI)

- 多 Agent 协作 / Agent Marketplace
- RAG 文档问答(知识库)
- 长期对话记忆(Redis/PG)
- 投资建议自主决策
- 报告自动生成(NLG → PDF)
- 实时数据流(目前是历史 + 预测)
- 分布式跑 suite
- 浏览器端 Agent(目前 server-side)
