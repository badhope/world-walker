# LLM 对话助手设计 / AI Chat Assistant Design (v7.0)

> **For agentic workers:** 这是设计文档(spec),不是实施计划(plan)。实施时调用 `writing-plans` skill 转 plan。

**日期**: 2026-06-04
**作者**: Claude (brainstorming skill)
**状态**: Approved (用户 2026-06-04)

---

## 1. 目标 / Goal

为 Regional Economic Analysis Platform 添加 **LLM 对话助手**:
- 用户用**自然语言**问经济/预测/风险/数据问题
- LLM 自动**调用现有投资 API**(forecast/risk/scenarios/lineage 等)取真实数据
- 用**自然语言**总结回答,附引用来源(API + 数据点)
- **双模式可切换**:云端 API(OpenAI/Claude) ↔ 本地 Ollama(Qwen/Llama)
- **轻量前端**:浮动 chat widget,跨页面可用,SSE 流式

**不做**(YAGNI):
- 不做报告生成(NLG → PDF/HTML)— 后续可加
- 不做投资建议自主决策 — 仅"数据 + 模型输出总结",人工判断
- 不做 RAG 文档问答 — 仅调 API 取真实数据
- 不做多 Agent 协作 — 单 Agent + tool calling
- 不做对话长期记忆(Redis)— 仅短期会话级

---

## 2. 架构 / Architecture

### 2.1 数据流

```
[用户输入]
  ↓ 浏览器
[Chat Widget (前端)]
  ↓ POST /api/v1/ai/chat/stream (SSE)
[chat_service.py]  ← FastAPI route handler
  ↓
[llm_client.py]  ← LiteLLM 包装,根据 LLM_DEFAULT_BACKEND 选
  ↓
[OpenAI / Claude / Ollama]  ← 1 个 SDK,1 个 API
  ↓ (function calling: 模型决定调哪个 tool + 参数)
[tool_registry.py]  ← 7 个 tool schema(OpenAI tool spec)
  ↓
[tool_executor.py]  ← 解析 tool call,调现有 API
  ↓
[现有 backend.api.routes.investment + data_lineage]  ← 不动
  ↓
[结果回 tool_executor]
  ↓
[回 LLM 继续生成]  ← 最多 5 轮 tool 调用(防无限循环)
  ↓
[最终答案]
  ↓ SSE 流回
[Chat Widget 打字机渲染]
```

### 2.2 模块依赖

```
backend/ai/
├── __init__.py
├── config.py            # 读 env,选 backend,模型名,温度
├── llm_client.py        # LiteLLM 包装:chat(messages, tools) → response
├── tool_registry.py     # 7 个 tool 的 OpenAI function schema
├── tool_executor.py     # 调现有 API 路由,转 Pydantic → dict
├── chat_service.py      # 主服务:循环 LLM ↔ tool 直到 done
├── prompts.py           # system prompt(中文 + 英文)
└── conversation.py      # 对话历史(短期,session 内存)

backend/api/routes/ai.py  # FastAPI 路由:POST /chat/stream, GET /tools, GET /config

frontend/chat_widget.html  # 浮动 chat widget
frontend/chat_widget.js    # 聊天气泡 + SSE 消费
frontend/chat_widget.css   # 样式
```

### 2.3 与现有代码集成点

- `backend/api/routes/investment.py` — 7 个 tool 包装成 `get_forecast`,`get_risk`, `get_diagnostics`, `get_backtest`, `get_scenarios`, `get_monte_carlo`
- `backend/api/routes/data_lineage.py` — 1 个 tool 包装成 `get_data_provenance`, `get_macro_data`
- `backend/data/historical_extended.py` — Tool 参数校验(SCOPE, INDICATORS 列表)
- 不修改现有投资 API 的 schema — 100% 向后兼容

---

## 3. 配置 / Configuration

### 3.1 环境变量(`.env` + `docker-compose.yml`)

