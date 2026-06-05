# v9.1 Web Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 FastAPI 后端加 8 个 admin endpoint,在 `frontend/console/` 加 19 个文件,做完整的 Web 管理界面(9 tool UI + chat + settings + history + dashboard)。

**Architecture:**
- **后端**:`backend/api/admin_store.py`(HistoryStore + ConfigStore,threading.Lock) + `backend/api/routes/admin.py`(8 endpoint) + 改 `main.py` wire 起来
- **前端**:`frontend/console/` 19 个静态文件,vanilla JS + ECharts,继承 `frontend/index.html` 的 design tokens(深墨蓝 #0E1F3F + 暖铜 #D08560 + Fraunces/Geist)
- **设计 spec**:[2026-06-05-v91-web-console-design.md](file:///workspace/docs/superpowers/specs/2026-06-05-v91-web-console-design.md)(已经 commit)

**Tech Stack:** FastAPI(已有)+ Pydantic v2(已有)+ threading.Lock(标准库)+ vanilla JS + ECharts 5.6(已有)+ CSS variables(继承)

---

## File Structure

**新增 22 文件:**

| 路径 | 行数估计 | 职责 |
|------|---------|------|
| `backend/api/admin_store.py` | 100 | HistoryStore(ring buffer 1000) + ConfigStore(hot-swap) |
| `backend/api/routes/admin.py` | 280 | 8 endpoint + 9 tool dispatch + SSE chat |
| `tests/api/test_admin.py` | 450 | 20+ 测试(8 endpoint happy/error + race + FIFO + SSE) |
| `frontend/console/index.html` | 90 | SPA shell + nav(继承 index.html tokens) |
| `frontend/console/css/console.css` | 220 | console 特有样式(继承 :root) |
| `frontend/console/js/api.js` | 60 | fetch 封装 + error 处理 |
| `frontend/console/js/chart.js` | 200 | ECharts 6 个 chart helper |
| `frontend/console/js/form-helpers.js` | 70 | city autocomplete + indicator select |
| `frontend/console/tool/{9 个}.html` × 9 | 100-150 各 | 9 tool 独立页面 |
| `frontend/console/chat.html` | 50 | 包装 chat_widget.js |
| `frontend/console/settings.html` | 100 | LLM config form |
| `frontend/console/history.html` | 130 | 列表 + 复跑 + 导出 + 清空 |
| `docs/CONSOLE_GUIDE.md` | 300 | 用户指南 |

**修改 3 文件:**
- `backend/api/main.py` — wire admin_router + `/console` static mount
- `CHANGELOG.md` — 加 9.1.0 段
- `README.md` — 加 v9.1 段

---

## 任务清单 (TDD 顺序)

### Phase A: 后端 (T1-T8)

#### Task 1: admin_store.py — HistoryStore + ConfigStore

**Files:** Create `backend/api/admin_store.py`, `tests/api/test_admin_store.py`

- [ ] **Step 1**: 写 failing test `tests/api/test_admin_store.py`(5 测试):
  - `test_history_add_and_list`
  - `test_history_fifo_eviction_at_1000`
  - `test_history_filter_by_tool`
  - `test_config_update_changes_model`
  - `test_config_update_sets_base_url_env`
- [ ] **Step 2**: 跑测试,确认 FAIL
- [ ] **Step 3**: 实现 `backend/api/admin_store.py`:
  - `class HistoryStore: __init__(maxlen=1000); _lock; add/list/clear/get`
  - `class ConfigStore: _lock; get/update`(构造新 AIConfig + hot-swap + 写 env)
  - `class QueryRecord(TypedDict)`
  - module-level `_history = HistoryStore()` / `_config = ConfigStore()`
- [ ] **Step 4**: 跑测试,PASS
- [ ] **Step 5**: `git commit -m "feat(admin): HistoryStore + ConfigStore with thread-safe hot-swap"`

#### Task 2: routes/admin.py — 8 endpoint skeleton + tool dispatch

**Files:** Create `backend/api/routes/admin.py`

- [ ] **Step 1**: 写 9 个 tool run failing test(每个 tool 1 个 happy + 1 个 error)
- [ ] **Step 2**: 实现:
  - `GET /admin/tools` — list 9 tool metadata(name / description / params)
  - `POST /admin/tools/{name}/run` — dispatch to rca.<func>
  - `GET /admin/history?tool=&limit=` — list
  - `DELETE /admin/history` — clear
  - `GET /admin/config` — get
  - `PUT /admin/config` — update
  - `POST /admin/chat` — non-stream chat
  - `GET /admin/chat/stream?session=&message=` — SSE
- [ ] **Step 3**: 9 个 tool test PASS
- [ ] **Step 4**: `git commit -m "feat(admin): 9 tool dispatch + 8 endpoint"`

#### Task 3: tests/api/test_admin.py — config + history + chat

**Files:** Modify `tests/api/test_admin.py`

- [ ] **Step 1**: 写 config GET/PUT 3 测试
- [ ] **Step 2**: 写 history GET/POST/DELETE 4 测试
- [ ] **Step 3**: 写 chat non-stream + SSE stream 3 测试
- [ ] **Step 4**: 跑 20 测试全 PASS
- [ ] **Step 5**: `git commit -m "test(admin): config + history + chat endpoint coverage"`

#### Task 4: backend/api/main.py — wire admin_router + /console static mount

**Files:** Modify `backend/api/main.py`

- [ ] **Step 1**: 加 `from backend.api.routes.admin import router as admin_router`
- [ ] **Step 2**: `app.include_router(admin_router, prefix="/api/v1")`
- [ ] **Step 3**: `app.mount("/console", StaticFiles(directory="frontend/console", html=True), name="console")`
- [ ] **Step 4**: 跑 `uvicorn backend.api.main:app --port 8000` 起服务,curl 验证 `/console/` 和 `/api/v1/admin/tools`
- [ ] **Step 5**: `git commit -m "feat(api): wire admin_router + /console static mount"`

#### Task 5: 真 backend smoke

**Files:** Create `tests/smoke/console_backend_smoke.py`

- [ ] **Step 1**: 写 smoke: 起 uvicorn 进程 → 9 tool POST → config GET/PUT → history GET/DEL → chat 一次
- [ ] **Step 2**: 跑 smoke,9 tool 全 pass + config + history + chat 端到端过
- [ ] **Step 3**: `git commit -m "test(smoke): console backend 9 tool + config + history + chat"`(smoke 不入库)

### Phase B: 前端基础 (T6-T9)

#### Task 6: css/console.css — base + nav + cards + form + chart 容器

**Files:** Create `frontend/console/css/console.css`

- [ ] **Step 1**: 写 nav(桌面 240px 侧栏 + 移动顶栏)+ card 网格 + form 样式 + ECharts 容器
- [ ] **Step 2**: 继承 index.html 的 :root tokens(直接 copy 几个 --ink / --copper / 字体)
- [ ] **Step 3**: 浏览器手测(开发阶段不写自动化)
- [ ] **Step 4**: `git commit -m "feat(console): base CSS (nav + card + form + chart container)"`

#### Task 7: js/api.js + form-helpers.js

**Files:** Create `frontend/console/js/api.js` + `form-helpers.js`

- [ ] **Step 1**: `api.js`: `rcaFetch(path, opts)` → 统一 fetch + 错误处理 + JSON 解析
- [ ] **Step 2**: `form-helpers.js`: `populateCityList()` + `populateIndicatorSelect(scope)` + `populateBackendSelect()`
- [ ] **Step 3**: 手测 console 打开后 fetch /api/v1/admin/tools 返 9 个
- [ ] **Step 4**: `git commit -m "feat(console): api + form-helpers (fetch + autocomplete)"`

#### Task 8: js/chart.js — ECharts 主题 + 6 个 chart helper

**Files:** Create `frontend/console/js/chart.js`

- [ ] **Step 1**: 6 个 helper:
  - `renderForecastChart(div, result)` — 折线 + CI 区间
  - `renderBacktestChart(div, result)` — 实际 vs 预测双线
  - `renderRiskChart(div, result)` — VaR/CVaR 4 bar + GARCH line
  - `renderScenariosChart(div, result)` — 4 档折线
  - `renderMonteCarloChart(div, result)` — P5/P50/P95 fan
  - `renderDiagnosticsChart(div, result)` — 5 指标 bar
- [ ] **Step 2**: 主题继承(用 `--copper-500` / `--ink-900` 作为色板)
- [ ] **Step 3**: 手测 6 个 chart 都能正常 init
- [ ] **Step 4**: `git commit -m "feat(console): 6 ECharts chart helpers"`

#### Task 9: index.html — SPA shell + nav

**Files:** Create `frontend/console/index.html`

- [ ] **Step 1**: 顶部 logo + 6 个 nav link(Dashboard / Tools / Chat / Settings / History / API)
- [ ] **Step 2**: Tools 下拉 9 个 tool 链接
- [ ] **Step 3**: 引入 console.css + api.js
- [ ] **Step 4**: 手测打开 `/console/` 看到 nav
- [ ] **Step 5**: `git commit -m "feat(console): SPA shell with nav"`

### Phase C: 9 tool 页面 (T10-T18)

每个 task 是:写 tool 页面 → form → 调 api.js → 调 chart.js → 手测

#### Task 10: list-cities.html(最简单,先做验证管线)
- [ ] form: 留空
- [ ] submit → POST get_list_cities → 渲染搜索列表
- [ ] `git commit`

#### Task 11: forecast.html
- [ ] form: city / scope / indicator / years
- [ ] submit → render ECharts forecast chart + diagnostics verdict badge + backtest MAPE
- [ ] `git commit`

#### Task 12: diagnostics.html
- [ ] form: city / scope / indicator
- [ ] submit → render 5 指标 bar + verdict badge
- [ ] `git commit`

#### Task 13: backtest.html
- [ ] form: city / scope / indicator
- [ ] submit → render 实际 vs 预测 + 5 指标卡
- [ ] `git commit`

#### Task 14: risk.html
- [ ] form: city / scope / indicator
- [ ] submit → render VaR/CVaR 4 bar + GARCH line
- [ ] `git commit`

#### Task 15: scenarios.html
- [ ] form: city / scope / indicator
- [ ] submit → render 4 档折线对比
- [ ] `git commit`

#### Task 16: monte-carlo.html
- [ ] form: city / scope / indicator / years
- [ ] submit → render P5/P50/P95 fan chart
- [ ] `git commit`

#### Task 17: data-provenance.html
- [ ] form: city / province
- [ ] submit → 渲染数据血缘 tree(HTML/CSS 嵌套 ul)
- [ ] `git commit`

#### Task 18: macro-data.html
- [ ] form: 无
- [ ] submit → 4 协变量当前值 + 同比 + sparkline
- [ ] `git commit`

### Phase D: chat + settings + history (T19-T21)

#### Task 19: chat.html
- [ ] 复用 chat_widget.js(浮动 bubble 不行,要全屏)
- [ ] 加 session 下拉(新 / 续)
- [ ] 改 fetch URL 为 /api/v1/admin/chat/stream
- [ ] `git commit`

#### Task 20: settings.html
- [ ] form: model(下拉) / base_url / temperature / max_tokens / max_tool_rounds / ...
- [ ] Load defaults → GET config
- [ ] Save → PUT config
- [ ] Reset → 重新从 env 读
- [ ] `git commit`

#### Task 21: history.html
- [ ] table: timestamp / tool / params 摘要 / duration / status
- [ ] 复跑 → POST 跳到对应 tool 页填表
- [ ] 导出 → 下载 history.json
- [ ] 清空 → DELETE 确认
- [ ] `git commit`

### Phase E: 文档 + 收尾 (T22-T26)

#### Task 22: docs/CONSOLE_GUIDE.md
- [ ] 用户指南:启动 / 9 tool 用法 / chat / settings / history / FAQ
- [ ] `git commit`

#### Task 23: CHANGELOG 9.1.0 + README v9.1 段
- [ ] `git commit`

#### Task 24: 真 LLM smoke 端到端
- [ ] 起 uvicorn → 浏览器 headless 测 9 tool POST + chat + config update + history(用 requests 库,不真开浏览器)
- [ ] 全 pass

#### Task 25: ruff + 全部测试
- [ ] ruff check 0 错
- [ ] pytest 全 pass

#### Task 26: push
- [ ] git push origin main

---

## 进度跟踪

- [ ] T1-T5: 后端(5 task)
- [ ] T6-T9: 前端基础(4 task)
- [ ] T10-T18: 9 tool 页(9 task)
- [ ] T19-T21: chat + settings + history(3 task)
- [ ] T22-T26: 文档 + 收尾(5 task)
- **26 task 全部完成**

---

## Self-Review Checklist

- [x] Spec coverage: 9 tool UI ✅ + chat ✅ + settings ✅ + history ✅ + dashboard ✅ + 8 endpoint ✅
- [x] Placeholder scan: 无 TBD / TODO
- [x] Type consistency: `_history` / `_config` 命名一致,`QueryRecord` 字段在 store 和 route 一致
- [x] File paths 完整
- [x] TDD 顺序:store → routes → wire → smoke → 前端基础 → 9 tool → chat/settings/history → 文档

---

## 风险(从 spec §11 继承)

| 风险 | plan 应对 |
|------|-----------|
| AIConfig hot-swap race | T1 store 用 `threading.Lock` |
| History FIFO | T1 测试覆盖 1000 上限 |
| Chat SSE 断连 | T19 用 EventSource auto-reconnect |
| 静态文件 cache | T9 `Cache-Control: no-cache` for HTML |
| 大响应阻塞 | T10-T18 只 show 摘要 + "View raw JSON" |

---

## 执行选项

按用户最近指示"开始全面制作 ... 不偷工减料",**采用 Inline Execution** — 在当前 session 直接 TDD 实施,不在 fresh subagent 跳来跳去(本 sandbox 已知 subagent skill 不稳)。
