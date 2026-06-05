# v9.0 Python SDK + CLI — 设计文档

> 日期: 2026-06-05
> 状态: 待批准
> 范围: Phase 1(4 子系统之首)— Python SDK + CLI;Web 管理界面 + GitHub Pages 留作 Phase 2/3

## 1. 背景

现有 national_stats 项目已有 9 个 tool(`backend/ai/tool_executor.py`)+ 完整 LLM agent(`backend/ai/chat_service.py`),
但 **用户只能在 Web UI 通过 chat widget 间接使用**。需求:

- **CLI** — 让开发者 / 分析师在终端直接调 9 个 tool 和 LLM agent
- **Python SDK** — 让代码 / notebook / 集成测试直接 `import` 调用
- **后续 Phase 2/3**:Web 管理界面 + GitHub Pages 展示站

## 2. 设计目标

- **简单** — 用户 `pip install -e .` 后能立即 `rca forecast --city shenzhen`
- **完整** — 9 个 tool 全部覆盖 + LLM agent (sync + stream)
- **可读** — 人类默认输出 rich table,脚本可加 `--format json` / `--format plain`
- **无新依赖** — typer 0.12.3 + click 8.1.7 已在 requirements-lock.txt

## 3. 架构

```
national_stats/
├── backend/                # 现有(不变)
│   ├── ai/
│   │   ├── tool_executor.py    # 9 tool dispatcher(SDK 直接复用)
│   │   ├── chat_service.py     # chat / chat_stream(SDK 直接复用)
│   │   └── config.py           # AIConfig
│   └── core/                   # forecast_engine / risk_engine(不变)
│
├── rca/                    # 新建 — Python SDK(主包一部分)
│   ├── __init__.py             # 暴露 RCAClient / 9 个 tool wrapper
│   ├── client.py               # RCAClient 主类
│   ├── tools.py                # 9 个 sync tool 函数(直接调 tool_executor)
│   ├── chat.py                 # chat() / chat_stream() 包装
│   ├── errors.py               # RCAError / ToolNotFound / ConfigError
│   └── _config.py              # SDK 内部 AIConfig 工厂
│
├── cli/                    # 新建 — Typer CLI
│   ├── __init__.py
│   ├── main.py                 # `rca` 入口,9 子命令 + chat / chat-stream
│   ├── formatters.py           # rich / json / plain 三种输出
│   └── _resolve.py             # CLI → SDK 调用桥
│
├── tests/
│   ├── rca/                    # SDK 单测
│   │   ├── test_tools.py
│   │   ├── test_chat.py
│   │   └── test_client.py
│   └── cli/
│       ├── test_main.py        # invoke CliRunner
│       └── test_formatters.py
│
├── pyproject.toml           # 加 rca CLI entry point: rca = cli.main:app
└── docs/
    └── SDK_CLI_GUIDE.md        # 用户使用文档
```

**设计原则**:
- **SDK 不重写 tool_executor** — 直接 import 复用,只是把 `dict in, dict out` 包装成 `**kwargs in, dataclass out` 友好 API
- **CLI 不重写 SDK** — 走 SDK,不直接调 backend
- **错误统一** — `rca.errors.RCAError` 顶层,SDK 抛 RCAError,CLI 转 exit code 1

## 4. SDK API 设计

### 4.1 主类 RCAClient

```python
from rca import RCAClient
client = RCAClient()  # 默认从 env 读 LLM_OPENAI_API_KEY 等

# 9 个 tool 全部暴露
client.forecast(scope="city", name="shenzhen", indicator="gdp", years=3)
client.diagnostics(scope="city", name="shanghai", indicator="gdp")
client.backtest(scope="city", name="beijing", indicator="gdp")
client.risk(scope="city", name="guangzhou", indicator="gdp")
client.scenarios(scope="city", name="shenzhen", indicator="gdp")
client.monte_carlo(scope="city", name="hangzhou", indicator="gdp")
client.data_provenance(name="shenzhen")
client.macro_data()
client.list_cities()

# LLM agent
client.chat(session_id="user-1", user_message="深圳 GDP 2026 多少?")
# → 返 {"content": "...", "tool_rounds": 1, "tool_calls": [...]}

for ev in client.chat_stream(session_id="user-1", user_message="..."):
    # ev 可能是 {"type":"thinking"} / {"type":"tool_call",...} / {"type":"token",...} / {"type":"done",...}
    if ev["type"] == "token":
        print(ev["content"], end="")
```