```bash
# === LLM 后端选择 ===
LLM_DEFAULT_BACKEND=openai  # openai | anthropic | ollama | gemini

# === 云端 API keys ===
LLM_OPENAI_API_KEY=sk-...
LLM_OPENAI_MODEL=gpt-4o-mini
LLM_ANTHROPIC_API_KEY=sk-ant-...
LLM_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# === 本地 Ollama ===
LLM_OLLAMA_BASE_URL=http://host.docker.internal:11434
LLM_OLLAMA_MODEL=qwen2.5:7b

# === 行为 ===
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2000
LLM_MAX_TOOL_ROUNDS=5     # 防无限 tool 循环
LLM_TIMEOUT_SEC=60
```

### 3.2 优先级与 fallback

1. `LLM_DEFAULT_BACKEND` 优先
2. 该 backend 不可用(API key 缺 / 连不上)→ 按 `openai → anthropic → ollama` 顺序降级
3. 全部不可用 → 返回 503,前端显示"AI 服务暂不可用,请检查配置"

### 3.3 镜像构建(Docker)

`Dockerfile` 加 `litellm>=1.50` 到 `requirements.txt`。
`docker-compose.yml` 不变(后端通过 env 配 LLM)。
**新增** `docker-compose.ollama.yml`(可选,本地起 ollama 服务):
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: ["ollama-data:/root/.ollama"]
  api:
    environment:
      LLM_DEFAULT_BACKEND: ollama
      LLM_OLLAMA_BASE_URL: http://ollama:11434
```

---

## 4. Tool 设计 / Tool Registry

### 4.1 7 个 tool(OpenAI function calling spec)

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_forecast",
            "description": "获取某城市/省份某指标的多年预测,返回 ensemble 集成预测 + 3 个基模型 + 5 项残差诊断 + 5 项 walk-forward CV",
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "enum": ["city", "province"]},
                    "name": {"type": "string", "description": "城市拼音或省份名"},
                    "indicator": {"type": "string", "enum": INDICATOR_LIST},
                    "years": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                },
                "required": ["scope", "name", "indicator"],
            },
        },
    },
    # ... 其余 6 个类似
]
```

### 4.2 Tool 列表(7 个核心 + 2 个辅助)

| # | Tool name | 包装的 API | 说明 |
|---|---|---|---|
| 1 | `get_forecast` | `GET /api/v1/investment/forecast/full` | 完整预测流水线 |
| 2 | `get_diagnostics` | `GET /api/v1/investment/diagnostics/{scope}/{name}` | 5 项残差诊断 |
| 3 | `get_backtest` | `GET /api/v1/investment/backtest/{scope}/{name}` | walk-forward CV |
| 4 | `get_risk` | `GET /api/v1/investment/risk/{scope}/{name}` | VaR/CVaR/GARCH |
| 5 | `get_scenarios` | `GET /api/v1/investment/scenarios/{scope}/{name}` | 4 档情景 |
| 6 | `get_monte_carlo` | `GET /api/v1/investment/monte-carlo/{scope}/{name}` | 1000-iter MC |
| 7 | `get_data_provenance` | `GET /api/v1/lineage/provenance/city/{name}` | 数据血缘 |
| 8 | `get_macro_data` | `GET /api/v1/lineage/macro` | 4 宏观协变量 |
| 9 | `list_cities` | (读 `cities.yaml`) | 列出可用城市 |

### 4.3 Tool 参数校验

- Tool 调用前:`tool_executor` 用 Pydantic 校验参数
- 不合法参数(例:`indicator="foo"`):返回 `{"error": "invalid indicator, must be one of [...]"}` 给 LLM,LLM 自己重试或告知用户
- Tool 内部错误:返回 `{"error": "internal: ..."}` 500 给 LLM(不暴露 traceback)

---

## 5. API 设计 / Endpoints

### 5.1 `POST /api/v1/ai/chat/stream` (主入口)

**Request**:
```json
{
  "session_id": "uuid",
  "messages": [
    {"role": "user", "content": "深圳 GDP 2026 预测多少?"}
  ]
}
```

