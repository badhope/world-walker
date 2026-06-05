# Regional Economic Analysis Agent — Python SDK & CLI Guide (v9.1)

> **Status**: stable · v9.1.0
> **Audience**: 数据科学家、量化分析师、MLOps、需要把区域经济分析能力嵌入应用/管道的开发者

RCA Agent 是一套可调用的区域经济分析工具集 + LLM agent。v9.0 起,你有两个互操作的入口:

1. **Python SDK** (`rca` 包)— 在 notebook / 脚本 / Web app 里 `import rca` 直接用
2. **CLI** (`rca` 命令) — 终端一行跑任意工具,支持 `rich` / `json` / `plain` 三种输出

本指南覆盖:**安装** · **SDK API** · **CLI 用法** · **错误处理** · **退出码** · **何时用哪个**。

---

## 1. 安装

### 1.1 从源码(推荐开发者)

```bash
git clone https://github.com/<your-org>/Regional-Economic-Analysis.git
cd Regional-Economic-Analysis
pip install -e .              # 安装 rca 包 + CLI entry point
```

`pip install -e .` 会:
- 装好 `rca` 这个 Python 包
- 注册 `rca` 这个 CLI(等价于 `python -m cli.main`)
- 装好所有 Python 依赖(forecast / risk / scenarios / monte-carlo 全部就跑得起来)

### 1.2 验证安装

```bash
# CLI 版本
rca --help
# → Usage: rca [OPTIONS] COMMAND [ARGS]...
# → Regional Economic Analysis agent — CLI for 9 tools + LLM chat.

# SDK 版本
python -c "import rca; print(rca.__version__)"
# → 9.1.0
```

### 1.3 LLM API Key(可选,但要 chat 必须)

```bash
export LLM_OPENAI_API_KEY="sk-..."
export LLM_OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"  # Qwen / DeepSeek / Kimi 等 OpenAI 兼容 gateway
export LLM_DEFAULT_BACKEND="openai"
```

- 跑 9 个 **tool** 不需要 LLM key(纯本地计算)
- 跑 `rca chat` / `rca chat-stream` / `rca.chat()` / `rca.chat_stream()` 必须配 LLM

> 9 个 tool 完全本地 — 0 网络、0 LLM 费用、可在 air-gap 环境跑。

---

## 2. Python SDK

### 2.1 概览

```python
import rca
rca.__version__  # '9.1.0'
```

顶层 API:

| 名称 | 类型 | 说明 |
|------|------|------|
| `RCAClient` | class | OO 入口,适合长生命周期 app |
| `chat(session_id, user_message)` | function | 单轮 LLM agent → 调 tool → 返答案 |
| `chat_stream(session_id, user_message)` | function | 流式 LLM agent,逐 token / event |
| `forecast(scope, name, indicator, years=5)` | function | 多年预测(ensemble + CI + diagnostics 摘要) |
| `diagnostics(scope, name, indicator)` | function | 5 项残差诊断(ADF/KPSS/Ljung-Box/Jarque-Bera/Breusch-Pagan) + verdict |
| `backtest(scope, name, indicator)` | function | walk-forward CV 5 指标(MAPE/RMSE/MASE/sMAPE/Coverage) |
| `risk(scope, name, indicator)` | function | VaR/CVaR 95/99 + GARCH(1,1) 条件波动率 |
| `scenarios(scope, name, indicator, years=5)` | function | 4 档情景:baseline/+10%/-10%/-25% |
| `monte_carlo(scope, name, indicator, years=5)` | function | 1000 次模拟分位数(P5/P50/P95) |
| `data_provenance(name)` | function | 数据来源信息(URL/置信度/估算标记) |
| `macro_data()` | function | 4 宏观协变量当前值 + 同比 |
| `list_cities()` | function | 系统支持的所有城市和省份 |
| `RCAError` | exception | 所有 RCA 异常的基类 |
| `ToolNotFoundError` | exception | tool 名不在 registry |
| `ToolArgumentError` | exception | tool 收到不合法参数 / 内部错 |
| `LLMUnavailableError` | exception | fallback chain 全部失败 |

### 2.2 两种用法

#### A) 模块级函数(简洁)

```python
import rca

# 列出支持的城市
cities = rca.list_cities()
print(cities["data"]["n_cities"])  # 10

# 预测深圳 GDP 未来 3 年
fc = rca.forecast(scope="city", name="shenzhen", indicator="gdp", years=3)
for i, pred in enumerate(fc["data"]["ensemble"]["predictions"]):
    year = 2024 + i
    print(f"{year}: {pred:,.2f}")

# 跑 walk-forward CV 看精度
bt = rca.backtest(scope="city", name="shenzhen", indicator="gdp")
print(f"MAPE: {bt['data']['metrics']['mape']:.2f}%")
```