### 4.2 直接 tool 调用(无 client)

```python
from rca import forecast, list_cities, macro_data

# 模块级函数 — 适合 notebook
result = forecast(scope="city", name="shenzhen", indicator="gdp", years=3)
print(result["ensemble"]["predictions"])  # [40344.36, 42273.63, 44202.90]
```

### 4.3 配置覆盖

```python
from rca import RCAClient, AIConfig

# 自定义 LLM (用 deepseek 不用 qwen)
cfg = AIConfig(
    default_backend="openai", active_backend="openai", model="deepseek-v3",
    temperature=0.3, max_tokens=2000, timeout_sec=60, max_tool_rounds=5,
    available_backends=["openai"],
)
client = RCAClient(config=cfg)
```

### 4.4 返回类型

- **9 tool 函数** → 返 `dict` (与现有 tool_executor 输出 100% 一致,无包装)
- **chat()** → 返 `dict` (与现有 chat_service.chat 一致)
- **chat_stream()** → `Iterator[dict]` (与 chat_stream_with_trace 一致)

设计取舍:不强加 dataclass 包装(避免破坏现有 76+ 个后端测试);用户需要时自己 `dataclasses.replace` 即可。

## 5. CLI 设计

### 5.1 命令树

```
rca --help
├── forecast       # 9 tool 各一个子命令
├── diagnostics
├── backtest
├── risk
├── scenarios
├── monte-carlo
├── data-provenance
├── macro-data
├── list-cities
├── chat           # 单轮 LLM
└── chat-stream    # 流式 LLM(默认 rich,带 spinner)
```

### 5.2 用法示例

```bash
# Tool 命令(直调)
$ rca forecast --city shenzhen --indicator gdp --years 3
┌─────────────────────────────────────────────────────────────┐
│ Shenzhen GDP Forecast (3y)                                  │
├─────────────────────────────────────────────────────────────┤
│ Year   │ Prediction (亿元) │ 95% CI                          │
├────────┼───────────────────┼────────────────────────────────┤
│ 2024   │ 40344.36          │ [39010.57, 41678.14]           │
│ 2025   │ 42273.63          │ [40591.51, 43955.75]           │
│ 2026   │ 44202.90          │ [42240.15, 46165.65]           │
└────────┴───────────────────┴────────────────────────────────┘
Diagnostics: WARN  Backtest MAPE: 2.35%  Data points: 16

# JSON 输出(脚本用)
$ rca forecast --city shenzhen --indicator gdp --years 3 --format json
{"scope": "city", "name": "深圳", "indicator": "gdp", "ensemble": {...}}

# 纯文本(管道)
$ rca forecast --city shenzhen --indicator gdp --years 3 --format plain
2024	40344.36
2025	42273.63
2026	44202.90

# list_cities
$ rca list-cities
支持 10 城市: 深圳, 上海, 北京, 广州, 武汉, 成都, 杭州, 南京, 苏州, 西安
支持 10 省份: 广东, 江苏, 浙江, 四川, 湖北, 陕西, 山东, 河南, 福建, 安徽

# chat
$ rca chat --message "深圳 GDP 2026 多少?"
[thinking]...
[tool_call] get_forecast(scope=city, name=shenzhen, indicator=gdp, years=1)
[done] rounds=1
深圳2026年GDP预测为44202.90亿元...

# chat-stream(带颜色 token 增量)
$ rca chat-stream --message "上海 GDP 风险"
[thinking]...
[tool_call] get_risk(scope=city, name=shanghai, indicator=gdp)
上海 GDP 在 2025 年的风险评估如下: ...

# 错误展示
$ rca forecast --city atlantis --indicator gdp
ERROR: No data for city=atlantis indicator=gdp
(exit 1)
```

### 5.3 全局 flag

```bash
rca --format {rich,json,plain}  forecast ...   # 默认 rich
rca --model deepseek-v3          chat ...       # 覆盖 LLM 模型
rca --base-url https://...       forecast ...   # 覆盖 LLM gateway
rca --no-color                   list-cities    # 禁 rich 颜色
```

### 5.4 退出码