**Response** (SSE):
```
event: message
data: {"type": "token", "content": "深圳"}

event: message
data: {"type": "token", "content": " GDP"}

event: message
data: {"type": "tool_call", "name": "get_forecast", "args": {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3}}

event: message
data: {"type": "tool_result", "name": "get_forecast", "result": {"ensemble": {"predictions": [40100, 41700, 43200]}}}

event: message
data: {"type": "token", "content": "2026"}

event: message
data: {"type": "done", "usage": {"prompt_tokens": 250, "completion_tokens": 180}}
```

**错误响应** (SSE):
```
event: error
data: {"code": "llm_unavailable", "message": "OpenAI API 401, check LLM_OPENAI_API_KEY"}
```

### 5.2 `GET /api/v1/ai/tools`

返回 9 个 tool 的 name + description + parameters(供前端展示"AI 能力清单")。

### 5.3 `GET /api/v1/ai/config`

```json
{
  "default_backend": "openai",
  "active_backend": "openai",
  "model": "gpt-4o-mini",
  "available_backends": ["openai", "anthropic", "ollama"],
  "max_tool_rounds": 5
}
```

### 5.4 `POST /api/v1/ai/chat` (非流式,供非浏览器客户端)

同 `stream` 但一次性返回完整 JSON。

---

## 6. 前端 / Chat Widget

### 6.1 UI 设计

- 右下角**浮动按钮**(💬),点击展开聊天窗口
- 聊天窗口 380×600px(可拖动)
- 消息气泡:用户右(蓝),AI 左(灰),tool 调用显示为内嵌 chip
- 输入框 + 发送按钮(Enter 发送,Shift+Enter 换行)
- 顶部下拉:切换 backend(openai/anthropic/ollama)
- 历史:仅当前会话,刷新清空(避免长上下文成本)

### 6.2 SSE 消费

```javascript
const es = new EventSource('/api/v1/ai/chat/stream', { /* withCredentials */ });
es.addEventListener('message', e => {
  const data = JSON.parse(e.data);
  if (data.type === 'token') appendToken(data.content);
  else if (data.type === 'tool_call') showToolChip(data);
  else if (data.type === 'done') es.close();
});
es.addEventListener('error', e => showError('连接中断'));
```

### 6.3 跨页面

每个 HTML 页面末尾加载 `<script src="/chat_widget.js">`,widget 挂在 body,
导航不重置(session_id 存 `sessionStorage`)。

### 6.4 CSP 兼容

`script-src` 加 `'self'`,`connect-src` 加 `http://localhost:8000`(SSE),
`style-src` 加 `'unsafe-inline'`(widget 样式)。在 `investment_grade.html`
等已有 CSP 严格页面中追加。

---

## 7. 对话历史 / Conversation

### 7.1 短期会话级

- 服务端存 dict `session_id -> List[Message]`
- TTL 30 分钟(滑动,无新消息则过期)
- 超过 30 轮自动截断最早(保留 system + 最近 30 轮)

### 7.2 不做长期记忆

- 跨用户/跨设备的记忆 → 后续可加 SQLite/Redis
- 此次 YAGNI

---

## 8. 错误处理 / Error Handling

### 8.1 LLM API 错

| 错误 | 行为 |
|---|---|
| `401` (key 错) | 返回 503,前端显示"AI 服务配置错误" |
| `429` (rate limit) | 自动 retry 1 次(2s 后),仍错则 503 |
| `500/502/503` (上游) | 自动降级到次选 backend,仍错则 503 |
| `timeout` (60s) | 返回 504,前端显示"AI 响应超时" |

### 8.2 Tool 调用错

- Tool 内部 500 → LLM 收到 `{"error": "..."}`,LLM 总结后告诉用户
- Tool 参数不合法 → 同上
- 累计 tool 调用 > `LLM_MAX_TOOL_ROUNDS`(5) → 强制结束,告诉用户"问题太复杂"

### 8.3 用户输入错

- 空消息 → 400
- 单消息 > 4000 字符 → 400
- 频率限制(同一 session 10 msg/min)→ 429

### 8.4 异常监控

