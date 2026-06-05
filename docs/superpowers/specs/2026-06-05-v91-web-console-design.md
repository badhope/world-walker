# RCA Web Console — Phase 2 Design (v9.1.0)

> **Status**: design — pending user approval
> **Date**: 2026-06-05
> **Author**: designed + spec'd by Claude (no user Q&A — user delegated design)

## 1. Goal

为已经能用 SDK/CLI 调用的 9 个 tool + chat agent 提供一个 **Web 管理界面**,让非开发者(分析师、决策者、产品经理)也能:
- 在浏览器里调 9 个 tool(form 提交 → 实时可视化结果)
- 跟 chat agent 对话(LLM 自动调 tool)
- 改 LLM 配置(model / base URL / temperature / max tokens / max tool rounds)
- 看历史记录(最近 1000 条 query + 复跑)

## 2. Scope / Non-Goals

### In scope
- 9 个 tool 全部有 UI 页面(form + 跑 + 渲染)
- chat 页面(支持多 session)
- settings 页面(runtime 改 LLM config)
- history 页面(查看 + 复跑 + 导出 + 清空)
- dashboard 落地页(状态 + 9 tool 卡片 + 最近 5 条)
- 8 个后端 endpoint
- 真 ECharts 可视化(forecast/risk/monte_carlo 的图)
- 匹配现有 editorial 风格(深墨蓝 + 暖铜 + Fraunces/Geist)