| 情况 | Exit code |
|------|-----------|
| 成功 | 0 |
| Tool 内部错误(`{"error": "..."}`) | 1 |
| 参数错误(typer 自带) | 2 |
| LLM 不可用(fallback 链全失败) | 3 |
| KeyboardInterrupt | 130 |

## 6. 错误处理

```python
# rca/errors.py
class RCAError(Exception): """SDK 顶层错误"""
class ToolNotFoundError(RCAError): """tool 名错"""
class ToolArgumentError(RCAError): """tool 参数错"""
class LLMUnavailableError(RCAError): """LLM fallback 链全失败"""
class ConfigError(RCAError): """SDK config 错(无 API key 等)"""
```

- **SDK 内部**:`tool_executor` 返 `{"error": ...}` 时,SDK 抛 `ToolArgumentError`,保留原 message
- **SDK 外部调用**:`RCAError` 可捕获
- **CLI**:`RCAError` → exit 1(LLM 错 → 3);`ToolArgumentError` → 打印 message + 1

## 7. 测试

- **SDK 单测** 13 个(`tests/rca/`):
  - 9 个 tool 各 1 个(verify dict 返与 tool_executor 一致)
  - `test_chat` mock llm_client(verify 调用 chat_service.chat)
  - `test_chat_stream` mock generator(verify stream event 流)
  - `test_client_with_custom_config` 覆盖 AIConfig 路径
  - `test_errors_propagate` 验证 ToolArgumentError 包装
- **CLI 单测** 8 个(`tests/cli/`):
  - `test_forecast_rich_output` CliRunner 跑 + assert "深圳" in output
  - `test_forecast_json_output` `--format json` 返合法 JSON
  - `test_forecast_plain_output` `--format plain` 返纯文本
  - `test_chat_message` `--message` 调 chat 一次
  - `test_chat_stream_message` stream 输出含 "tool_call"
  - `test_list_cities_default`
  - `test_error_exit_code_1` ToolArgumentError
  - `test_help_text` `--help` 不 crash

**总**: v9.0 +21 测试(76 v7.1 + 37 v8.0 + 21 v9.0 = **134**)。

## 8. 范围外(留 Phase 2/3)

- **Web 管理界面** — 在 chat_widget 上加 tool 调用历史/管理面板(后续 spec)
- **GitHub Pages 展示站** — `docs/index.html` 改成交互式 demo(后续 spec)
- **async SDK** — 暂不实现,FastAPI 是 sync 路径,sync 够用
- **CLI 配置持久化** — 暂不实现,只用 env / `--model` flag

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| Typer / rich 在 Windows console 渲染异常 | `--no-color` / `--format plain` 兜底;CI 跑 plain |
| Tool 返回大数据(risk 1000 iter MC)撑爆 rich | rich 自动 truncate;`--format json` 全量 |
| LLM chat_stream 慢 → 用户等 | typer 进度 spinner + Ctrl-C 友好 |
| SDK 包装破坏现有 76 测试 | 100% 走原 `tool_executor` / `chat_service`,不加新字段 |

## 10. 文件清单(预计)

- 新建:`rca/__init__.py` `rca/client.py` `rca/tools.py` `rca/chat.py` `rca/errors.py` `rca/_config.py` (6)
- 新建:`cli/__init__.py` `cli/main.py` `cli/formatters.py` `cli/_resolve.py` (4)
- 新建:`tests/rca/test_tools.py` `tests/rca/test_chat.py` `tests/rca/test_client.py` (3)
- 新建:`tests/cli/test_main.py` `tests/cli/test_formatters.py` (2)
- 新建:`docs/SDK_CLI_GUIDE.md` (1)
- 修改:`pyproject.toml`(加 entry point + rca cli 包) (1)
- **共 17 文件,~600 行代码 + ~200 行测试**

## 11. 验收标准

1. `pip install -e .` 后 `rca --help` 跑出所有 11 个子命令
2. `rca list-cities` 输出 10 城市 + 10 省份
3. `rca forecast --city shenzhen --indicator gdp --years 3` 输出 3 行预测表
4. `rca forecast ... --format json | jq .` 返合法 JSON
5. `rca chat --message "..."` 至少调 1 次 tool(在有 LLM key 时)
6. 113 + 21 = **134 测试全 pass**
7. `ruff check rca/ cli/ tests/rca/ tests/cli/` 全 clean