#### B) RCAClient(OO,适合长生命周期)

```python
from rca import RCAClient

client = RCAClient()  # 默认 load_config() — 从 env 读

# 调 tool
cities = client.list_cities()
fc = client.forecast(scope="city", name="shenzhen", indicator="gdp", years=3)

# 跑 chat(LLM agent)
result = client.chat(session_id="user-42", user_message="深圳 2026 GDP 多少?")
print(result["content"])
print(f"调了 {result.get('tool_rounds', 0)} 轮 tool")

# 注入自定义 config
from backend.ai.config import AIConfig
custom_cfg = AIConfig(..., fallback_chain=("qwen-long",))
client = RCAClient(config=custom_cfg)
```

`RCAClient` 和模块级函数完全等价 — 内部都委托给 `rca.tools.*` 和 `rca.chat.*`,只是入口风格不同。

### 2.3 9 个 tool wrapper 的参数

| Tool | 函数签名 | 必填 | 选填 |
|------|---------|------|------|
| `forecast` | `(scope, name, indicator, years=5)` | scope / name / indicator | years |
| `diagnostics` | `(scope, name, indicator)` | 同上 | — |
| `backtest` | `(scope, name, indicator)` | 同上 | — |
| `risk` | `(scope, name, indicator)` | 同上 | — |
| `scenarios` | `(scope, name, indicator, years=5)` | 同上 | years |
| `monte_carlo` | `(scope, name, indicator, years=5)` | 同上 | years |
| `data_provenance` | `(name)` | name | — |
| `macro_data` | `()` | — | — |
| `list_cities` | `()` | — | — |

**`scope`** 必须是 `"city"` 或 `"province"`。
**`name`** 城市用拼音小写(`shenzhen` / `beijing`)、省份用英文小写(`guangdong`)。
**`indicator`** 必须是 `list_cities()` 返回的某个指标(常见 `gdp` / `population` / `fdi` / `cpi` 等)。

### 2.4 chat / chat_stream

```python
import rca

# 单轮
result = rca.chat(session_id="abc", user_message="深圳 GDP 走势如何?")
# → {"content": "...", "tool_rounds": 2, "tool_calls": [...], "trace": [...]}

# 流式
for ev in rca.chat_stream(session_id="abc", user_message="深圳 2025 风险?"):
    if ev["type"] == "thinking":
        print("[thinking]...")
    elif ev["type"] == "tool_call":
        print(f"[tool_call] {ev['name']}({ev['args']})")
    elif ev["type"] == "token":
        print(ev["content"], end="", flush=True)
    elif ev["type"] == "done":
        print(f"\n[done rounds={ev['tool_rounds']}]")
    elif ev["type"] == "error":
        print(f"[error] {ev['message']}")
```

`session_id` 用于保留多轮上下文。同一个 `session_id` 内,agent 能记住前几轮的 tool 结果。

### 2.5 错误处理

```python
from rca import (
    RCAError,            # 基类
    ToolNotFoundError,   # tool 名错
    ToolArgumentError,   # tool 参数错或内部计算错
    LLMUnavailableError, # LLM 全部 fallback 失败
)

try:
    fc = rca.forecast(scope="city", name="atlantis", indicator="gdp")
except ToolArgumentError as e:
    print(f"参数问题: {e}")
except LLMUnavailableError as e:
    print(f"LLM 不可用: {e}")
except RCAError as e:
    print(f"RCA 错: {e}")
```

`LLMUnavailableError` 只在 `chat` / `chat_stream` 时抛(因为 9 tool 完全本地)。Tool 调用只可能抛 `ToolNotFoundError` / `ToolArgumentError`。

### 2.6 完整示例:在 notebook 里跑 ensemble + 风险分析