### Out of scope
- 多人用户 / 登录(本地单用户)
- 持久化到数据库(history 用 in-memory ring buffer)
- 实时推送(WebSocket 不在本 phase)
- 移动端优化(响应式做了,但不专门调优)
- 国际化(只中文 + 英文混排)
- i18n / 暗色模式切换(先用 light theme,后面再加)

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ Browser (vanilla JS SPA shell)                                    │
│  ├─ /console  → index.html (SPA shell,加载子页)                  │
│  ├─ /console/tool/forecast.html  → form + chart                   │
│  ├─ /console/tool/diagnostics.html                                │
│  ├─ ... (9 个 tool 页面)                                          │
│  ├─ /console/chat.html  → chat (reuse chat_widget)                │
│  ├─ /console/settings.html  → LLM config form                    │
│  └─ /console/history.html  → past queries list                   │
└──────────────────────────────────────────────────────────────────┘
                            ↑ JSON / SSE
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ FastAPI backend (backend/api/main.py + routes/admin.py)          │
│  ├─ GET  /api/v1/admin/tools          → 9 tool metadata          │
│  ├─ POST /api/v1/admin/tools/{name}/run  → run one tool           │
│  ├─ GET  /api/v1/admin/history        → past queries             │
│  ├─ DEL  /api/v1/admin/history        → clear                    │
│  ├─ GET  /api/v1/admin/config         → current LLM config       │
│  ├─ PUT  /api/v1/admin/config         → update LLM config       │
│  ├─ POST /api/v1/admin/chat           → non-stream chat          │
│  └─ GET  /api/v1/admin/chat/stream    → SSE stream chat          │
└──────────────────────────────────────────────────────────────────┘
                            ↑ AIConfig (mutated in place)
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│ backend/ai/* (rca SDK, chat_service, tool_executor, fallback)    │
└──────────────────────────────────────────────────────────────────┘
```

**关键决定**:
- 静态 HTML 入口(`/console/index.html`)+ 9 个独立 tool HTML 子页 — 不做 client-side router,直接用 `<iframe>` 或 fetch 加载 — **简化部署**
- 后端**直接 import** `rca` SDK(`rca.forecast()` / `rca.chat()` 等)— 单一代码路径
- `AIConfig` 是 frozen,settings update 用**新建**后 hot-swap
- `admin_store` 用**线程锁保护**的 in-memory ring buffer(简单、足够)

## 4. Component Breakdown

### 4.1 Backend (`backend/api/routes/admin.py` + `backend/api/admin_store.py`)

**`admin_store.py`** (~80 行):
- `class HistoryStore:`
  - `add(query: QueryRecord) -> None` — 加锁 → 写入 deque(maxlen=1000)
  - `list(tool: str | None, limit: int) -> list[QueryRecord]`
  - `clear() -> None`
  - `get(id: str) -> QueryRecord | None`
- `class ConfigStore:`
  - `get() -> AIConfig`
  - `update(model=None, base_url=None, ...) -> AIConfig` — 构造新 cfg + hot-swap + 写 env(base_url)
- `class QueryRecord(TypedDict):` id, ts, tool, params, result_summary, duration_ms
- 单例 `_history` / `_config` 在 module-level

**`routes/admin.py`** (~200 行):
- 8 个 endpoint(见 §3 表格)
- 全部用 Pydantic model 校验请求体
- tool run endpoint 内部 `from rca import forecast / diagnostics / ...` 然后 `func(**params)` — 单一调用路径
- chat stream endpoint 用 `rca.chat_stream()`,包装成 SSE event

**修改 `main.py`**:
- 加 `from backend.api.routes.admin import router as admin_router`
- `app.include_router(admin_router, prefix=settings.API_V1_STR)` 或直接挂 `/admin/...`
- 加 `app.mount("/console", StaticFiles(directory="frontend/console"))` 提供静态文件

### 4.2 Frontend (`frontend/console/`)

```
frontend/console/
├── index.html              # SPA shell — 顶部 nav + iframe 主区
├── tool/
│   ├── forecast.html       # 9 个 tool 独立页面
│   ├── diagnostics.html
│   ├── backtest.html
│   ├── risk.html
│   ├── scenarios.html
│   ├── monte-carlo.html
│   ├── data-provenance.html
│   ├── macro-data.html
│   └── list-cities.html
├── chat.html               # 复用现有 chat_widget
├── settings.html           # LLM config form
├── history.html            # 列表 + 复跑 + 导出
├── css/
│   └── console.css         # console 特有样式(继承 index.html 的 :root tokens)
└── js/
    ├── api.js              # fetch 封装
    ├── chart.js            # ECharts 辅助函数
    └── form-helpers.js     # autocomplete / dropdown
```

**`index.html` (SPA shell)**:
- 顶部 nav(logo + 6 个 tab: Dashboard / Tools / Chat / Settings / History / API Docs)
- 主区域 `<iframe id="main-frame">` — nav 切换加载不同子页
- 或更简单:9 个 tool 链接直接打开新页面,不嵌入 SPA(决策:不用 iframe,直接 9 个独立 page,反正静态文件,导航就是普通 `<a href>`)

**`tool/forecast.html`** (representative):
```html
<form id="forecast-form">
  <label>城市 <input name="city" list="cities" required></label>
  <datalist id="cities"><!-- JS 填充 --></datalist>
  <label>指标 <select name="indicator" required></select></label>
  <label>范围 <select name="scope"><option value="city">城市</option><option value="province">省份</option></select></label>
  <label>年数 <input type="range" name="years" min="1" max="20" value="5"></label>
  <button>Run</button>
</form>
<div id="result"><!-- ECharts 容器 --></div>
<div id="metrics"></div>
<div id="diagnostics"></div>
```

JS:
- `submit` → `POST /api/v1/admin/tools/get_forecast/run` → render ECharts line chart with CI band
- 显示 diagnostics verdict(绿/黄/红 badge)+ backtest MAPE 数字
- 错误时:`<div class="error">` 显示

**`settings.html`**:
- 9 个字段 form(model / base_url / temperature / max_tokens / max_tool_rounds / ...)
- `Load defaults` 按钮 → `GET /api/v1/admin/config` → 填表
- `Save` 按钮 → `PUT /api/v1/admin/config` → 弹出 toast
- Reset 按钮 → 重新从 env 读

**`history.html`**:
- 列表(每行:timestamp, tool 名, params 摘要, duration, 状态)
- 复跑 button → POST 同一 params,跳到对应 tool 页填好表单
- 导出 button → 下载 `history.json`
- 清空 button → `DELETE /api/v1/admin/history`,confirm 后清

**`chat.html`**:
- 直接复用现有 `chat_widget.js`(SSE 真流式)
- 新增:多 session 下拉(从 `GET /api/v1/admin/chat/sessions` 拿)
- 新增:session 历史(从 history store 拿 chat 类型)

### 4.3 Visual style

继承 `frontend/index.html` 的 design tokens:
- `--ink-900: #0E1F3F` (主色)
- `--copper-500: #D08560` (强调)
- `--copper-300: #E8BFA6` (hover)
- Font: Fraunces (标题) + Geist (正文) + JetBrains Mono (数据)
- 圆角 12-16px,卡片阴影柔和

新增 console 特有样式:
- 侧栏 nav(桌面)/ 顶 nav(移动)
- 卡片网格(Dashboard)
- ECharts 主题继承 index.html 的 `CHART_THEME`

### 4.4 ECharts charts

| Tool | Chart | Type |
|------|-------|------|
| forecast | 预测折线 + CI 区间带 | line + area |
| diagnostics | 5 指标 bar | bar |
| backtest | 实际 vs 预测 双线 + MAPE 标注 | line |
| risk | VaR/CVaR 4 卡片 + GARCH 条件波动 | bar + line |
| scenarios | 4 档情景对比 | multi-line |
| monte_carlo | P5/P50/P95 扇形带 | line + area |
| data_provenance | 数据血缘树(HTML/CSS) | (no chart) |
| macro_data | 4 指标当前值 + 同比 | 4 mini-sparkline |
| list_cities | (no chart) | 搜索列表 |

## 5. Data flow

### 5.1 Tool 调用流程

```
user 填 form → submit
   ↓
fetch POST /api/v1/admin/tools/{tool_name}/run
   body = {city: "shenzhen", indicator: "gdp", years: 5}
   ↓
backend route handler:
   1. 校验 body schema
   2. 查 _TOOL_FUNC_NAMES 表 → rca.forecast
   3. try: result = rca.forecast(scope="city", name=city, indicator=indicator, years=years)
   4. except ToolArgumentError → 400 + {error: str}
   5. record to history
   6. return 200 + {data: result["data"]}
   ↓
frontend render:
   - ECharts init
   - show metrics card
   - show diagnostics verdict badge
   - show error if any
```

### 5.2 Chat 流式流程

```
user 输入 → 触发 chat_widget.js
   ↓
fetch GET /api/v1/admin/chat/stream?session=X&message=Y
   (SSE, text/event-stream)
   ↓
backend async generator:
   for ev in rca.chat_stream(session_id=X, user_message=Y, config=current_cfg):
       yield f"data: {json.dumps(ev)}\n\n"
   ↓
frontend EventSource:
   on message: parse JSON
   if type==token: append to message div
   if type==tool_call: show "正在调 tool X" line
   if type==done: finish
   if type==error: show error
```

### 5.3 Settings 更新流程

```
GET /api/v1/admin/config → 返当前 AIConfig.to_dict()
user 改 form
PUT /api/v1/admin/config body={model: "deepseek-v3", ...}
   ↓
backend ConfigStore.update():
   - 读 base cfg(从 env 重新 load)
   - 构造 new AIConfig(其他字段保留,只改 user 改的)
   - global swap: _cfg = new_cfg
   - 设 env if base_url changed
   - return new cfg
   ↓
所有后续 rca.chat / rca.chat_stream 用新 cfg(因为 _get_cfg() 重新 load)
```

## 6. Error handling

| 场景 | 行为 |
|------|------|
| Tool 参数错(城市名不存在) | 400 + `{error: "...atlantis..."}`,前端红色 banner |
| LLM 全部失败 | 502 + `{error: "LLM unavailable: ..."}`,前端 toast |
| Chat stream 断连 | EventSource 自动重连(3 次),前端显示"重连中" |
| Settings 更新校验失败 | 400 + Pydantic 错误 detail,前端红字段 |
| History ring buffer 满 | 旧的自动 FIFO 出队(用户无感) |
| 后端 down | 前端 fetch → "无法连接,请确认后端 :8000 在跑" |

## 7. Testing

### 7.1 Backend (pytest)
- `tests/api/test_admin.py` (~20 测试)
  - 8 个 endpoint happy path
  - 8 个 endpoint 错误 path(参数错 / LLM 错 / 404)
  - History FIFO(超过 1000 自动丢)
  - Config update hot-swap(更新后立刻生效)
  - chat_stream SSE 格式正确

### 7.2 Frontend
- 不写自动化测试(vanilla JS 太琐碎)
- 用 `frontend/console/` 打开 dev server 手测 9 个 tool + chat + settings + history
- 截图留档

### 7.3 真 LLM smoke
- `tests/smoke/console_smoke.py`:
  - POST 9 个 tool 端到端
  - GET config / PUT config / GET config 验证更新
  - POST chat 一次(可能 30s)
  - GET history 看记录
  - DEL history 验证清空

## 8. Files to create

新增 22 文件,修改 3 文件:

**Backend** (3 新):
- `backend/api/admin_store.py` (~80 行)
- `backend/api/routes/admin.py` (~250 行)
- `tests/api/test_admin.py` (~400 行,20 测试)

**Backend** (1 改):
- `backend/api/main.py` — 加 `admin_router` + `static mount /console`

**Frontend** (19 新):
- `frontend/console/index.html` (60 行 — nav shell)
- `frontend/console/tool/{9 个}.html` × 9 (各 80-150 行)
- `frontend/console/chat.html` (40 行 — 包装 chat_widget)
- `frontend/console/settings.html` (80 行)
- `frontend/console/history.html` (100 行)
- `frontend/console/css/console.css` (200 行)
- `frontend/console/js/api.js` (50 行)
- `frontend/console/js/chart.js` (150 行)
- `frontend/console/js/form-helpers.js` (60 行)

**Docs** (2 新):
- `docs/CONSOLE_GUIDE.md` (300 行 — 用户指南)
- `CHANGELOG.md` + `README.md` v9.1 段

## 9. Implementation order (TDD)

按 TDD 顺序,22 个 task:

```
T1: backend/api/admin_store.py — HistoryStore + ConfigStore (含 lock)
T2: tests/api/test_admin_store.py — 5 测试(race / FIFO / config update)
T3: backend/api/routes/admin.py — 8 endpoint skeleton + tool dispatch
T4: tests/api/test_admin.py — tools 9 happy + 9 error path
T5: tests/api/test_admin.py — config GET/PUT + history GET/POST/DELETE
T6: tests/api/test_admin.py — chat non-stream + stream SSE
T7: backend/api/main.py — wire admin_router + /console static mount
T8: 真 backend smoke — 9 tool endpoint + config + history 端到端
T9: frontend/console/css/console.css — base + nav + cards + form
T10: frontend/console/js/api.js + form-helpers.js — fetch + autocomplete
T11: frontend/console/js/chart.js — ECharts 主题 + 6 个 chart helper
T12: frontend/console/index.html — SPA shell + nav
T13: frontend/console/tool/list-cities.html — 列表 tool(最简单的,先验证)
T14: frontend/console/tool/forecast.html — 完整 form + ECharts line
T15: frontend/console/tool/diagnostics.html — verdict badge + 5 指标
T16: frontend/console/tool/backtest.html — metrics 表格
T17: frontend/console/tool/risk.html — VaR/CVaR + GARCH 图
T18: frontend/console/tool/scenarios.html — 4 档对比
T19: frontend/console/tool/monte-carlo.html — fan chart
T20: frontend/console/tool/data-provenance.html — lineage tree
T21: frontend/console/tool/macro-data.html — 4 sparkline
T22: frontend/console/chat.html + settings.html + history.html
T23: docs/CONSOLE_GUIDE.md
T24: CHANGELOG 9.1.0 + README 段
T25: 真 LLM smoke 9 tool + chat + config update + history
T26: ruff + 全部测试 + push
```

**总 26 task**,预计 5000+ 行新代码(后端 700 + 前端 3500 + 测试 500 + 文档 400)。

## 10. Open questions

- **Q1: AIConfig 在 chat 期间 hot-swap 会有 race condition 吗?** — 答:不会,因为 rca.chat() 在调时读 cfg,拿到引用就保持到那次 chat 结束。下一个 chat 才看新 cfg。
- **Q2: History 多进程安全吗?** — uvicorn 单进程多 worker 默认 false(只用一个 worker),in-memory 够用。如果以后多 worker,得换 SQLite。**本 phase 不做**。
- **Q3: Chat 端是否要持久化 conversation messages 到 disk?** — 答:**不做**,in-memory only(跟 history 一样)。生产环境再加。
- **Q4: AIConfig 是 frozen,update 时 base_url 怎么处理?** — 走 env(跟 v9.0 chat 一致),不污染 cfg。
- **Q5: 如果用户改 model 后 LLM 不可用怎么办?** — 改完立刻试跑一次小测试,失败回滚 + 提示。

## 11. 风险 + 缓解

| 风险 | 缓解 |
|------|------|
| AIConfig hot-swap 引入 race | T1 用 threading.Lock 保护,ConfigStore 写时锁;读时不用锁(Python GIL 够) |
| History 在 LLM 错时仍要 record | admin_store.add() 在 route handler 末尾(无论成功失败),用 try/finally 包裹 |
| Chat SSE 在 nginx 后 buffer | FastAPI 默认不 buffer,生产部署时 nginx 配 `proxy_buffering off;` |
| 前端跨域 | 同源(API + console 同一 host:port),不需 CORS |
| 大响应阻塞 | forecast / monte_carlo 返大 dict,前端只 show 摘要 + "View raw JSON" 按钮 |
| 静态文件 cache | 设 `Cache-Control: no-cache` for HTML,`max-age=3600` for CSS/JS |

## 12. Acceptance criteria

✅ 用户能:
1. 打开 `http://localhost:8000/console/` 看 dashboard
2. 点 9 个 tool 卡片 → 进对应 form 页 → 填表 → Run → 看 ECharts 图 + 数字
3. 在 chat 页问自然语言问题,看流式响应 + tool call 中间过程
4. 在 settings 页改 model dropdown → Save → 立即生效(下次 chat 用新 model)
5. 在 history 页看最近查询、点复跑、点导出下载 JSON
6. 所有 9 tool + chat + config + history 端到端跑通(真 LLM)
7. ruff 0 错
8. 全部测试 pass(后端 20 个新测试 + 现有 77 个 = 至少 97 个)

## 13. 未来扩展(不在本 phase)

- WebSocket 推送(替代 SSE,支持反向 chat)
- 多用户 + 登录(JWT)
- 历史持久化(SQLite / Postgres)
- 工具执行调度(cron / 定时)
- 模型对比页面
- Dark mode
- i18n