- 所有 LLM 调用记录 `prompt_tokens` / `completion_tokens` / `duration_ms` / `tool_rounds`
- `/api/v1/ai/config` 输出累计 token 用量(可选)

---

## 9. 测试 / Testing

### 9.1 单元测试(`tests/backend/test_ai_*.py`)

- `test_llm_client.py` (3 测试):backend 切换 / fallback 链 / 模型名解析
- `test_tool_registry.py` (3 测试):tool schema 完整 / 参数校验 / 名称唯一
- `test_tool_executor.py` (4 测试):成功调用 / 参数错 / API 错 / Pydantic 转换
- `test_chat_service.py` (4 测试):单轮 / 多 tool / 超过 max rounds / 流式输出

### 9.2 集成测试

- `test_ai_e2e.py` (3 测试):真实 LLM(用 mock)对话 / SSE 事件流 / 配置 fallback

### 9.3 前端测试

- `frontend/chat_widget.html` 手动 browser test
- 截图加入 `docs/screenshots/13-ai-chat.png`

### 9.4 覆盖

- 共 ~14 新测试,总 ~277 后端测试
- ruff 新代码 clean

---

## 10. 风险与限制 / Risks & Limitations

| 风险 | 缓解 |
|---|---|
| LLM 幻觉(编造数字) | 强制 tool calling:必须先调 API 拿真实数据,prompt 强调"不要编造数字,所有数字必须从 tool 结果引用" |
| LLM 选错 tool | 7 个 tool 不算多,Claude/GPT-4 选对率 > 95%,加 tool result validation |
| LLM 成本 | 用 `gpt-4o-mini`($0.15/1M tokens),加 `LLM_MAX_TOKENS=2000` |
| 数据出本机(云端 API) | 文档明示 / 用户可切 Ollama / 生产环境建议 Ollama |
| 慢响应(>10s) | SSE 流式边生成边返回,UX 好 |
| Tool 失败导致死循环 | `LLM_MAX_TOOL_ROUNDS=5` 强保护 |
| 中英文混杂 | system prompt 指定"默认中文,术语用英文" |

---

## 11. 实施步骤(高层)/ Implementation Outline

1. **Phase 1**: 安装 `litellm`,加 `LLM_*` env 到 `config.py` + `requirements.txt`
2. **Phase 2**: 写 `tool_registry.py` 9 个 tool + 单元测试
3. **Phase 3**: 写 `tool_executor.py` 调现有 API + Pydantic 转换 + 单元测试
4. **Phase 4**: 写 `llm_client.py` LiteLLM 包装 + 单元测试
5. **Phase 5**: 写 `chat_service.py` 主循环 + 流式输出 + 单元测试
6. **Phase 6**: 写 FastAPI 路由 `/api/v1/ai/chat/stream` + 集成测试
7. **Phase 7**: 写 `frontend/chat_widget.{html,js,css}` + 浏览器测试
8. **Phase 8**: 文档(METHODOLOGY §11 + README + CHANGELOG v7.0)
9. **Phase 9**: 全量 ruff + pytest + commit + push

**预估**: 半天到 1 天。

---

## 12. 验收标准 / Acceptance Criteria

- [ ] 启服务后 `curl /api/v1/ai/config` 返回当前 backend
- [ ] `curl -X POST /api/v1/ai/chat` 不带 stream 也能跑通
- [ ] 浏览器 chat widget 打开后能流式打字
- [ ] 输入"深圳 GDP 2026 预测多少"→ AI 调 `get_forecast` → 返回真实数字
- [ ] 输入"风险如何"→ AI 调 `get_risk` → 返回 VaR/GARCH
- [ ] 切 `LLM_DEFAULT_BACKEND=ollama` 重启 → 自动走本地模型
- [ ] 14 个新测试全过,全量 277 后端测试无回归
- [ ] ruff 新代码 clean
- [ ] 文档更新到 v7.0

---

**最后更新**: 2026-06-04
**版本**: v7.0 (AI Chat Assistant)
**状态**: Ready for plan