```python
import rca
import json

# 1. 找支持的城市
cities = rca.list_cities()["data"]
print("支持城市:", cities["cities_pinyin"])
print("支持省份:", cities["provinces"])

# 2. 跑 ensemble forecast
fc = rca.forecast(scope="city", name="shenzhen", indicator="gdp", years=5)["data"]
ens = fc["ensemble"]
print(f"\n深圳 GDP 5 年预测 (ensemble):")
for i, p in enumerate(ens["predictions"]):
    print(f"  {2024+i}: {p:,.0f}  CI=[{ens['ci_lower'][i]:,.0f}, {ens['ci_upper'][i]:,.0f}]")

# 3. 看 diagnostics
diag = rca.diagnostics(scope="city", name="shenzhen", indicator="gdp")["data"]
print(f"\n诊断 verdict: {diag['verdict']}  ({diag['n']} 个数据点)")

# 4. 看 backtest
bt = rca.backtest(scope="city", name="shenzhen", indicator="gdp")["data"]
m = bt["metrics"]
print(f"\n精度: MAPE={m['mape']:.2f}%  RMSE={m['rmse']:.0f}  Coverage={m['coverage']:.0%}")

# 5. 风险
risk = rca.risk(scope="city", name="shenzhen", indicator="gdp")["data"]
print(f"\n风险: VaR 95%={risk['var_95']['var_pct']:.2f}%  CVaR 95%={risk['cvar_95']['cvar_pct']:.2f}%")

# 6. 情景
sc = rca.scenarios(scope="city", name="shenzhen", indicator="gdp")["data"]
for name, payload in sc["scenarios"].items():
    print(f"  {name}: 终值 {payload['final_value']:,.0f}")

# 7. Monte Carlo
mc = rca.monte_carlo(scope="city", name="shenzhen", indicator="gdp", years=5)["data"]
print(f"\nMonte Carlo (n={mc['n_sims']}):")
print(f"  P5  = {mc['percentiles']['p5'][-1]:,.0f}")
print(f"  P50 = {mc['percentiles']['p50'][-1]:,.0f}")
print(f"  P95 = {mc['percentiles']['p95'][-1]:,.0f}")
```

---

## 3. CLI

### 3.1 三种调用方式

```bash
# 1. entry point(装好后)
rca <command> [options]

# 2. python -m
python -m cli.main <command> [options]

# 3. 直接跑(开发)
PYTHONPATH=/workspace python /workspace/cli/main.py <command> [options]
```

### 3.2 Global flags(必须在子命令前)

```bash
rca --format {rich,json,plain}     # 默认 rich
   --model <name>                  # 覆盖 LLM 模型(如 deepseek-v3)
   --base-url <url>                # 覆盖 LLM gateway
   --no-color                      # 关 rich 颜色
   <command> [args]
```

> **typer 限制**: global flag 必须在 subcommand 前。`rca list-cities --format json` 会报"no such option"。正确写法是 `rca --format json list-cities`。

### 3.3 11 个子命令

```bash
# ===== 9 tool 子命令 =====

# 1. forecast — 多年预测
rca --format rich forecast --city shenzhen --indicator gdp --years 5
rca --format json forecast --city shenzhen --indicator gdp --years 3

# 2. diagnostics — 5 项残差诊断
rca diagnostics --city shanghai --indicator gdp

# 3. backtest — walk-forward CV
rca backtest --city shenzhen --indicator gdp

# 4. risk — VaR / CVaR / GARCH
rca risk --city guangzhou --indicator gdp

# 5. scenarios — 4 档情景
rca scenarios --city shenzhen --indicator gdp

# 6. monte-carlo — 1000 次模拟
rca monte-carlo --city hangzhou --indicator gdp --years 5

# 7. data-provenance — 数据来源
rca data-provenance --city shenzhen

# 8. macro-data — 4 宏观协变量
rca macro-data

# 9. list-cities — 支持的城市/省份
rca list-cities

# ===== 2 chat 子命令 =====

# 10. chat — 单轮 LLM agent
rca chat --message "深圳 GDP 2026 多少?" --session user-1

# 11. chat-stream — 流式 LLM agent
rca chat-stream --message "上海 2025 风险?" --session user-1
```

### 3.4 三种输出格式

#### rich(默认,人类可读)

```
                       深圳 GDP Forecast (5y)
┌──────┬─────────────────┬────────────────────────┐
│ Year │ Prediction      │ 95% CI                 │
├──────┼─────────────────┼────────────────────────┤
│ 2024 │       40,344.36 │ [39,010.57, 41,678.14] │
│ 2025 │       42,273.63 │ [40,591.51, 43,955.75] │
│ 2026 │       44,202.90 │ [42,240.15, 46,165.65] │
└──────┴─────────────────┴────────────────────────┘
Diagnostics: WARN
Backtest MAPE: 2.35%
Data points: 16
```

有专门 table 渲染的命令:`forecast` / `list-cities` / `risk` / `data-provenance` / `macro-data`。其他命令(backtest / scenarios / monte-carlo / diagnostics)走 generic key-value table。

#### json(机器可读)

```bash
$ rca --format json forecast --city shenzhen --indicator gdp --years 3
{
  "scope": "city",
  "name": "深圳",
  "indicator": "gdp",
  "ensemble": {
    "predictions": [40344.36, 42273.63, 44202.90],
    "ci_lower": [39010.57, 40591.51, 42240.15],
    "ci_upper": [41678.14, 43955.75, 46165.65]
  },
  "diagnostics_verdict": "WARN",
  "backtest_mape": 2.35,
  "data_points": 16
}
```

直接 `jq` 拿字段:

```bash
rca --format json forecast --city shenzhen --indicator gdp --years 3 \
  | jq '.ensemble.predictions[0]'
# 40344.36
```

#### plain(脚本友好 key=value)

```bash
$ rca --format plain forecast --city shenzhen --indicator gdp --years 3
scope=city
name=深圳
indicator=gdp
ensemble.predictions=[40344.36, 42273.63, 44202.90]
ensemble.ci_lower=[39010.57, 40591.51, 42240.15]
ensemble.ci_upper=[41678.14, 43955.75, 46165.65]
diagnostics_verdict=WARN
backtest_mape=2.35
data_points=16
```

适合在 shell 脚本里 `source` 或 `eval`。

### 3.5 退出码

| Exit | 含义 | 触发 |
|------|------|------|
| 0 | 成功 | tool / chat 正常完成 |
| 1 | 业务错 | `ToolArgumentError` / `ToolNotFoundError` / `RCAError` |
| 2 | CLI 用法错 | typer 拒绝的 flag / 缺必填 |
| 3 | LLM 不可用 | fallback chain 全部失败 |

shell 脚本里检查:

```bash
if rca --format json forecast --city shenzhen --indicator gdp > /tmp/fc.json; then
    echo "OK"
else
    case $? in
        1) echo "参数错" ;;
        3) echo "LLM 不可用(但 tool 不该 exit 3)" ;;
        *) echo "未知错" ;;
    esac
fi
```

---

## 4. SDK vs CLI — 何时用哪个

| 场景 | 推荐 | 原因 |
|------|------|------|
| Notebook / 探索性分析 | **SDK** | 一次会话内反复调,Python 原生对象 |
| Web app / 后端服务 | **SDK** | `RCAClient` 长生命周期,可缓存 config |
| ETL / 批处理 | **SDK** | 配合 pandas / polars 流水线 |
| CI / cron / 定时任务 | **CLI** | 进程隔离,无 Python 状态泄漏 |
| 一次性 ad-hoc 查 | **CLI** | 不用写脚本,直接终端 |
| 远程 SSH 上排查 | **CLI** | ssh 进去一行命令,不用传脚本 |
| 给非开发者用 | **CLI** | 不需要 Python 环境 |
| 写 demo / 录屏 | **CLI + rich** | 自动有彩色表格 |

**两者完全等价** — CLI 内部就是 `import rca` 然后调 SDK 函数。

---

## 5. 常见问题

### Q: `rca chat` 报 `LLMUnavailableError`?

确认三个 env 都设了:

```bash
echo $LLM_OPENAI_API_KEY
echo $LLM_OPENAI_BASE_URL
echo $LLM_DEFAULT_BACKEND
```

或者绕过 — 9 个 tool 完全不用 LLM,先跑 tool 验证数据层没问题。

### Q: 9 tool 跑出 0 / 异常值?

城市名 / 指标名要严格匹配。运行 `rca list-cities` 看支持哪些,再用合法 `name` 和 `indicator`。

### Q: 全局 `--format` 必须在子命令前?

是的,typer 的限制。`rca list-cities --format json` 不行,要用 `rca --format json list-cities`。或用 `python -m cli.main --format json list-cities`。

### Q: fallback chain 是什么?

`rca.chat()` 内部有 fallback chain:优先 `LLM_PRIMARY_MODEL`,失败后降级到 `LLM_FALLBACK_CHAIN`(默认 5 个模型)。这样某个模型限流/挂了,自动切下一个,不需要用户重试。

### Q: SDK 和 CLI 的输出格式一致吗?

数据层完全一致(`rca.forecast()` 和 `rca --format json forecast` 返同样的 dict)。CLI 只是多了 `rich` / `plain` 的人类可读渲染,不影响数据。

---

## 6. 链接

- [Spec v9.0](docs/superpowers/specs/2026-06-05-v90-sdk-cli-design.md) — 设计文档
- [Plan v9.0](docs/superpowers/plans/2026-06-05-v90-sdk-cli.md) — 22 task 实施计划
- [Eval 报告](tests/eval/reports/) — 多模型对比
- [Methodology](docs/METHODOLOGY.md) — 算法原理
- [Config Guide](docs/CONFIG_GUIDE.md) — 自定义配置

---

**License**: Apache-2.0 · **Status**: v9.1.0 stable · 9 tool + chat + chat-stream · 0 第三方 SaaS 依赖(LLM 除外)
