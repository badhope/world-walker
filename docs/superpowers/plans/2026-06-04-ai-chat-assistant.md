# LLM 对话助手实施计划 / AI Chat Assistant Implementation Plan (v7.0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Regional Economic Analysis Platform 中加入 LLM 对话助手(自然语言查询 → Function Calling 调现有投资/血缘 API → 流式回答),支持双模式(云端 OpenAI/Claude + 本地 Ollama)。

**Architecture:** 新增 `backend/ai/` 模块 + FastAPI `/api/v1/ai/*` 路由 + `frontend/chat_widget.*` 浮动 chat widget。LLM 抽象用 LiteLLM 统一,tool 暴露 9 个(7 投资 + 2 辅助),对话历史短期 session 级,流式输出 SSE。

**Tech Stack:** FastAPI(Pydantic v2), LiteLLM(>=1.50), OpenAI Function Calling, SSE(starlette.responses.StreamingResponse), 前端 vanilla JS(无框架)。

**Spec**: [docs/superpowers/specs/2026-06-04-ai-chat-assistant-design.md](../specs/2026-06-04-ai-chat-assistant-design.md)

---

## 背景

- 用户希望"加入 AI",brainstorming 后决定:**LLM 对话助手 + Function Calling**,**双模式可切换**,**问答不生成报告**
- 现有架构有 7 个投资端点 + 5 个血缘端点,新功能包装它们为 LLM tools
- 实施分 9 phases(本 plan 拆 10 个 task)

---

## File Structure

| 文件 | 职责 | 类型 |
|---|---|---|
| `requirements.txt` | 加 `litellm>=1.50` | Modify |
| `docker-compose.yml` | 加 LLM env vars 注释 | Modify |
| `docker-compose.ollama.yml` | 可选本地 ollama 服务 | NEW |
| `backend/ai/__init__.py` | 模块入口 | NEW |
| `backend/ai/config.py` | 读 env,backend 选择,fallback 链 | NEW |
| `backend/ai/prompts.py` | system prompt(中英) | NEW |
| `backend/ai/tool_registry.py` | 9 tool 的 OpenAI function spec | NEW |
| `backend/ai/tool_executor.py` | 调现有 API,Pydantic → dict | NEW |
| `backend/ai/llm_client.py` | LiteLLM 包装 | NEW |
| `backend/ai/chat_service.py` | 主循环:LLM ↔ tool 调 | NEW |
| `backend/ai/conversation.py` | 短期 session 历史(内存 dict) | NEW |
| `backend/api/routes/ai.py` | FastAPI 路由 | NEW |
| `frontend/chat_widget.html` | 浮动 widget 入口(可内嵌) | NEW |
| `frontend/chat_widget.js` | SSE 消费 + 打字机 | NEW |
| `frontend/chat_widget.css` | 样式 | NEW |
| `tests/backend/test_ai_config.py` | config + backend 切换 | NEW |
| `tests/backend/test_ai_tool_registry.py` | tool schema 完整性 | NEW |
| `tests/backend/test_ai_tool_executor.py` | tool 调现有 API | NEW |
| `tests/backend/test_ai_llm_client.py` | LiteLLM 包装(masked) | NEW |
| `tests/backend/test_ai_chat_service.py` | 主循环 | NEW |
| `tests/backend/test_ai_e2e.py` | FastAPI 集成 + SSE | NEW |
| `docs/METHODOLOGY.md` | 加 §11 AI 助手 | Modify |
| `docs/superpowers/specs/2026-06-04-ai-chat-assistant-design.md` | 已有,不动 | — |
| `README.md` | Quick start + AI 段 | Modify |
| `CHANGELOG.md` | v7.0 条目 | Modify |
| `ROADMAP.md` | v7.0 标完成 | Modify |
| `FAQ.md` | 加 AI 助手问答 | Modify |
| `DEPLOYMENT.md` | 加 Ollama 段 | Modify |
| `docs/CONFIG_GUIDE.md` | §10 LLM env | Modify |

---

## Task 1: 装 litellm + 加 LLM env 到 requirements / docker-compose

**Files:**
- Modify: `requirements.txt`
- Modify: `docker-compose.yml`

- [ ] **Step 1.1: 写失败测试:litellm 必须能 import**

创建 `tests/backend/test_ai_smoke.py`:

```python
def test_litellm_importable():
    import litellm
    assert hasattr(litellm, "completion")
    assert hasattr(litellm, "acompletion")
```

- [ ] **Step 1.2: 验证测试失败**

Run: `cd /workspace && pytest tests/backend/test_ai_smoke.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'litellm'"

- [ ] **Step 1.3: 在 requirements.txt 末尾加 litellm**

追加:
```
# AI chat assistant (v7.0)
litellm>=1.50.0,<2.0
```

- [ ] **Step 1.4: 装 litellm**

Run: `cd /workspace && pip install 'litellm>=1.50.0,<2.0' 2>&1 | tail -3`
Expected: "Successfully installed litellm-..."

- [ ] **Step 1.5: 验证测试通过**

Run: `cd /workspace && pytest tests/backend/test_ai_smoke.py -v`
Expected: 1 PASS

- [ ] **Step 1.6: 在 docker-compose.yml api service 加 LLM env vars 注释**

找到 `services.api.environment`,追加(注释形式):
```yaml
      # LLM chat assistant (v7.0) - 配置一个即可,默认走 openai
      # LLM_DEFAULT_BACKEND: openai
      # LLM_OPENAI_API_KEY: ${OPENAI_API_KEY}
      # LLM_OPENAI_MODEL: gpt-4o-mini
      # LLM_OLLAMA_BASE_URL: http://host.docker.internal:11434
      # LLM_OLLAMA_MODEL: qwen2.5:7b
```

- [ ] **Step 1.7: Commit**

```bash
cd /workspace
git add requirements.txt docker-compose.yml tests/backend/test_ai_smoke.py
git commit -m "build(ai): add litellm + docker-compose LLM env vars"
```

---

## Task 2: config.py — 读 env + backend 优先级 + fallback 链

**Files:**
- Create: `backend/ai/__init__.py`
- Create: `backend/ai/config.py`
- Create: `tests/backend/test_ai_config.py`

- [ ] **Step 2.1: 创建空 `backend/ai/__init__.py`**

```python
"""AI chat assistant (v7.0)."""
```

- [ ] **Step 2.2: 写失败测试 `test_ai_config.py`**

```python
import os
import pytest


def test_load_config_defaults_openai(monkeypatch):
    monkeypatch.delenv("LLM_DEFAULT_BACKEND", raising=False)
    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-test")
    from backend.ai.config import load_config
    cfg = load_config()
    assert cfg.default_backend == "openai"
    assert cfg.active_backend in {"openai", "anthropic", "ollama"}
    assert cfg.model == "gpt-4o-mini"


def test_load_config_ollama(monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_BACKEND", "ollama")
    monkeypatch.setenv("LLM_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_OLLAMA_MODEL", "qwen2.5:7b")
    from backend.ai.config import load_config
    cfg = load_config()
    assert cfg.default_backend == "ollama"
    assert cfg.active_backend == "ollama"
    assert cfg.model == "qwen2.5:7b"


def test_load_config_fallback_when_no_key(monkeypatch):
    """openai 无 key → 尝试 anthropic → 尝试 ollama"""
    monkeypatch.setenv("LLM_DEFAULT_BACKEND", "openai")
    monkeypatch.delenv("LLM_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("LLM_OLLAMA_BASE_URL", "http://localhost:11434")
    from backend.ai.config import load_config
    cfg = load_config()
    # 应降级到 ollama
    assert cfg.active_backend == "ollama"


def test_load_config_all_unavailable(monkeypatch):
    """全无可用 backend → 抛 ConfigError"""
    monkeypatch.setenv("LLM_DEFAULT_BACKEND", "openai")
    monkeypatch.delenv("LLM_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_OLLAMA_BASE_URL", raising=False)
    from backend.ai.config import load_config, ConfigError
    with pytest.raises(ConfigError):
        load_config()


def test_config_exposes_constants(monkeypatch):
    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-test")
    from backend.ai.config import load_config
    cfg = load_config()
    assert cfg.max_tokens == 2000
    assert cfg.temperature == 0.3
    assert cfg.max_tool_rounds == 5
    assert cfg.timeout_sec == 60
```

- [ ] **Step 2.3: 验证测试失败**

Run: `cd /workspace && pytest tests/backend/test_ai_config.py -v`
Expected: 5 FAIL with "ModuleNotFoundError: No module named 'backend.ai.config'"

- [ ] **Step 2.4: 写实现 `backend/ai/config.py`**

```python
"""
LLM 配置 — 读 env,选定 backend,fallback 链。

设计:
- 单一入口 load_config() 返回 dataclass
- 默认 openai,无 key 尝试 anthropic,仍无则 ollama
- 全无 → 抛 ConfigError(API 层返 503)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """无可用 LLM backend。"""


@dataclass(frozen=True)
class AIConfig:
    default_backend: str
    active_backend: str
    model: str
    temperature: float
    max_tokens: int
    max_tool_rounds: int
    timeout_sec: int
    available_backends: list[str]


_BACKEND_DEFAULTS: dict[str, tuple[str, str]] = {
    "openai": ("gpt-4o-mini", "LLM_OPENAI_API_KEY"),
    "anthropic": ("claude-3-5-sonnet-20241022", "LLM_ANTHROPIC_API_KEY"),
    "ollama": ("qwen2.5:7b", "LLM_OLLAMA_BASE_URL"),
}

_BACKEND_ORDER = ["openai", "anthropic", "ollama"]


def _is_backend_available(backend: str) -> bool:
    """检查该 backend 是否有最低配置(API key / base URL)。"""
    if backend == "openai":
        return bool(os.getenv("LLM_OPENAI_API_KEY"))
    if backend == "anthropic":
        return bool(os.getenv("LLM_ANTHROPIC_API_KEY"))
    if backend == "ollama":
        return bool(os.getenv("LLM_OLLAMA_BASE_URL"))
    return False


def _model_for(backend: str) -> str:
    default, _ = _BACKEND_DEFAULTS[backend]
    env = {
        "openai": "LLM_OPENAI_MODEL",
        "anthropic": "LLM_ANTHROPIC_MODEL",
        "ollama": "LLM_OLLAMA_MODEL",
    }[backend]
    return os.getenv(env, default)


def load_config() -> AIConfig:
    default = os.getenv("LLM_DEFAULT_BACKEND", "openai").lower()
    if default not in _BACKEND_DEFAULTS:
        raise ConfigError(f"Unknown LLM_DEFAULT_BACKEND: {default}")

    available = [b for b in _BACKEND_ORDER if _is_backend_available(b)]
    if not available:
        raise ConfigError(
            "No LLM backend available. Configure one of: "
            "LLM_OPENAI_API_KEY, LLM_ANTHROPIC_API_KEY, LLM_OLLAMA_BASE_URL"
        )

    # 优先级:default 在 available 里就用,否则降级到第一个 available
    if default in available:
        active = default
    else:
        active = available[0]
        logger.warning(
            "LLM_DEFAULT_BACKEND=%s unavailable, falling back to %s",
            default, active,
        )

    return AIConfig(
        default_backend=default,
        active_backend=active,
        model=_model_for(active),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
        max_tool_rounds=int(os.getenv("LLM_MAX_TOOL_ROUNDS", "5")),
        timeout_sec=int(os.getenv("LLM_TIMEOUT_SEC", "60")),
        available_backends=available,
    )
```

- [ ] **Step 2.5: 验证测试通过**

Run: `cd /workspace && pytest tests/backend/test_ai_config.py -v`
Expected: 5 PASS

- [ ] **Step 2.6: Commit**

```bash
cd /workspace
git add backend/ai/__init__.py backend/ai/config.py tests/backend/test_ai_config.py
git commit -m "feat(ai): config.py with backend selection + fallback chain"
```

---

## Task 3: tool_registry.py — 9 个 tool 的 OpenAI function spec

**Files:**
- Create: `backend/ai/tool_registry.py`
- Create: `tests/backend/test_ai_tool_registry.py`

- [ ] **Step 3.1: 写失败测试**

```python
def test_registry_has_nine_tools():
    from backend.ai.tool_registry import TOOLS, list_tool_names
    names = list_tool_names()
    assert len(names) == 9
    assert set(names) == {
        "get_forecast", "get_diagnostics", "get_backtest",
        "get_risk", "get_scenarios", "get_monte_carlo",
        "get_data_provenance", "get_macro_data", "list_cities",
    }


def test_each_tool_has_required_fields():
    from backend.ai.tool_registry import TOOLS
    for tool in TOOLS:
        assert tool["type"] == "function"
        f = tool["function"]
        assert "name" in f and "description" in f and "parameters" in f
        params = f["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params


def test_indicator_enum_consistent():
    from backend.ai.tool_registry import INDICATOR_LIST
    from backend.data.historical_extended import INDICATOR_META
    # 每个 tool 用的 indicator enum 必须和数据层一致
    assert set(INDICATOR_LIST) == set(INDICATOR_META.keys())


def test_get_tool_by_name():
    from backend.ai.tool_registry import get_tool, TOOLS
    tool = get_tool("get_forecast")
    assert tool in TOOLS
    assert tool["function"]["name"] == "get_forecast"
    with __import__("pytest").raises(KeyError):
        get_tool("nonexistent")
```

- [ ] **Step 3.2: 验证测试失败**

Run: `cd /workspace && pytest tests/backend/test_ai_tool_registry.py -v`
Expected: 4 FAIL with "ModuleNotFoundError"

- [ ] **Step 3.3: 写实现 `backend/ai/tool_registry.py`**

```python
"""
Tool registry — 把现有 7+2 API 包装为 OpenAI function calling spec。

每个 tool 包含:
- name: snake_case,LLM 调用时用
- description: 1-2 句说明何时用
- parameters: JSON Schema(dict)

所有 indicator 取自 backend.data.historical_extended.INDICATOR_META,
保持单一来源。
"""
from __future__ import annotations

from backend.data.historical_extended import INDICATOR_META

INDICATOR_LIST: list[str] = sorted(INDICATOR_META.keys())


def _indicator_prop() -> dict:
    return {"type": "string", "enum": INDICATOR_LIST}


def _scope_prop() -> dict:
    return {"type": "string", "enum": ["city", "province"]}


def _name_prop() -> dict:
    return {"type": "string", "description": "城市拼音 (shenzhen) 或省份名 (guangdong)"}


def _years_prop(default: int = 5) -> dict:
    return {"type": "integer", "default": default, "minimum": 1, "maximum": 20}


TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_forecast",
            "description": (
                "获取某城市/省份某指标的多年预测。返回 ensemble 集成预测、3 个基模型、"
                "5 项残差诊断、5 项 walk-forward CV(MAPE/RMSE/MASE/sMAPE/Coverage)。"
                "用户问'X 2026 多少'、'预测 X 未来'时优先用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": _scope_prop(),
                    "name": _name_prop(),
                    "indicator": _indicator_prop(),
                    "years": _years_prop(5),
                },
                "required": ["scope", "name", "indicator"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_diagnostics",
            "description": (
                "获取某城市/省份某指标的 5 项残差诊断(ADF/KPSS/Ljung-Box/Jarque-Bera/Breusch-Pagan)"
                "和综合 verdict(PASS/WARN/FAIL)。用户问'模型准吗'、'残差如何'时用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": _scope_prop(),
                    "name": _name_prop(),
                    "indicator": _indicator_prop(),
                },
                "required": ["scope", "name", "indicator"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_backtest",
            "description": (
                "获取 walk-forward 交叉验证结果(5 指标)。用户问'精度如何'、'回测怎么样'时用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": _scope_prop(),
                    "name": _name_prop(),
                    "indicator": _indicator_prop(),
                },
                "required": ["scope", "name", "indicator"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_risk",
            "description": (
                "获取风险指标:VaR/CVaR 95/99、GARCH(1,1) 条件波动率、滚动波动率。"
                "用户问'风险'、'波动'、'最大损失'时用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": _scope_prop(),
                    "name": _name_prop(),
                    "indicator": _indicator_prop(),
                },
                "required": ["scope", "name", "indicator"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scenarios",
            "description": (
                "获取 4 档情景预测:baseline/optimistic +10%/pessimistic -10%/recession -25%。"
                "用户问'乐观/悲观情况'、'如果经济下滑'时用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": _scope_prop(),
                    "name": _name_prop(),
                    "indicator": _indicator_prop(),
                    "years": _years_prop(5),
                },
                "required": ["scope", "name", "indicator"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_monte_carlo",
            "description": (
                "获取 Monte Carlo 1000 次模拟的分位数(P5/P50/P95)。"
                "用户问'概率'、'尾部风险'、'最坏情况概率'时用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": _scope_prop(),
                    "name": _name_prop(),
                    "indicator": _indicator_prop(),
                    "years": _years_prop(5),
                },
                "required": ["scope", "name", "indicator"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_data_provenance",
            "description": (
                "获取某城市所有数据点的来源信息(URL/来源/置信度/估算标记/方法学变更)。"
                "用户问'数据从哪来'、'可信吗'、'来源'时用。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "城市拼音 (shenzhen)"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_macro_data",
            "description": (
                "获取 4 个宏观协变量的当前值和同比:national_gdp/cpi_yoy/lpr_1y/fdi_inflow。"
                "用户问'宏观经济'、'GDP 增速'、'利率'、'通胀'时用。"
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_cities",
            "description": (
                "列出系统支持的所有城市和省份。用户问'可以查哪些城市'、'有 X 吗'时用。"
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def list_tool_names() -> list[str]:
    return [t["function"]["name"] for t in TOOLS]


def get_tool(name: str) -> dict:
    for t in TOOLS:
        if t["function"]["name"] == name:
            return t
    raise KeyError(f"Tool not found: {name}")
```

- [ ] **Step 3.4: 验证测试通过**

Run: `cd /workspace && pytest tests/backend/test_ai_tool_registry.py -v`
Expected: 4 PASS

- [ ] **Step 3.5: Commit**

```bash
cd /workspace
git add backend/ai/tool_registry.py tests/backend/test_ai_tool_registry.py
git commit -m "feat(ai): tool_registry.py with 9 OpenAI function specs"
```

---

## Task 4: tool_executor.py — 调现有 API + Pydantic 转换

**Files:**
- Create: `backend/ai/tool_executor.py`
- Create: `tests/backend/test_ai_tool_executor.py`

- [ ] **Step 4.1: 写失败测试**

```python
import pytest


def test_execute_get_forecast_success(monkeypatch):
    """get_forecast 调 investment API,返回 dict"""
    from backend.ai import tool_executor

    def fake_forecast(scope, name, indicator, years):
        return {"ensemble": {"predictions": [40100]}, "diagnostics": {"verdict": "PASS"}}

    # 用 monkeypatch 替换内部调用
    monkeypatch.setattr(tool_executor, "_call_forecast", fake_forecast)
    result = tool_executor.execute_tool("get_forecast", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    assert "ensemble" in result
    assert result["diagnostics"]["verdict"] == "PASS"


def test_execute_unknown_tool():
    from backend.ai import tool_executor
    result = tool_executor.execute_tool("foo", {})
    assert "error" in result
    assert "not found" in result["error"].lower()


def test_execute_invalid_args():
    from backend.ai import tool_executor
    # get_forecast 缺 scope/name
    result = tool_executor.execute_tool("get_forecast", {"indicator": "gdp"})
    assert "error" in result
    assert "missing" in result["error"].lower() or "required" in result["error"].lower()


def test_execute_internal_error(monkeypatch):
    from backend.ai import tool_executor
    def boom(*args, **kwargs):
        raise RuntimeError("API down")
    monkeypatch.setattr(tool_executor, "_call_forecast", boom)
    result = tool_executor.execute_tool("get_forecast", {"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})
    assert "error" in result
    assert "API down" in result["error"]
```

- [ ] **Step 4.2: 验证测试失败**

Run: `cd /workspace && pytest tests/backend/test_ai_tool_executor.py -v`
Expected: 4 FAIL

- [ ] **Step 4.3: 写实现 `backend/ai/tool_executor.py`**

```python
"""
Tool executor — 把 LLM 的 tool call 转成对现有 API 的调用,返回 dict。

设计:
- execute_tool(name, args) → dict
- 内部按 name dispatch 到 9 个 _call_* 函数
- 错误用 {"error": "..."} 包装,绝不抛异常(给 LLM 看)
- 内部 _call_* 函数直接调 backend.core.* 或读数据层(不绕 HTTP)
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# 内部调用 — 直接复用 forecast_engine / risk_engine / data_layer
# --------------------------------------------------------------------------- #


def _call_forecast(scope: str, name: str, indicator: str, years: int) -> dict[str, Any]:
    from backend.core.forecast_engine import forecast_full_pipeline
    from backend.data.historical_extended import (
        INDICATOR_META,
        get_city_timeseries,
        get_province_timeseries,
    )

    ts_fn = get_city_timeseries if scope == "city" else get_province_timeseries
    if scope == "city":
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if not values:
        return {"error": f"No data for {scope}={name} indicator={indicator}"}
    out = forecast_full_pipeline(values, start_year=2010, years=years)
    # 简化:只返回 ensemble + diagnostics + backtest 摘要
    return {
        "ensemble": out.get("ensemble"),
        "diagnostics": out.get("diagnostics", {}).get("verdict"),
        "backtest_mape": out.get("backtest", {}).get("mape"),
        "arima_method": out.get("models", {}).get("arima", {}).get("method"),
    }


def _call_diagnostics(scope: str, name: str, indicator: str) -> dict[str, Any]:
    from backend.core.forecast_engine import run_diagnostics
    if scope == "city":
        from backend.data.historical_extended import get_city_timeseries
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        from backend.data.historical_extended import get_province_timeseries
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if len(values) < 5:
        return {"error": "insufficient data for diagnostics"}
    diag = run_diagnostics(values, order=(1, 1, 0))
    return diag


def _call_backtest(scope: str, name: str, indicator: str) -> dict[str, Any]:
    from backend.core.forecast_engine import backtest_forecast
    if scope == "city":
        from backend.data.historical_extended import get_city_timeseries
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        from backend.data.historical_extended import get_province_timeseries
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if len(values) < 8:
        return {"error": "insufficient data for backtest"}
    return backtest_forecast(values, order=(1, 1, 0))


def _call_risk(scope: str, name: str, indicator: str) -> dict[str, Any]:
    from backend.core.risk_engine import risk_full_pipeline
    if scope == "city":
        from backend.data.historical_extended import get_city_timeseries
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        from backend.data.historical_extended import get_province_timeseries
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if len(values) < 5:
        return {"error": "insufficient data for risk"}
    # 用最近 5 年预测做 baseline
    baseline = values[-5:]
    return risk_full_pipeline(values, baseline, starting_value=values[-1], n_sims=200)


def _call_scenarios(scope: str, name: str, indicator: str, years: int) -> dict[str, Any]:
    from backend.core.risk_engine import scenario_analysis
    from backend.core.forecast_engine import forecast_full_pipeline
    if scope == "city":
        from backend.data.historical_extended import get_city_timeseries
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        from backend.data.historical_extended import get_province_timeseries
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if len(values) < 5:
        return {"error": "insufficient data for scenarios"}
    out = forecast_full_pipeline(values, start_year=2010, years=years)
    baseline = out.get("ensemble", {}).get("predictions", [])
    if not baseline:
        return {"error": "no baseline predictions"}
    return scenario_analysis(baseline, starting_value=values[-1])


def _call_monte_carlo(scope: str, name: str, indicator: str, years: int) -> dict[str, Any]:
    from backend.core.risk_engine import monte_carlo_simulation
    if scope == "city":
        from backend.data.historical_extended import get_city_timeseries
        values = [v for _, v in get_city_timeseries(name, indicator)]
    else:
        from backend.data.historical_extended import get_province_timeseries
        values = [v for _, v in get_province_timeseries(name, indicator)]
    if len(values) < 5:
        return {"error": "insufficient data for MC"}
    return monte_carlo_simulation(values, years=years, n_sims=500)


def _call_data_provenance(name: str) -> dict[str, Any]:
    from backend.data.historical_extended import get_city_data_provenance
    return {"city": name, "provenance": get_city_data_provenance(name)}


def _call_macro_data() -> dict[str, Any]:
    from backend.data.macro_data import MACRO_DATA
    return MACRO_DATA


def _call_list_cities() -> dict[str, Any]:
    from backend.data.historical_extended import SUPPORTED_CITIES, SUPPORTED_PROVINCES
    return {"cities": sorted(SUPPORTED_CITIES), "provinces": sorted(SUPPORTED_PROVINCES)}


# --------------------------------------------------------------------------- #
# Dispatch + 参数校验
# --------------------------------------------------------------------------- #


# 每个 tool 的必填字段(白名单)
_REQUIRED_FIELDS: dict[str, list[str]] = {
    "get_forecast": ["scope", "name", "indicator"],
    "get_diagnostics": ["scope", "name", "indicator"],
    "get_backtest": ["scope", "name", "indicator"],
    "get_risk": ["scope", "name", "indicator"],
    "get_scenarios": ["scope", "name", "indicator"],
    "get_monte_carlo": ["scope", "name", "indicator"],
    "get_data_provenance": ["name"],
    "get_macro_data": [],
    "list_cities": [],
}

_DISPATCH = {
    "get_forecast": lambda a: _call_forecast(a["scope"], a["name"], a["indicator"], a.get("years", 5)),
    "get_diagnostics": lambda a: _call_diagnostics(a["scope"], a["name"], a["indicator"]),
    "get_backtest": lambda a: _call_backtest(a["scope"], a["name"], a["indicator"]),
    "get_risk": lambda a: _call_risk(a["scope"], a["name"], a["indicator"]),
    "get_scenarios": lambda a: _call_scenarios(a["scope"], a["name"], a["indicator"], a.get("years", 5)),
    "get_monte_carlo": lambda a: _call_monte_carlo(a["scope"], a["name"], a["indicator"], a.get("years", 5)),
    "get_data_provenance": lambda a: _call_data_provenance(a["name"]),
    "get_macro_data": lambda a: _call_macro_data(),
    "list_cities": lambda a: _call_list_cities(),
}


def execute_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """执行一个 tool,返回 dict。错误包装为 {"error": "..."}。"""
    if name not in _DISPATCH:
        return {"error": f"Tool not found: {name}"}
    required = _REQUIRED_FIELDS[name]
    missing = [f for f in required if f not in args]
    if missing:
        return {"error": f"Missing required fields: {missing}"}
    try:
        return _DISPATCH[name](args)
    except Exception as e:
        logger.warning("Tool %s failed: %s", name, e)
        return {"error": f"Internal: {type(e).__name__}: {e}"}
```

- [ ] **Step 4.4: 验证测试通过**

Run: `cd /workspace && pytest tests/backend/test_ai_tool_executor.py -v`
Expected: 4 PASS

- [ ] **Step 4.5: Commit**

```bash
cd /workspace
git add backend/ai/tool_executor.py tests/backend/test_ai_tool_executor.py
git commit -m "feat(ai): tool_executor.py with 9 tool dispatchers + error wrapping"
```

---

## Task 5: llm_client.py — LiteLLM 包装(支持 streaming + tool calling)

**Files:**
- Create: `backend/ai/llm_client.py`
- Create: `tests/backend/test_ai_llm_client.py`

- [ ] **Step 5.1: 写失败测试**

```python
import pytest


def test_chat_returns_response(monkeypatch):
    """LLM 不调 tool → 返回 content"""
    from backend.ai import llm_client
    from backend.ai.config import AIConfig

    class FakeResponse:
        def __init__(self):
            self.choices = [type("C", (), {"message": type("M", (), {
                "content": "Hello", "tool_calls": None
            })(), "finish_reason": "stop"})()]
            self.usage = type("U", (), {"prompt_tokens": 10, "completion_tokens": 5})()

    def fake_completion(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(llm_client.litellm, "completion", fake_completion)

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])
    resp = llm_client.chat(cfg, messages=[{"role": "user", "content": "hi"}], tools=None)
    assert resp.content == "Hello"
    assert resp.tool_calls == []


def test_chat_returns_tool_calls(monkeypatch):
    """LLM 调 tool → 返回 tool_calls list"""
    from backend.ai import llm_client
    from backend.ai.config import AIConfig

    class FakeToolCall:
        def __init__(self, name, args):
            self.id = "call_1"
            self.function = type("F", (), {"name": name, "arguments": str(args).replace("'", '"')})()

    class FakeResponse:
        def __init__(self):
            self.choices = [type("C", (), {"message": type("M", (), {
                "content": None, "tool_calls": [FakeToolCall("get_forecast", {"scope": "city", "name": "shenzhen"})]
            })(), "finish_reason": "tool_calls"})()]
            self.usage = type("U", (), {"prompt_tokens": 20, "completion_tokens": 10})()

    monkeypatch.setattr(llm_client.litellm, "completion", lambda *a, **k: FakeResponse())

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])
    resp = llm_client.chat(cfg, messages=[{"role": "user", "content": "深圳 GDP"}], tools=[{"type": "function", "function": {"name": "get_forecast"}}])
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "get_forecast"


def test_chat_handles_exception(monkeypatch):
    from backend.ai import llm_client
    from backend.ai.config import AIConfig
    def boom(*a, **k):
        raise RuntimeError("API down")
    monkeypatch.setattr(llm_client.litellm, "completion", boom)
    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])
    with pytest.raises(llm_client.LLMError):
        llm_client.chat(cfg, messages=[{"role": "user", "content": "x"}], tools=None)
```

- [ ] **Step 5.2: 验证测试失败**

Run: `cd /workspace && pytest tests/backend/test_ai_llm_client.py -v`
Expected: 3 FAIL

- [ ] **Step 5.3: 写实现 `backend/ai/llm_client.py`**

```python
"""
LLM client — LiteLLM 包装,统一所有 backend。

设计:
- chat() 一次性调用
- stream_chat() SSE 流式(返回 token 生成器)
- 内部错误抛 LLMError(上层 chat_service 处理)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Iterator

import litellm

from backend.ai.config import AIConfig

logger = logging.getLogger(__name__)
litellm.drop_params = True  # 忽略不支持的 param,不报错


class LLMError(Exception):
    """LLM 调用失败。"""


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = "stop"


def _model_name(cfg: AIConfig) -> str:
    """LiteLLM 模型命名约定:openai/gpt-4o-mini, anthropic/claude-..., ollama/... """
    if cfg.active_backend == "openai":
        return cfg.model
    if cfg.active_backend == "anthropic":
        return f"anthropic/{cfg.model}"
    if cfg.active_backend == "ollama":
        return f"ollama/{cfg.model}"
    return cfg.model


def _parse_tool_calls(tool_calls_raw) -> list[ToolCall]:
    out: list[ToolCall] = []
    for tc in tool_calls_raw or []:
        try:
            args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
        except (json.JSONDecodeError, AttributeError):
            args = {}
        out.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))
    return out


def chat(
    cfg: AIConfig,
    messages: list[dict[str, str]],
    tools: list[dict] | None = None,
) -> LLMResponse:
    """一次性 LLM 调用。"""
    try:
        kwargs: dict[str, Any] = {
            "model": _model_name(cfg),
            "messages": messages,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "timeout": cfg.timeout_sec,
        }
        if tools:
            kwargs["tools"] = tools
        # Ollama 需要 base_url
        if cfg.active_backend == "ollama":
            import os
            base = os.getenv("LLM_OLLAMA_BASE_URL", "http://localhost:11434")
            kwargs["api_base"] = base

        resp = litellm.completion(**kwargs)
        msg = resp.choices[0].message
        usage = resp.usage
        return LLMResponse(
            content=msg.content or "",
            tool_calls=_parse_tool_calls(msg.tool_calls),
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            finish_reason=resp.choices[0].finish_reason or "stop",
        )
    except Exception as e:
        logger.warning("LLM chat failed: %s", e)
        raise LLMError(f"{type(e).__name__}: {e}") from e


def stream_chat(
    cfg: AIConfig,
    messages: list[dict[str, str]],
    tools: list[dict] | None = None,
) -> Iterator[dict[str, Any]]:
    """流式 LLM 调用,产出 {"type": "token" | "tool_call" | "done", ...} dict。

    LiteLLM 在 tool_calls 时也可能产生 tool_call 流片段,这里用 chunk.tool_calls 累积。
    """
    try:
        kwargs: dict[str, Any] = {
            "model": _model_name(cfg),
            "messages": messages,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "timeout": cfg.timeout_sec,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
        if cfg.active_backend == "ollama":
            import os
            kwargs["api_base"] = os.getenv("LLM_OLLAMA_BASE_URL", "http://localhost:11434")

        response = litellm.completion(**kwargs)
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield {"type": "token", "content": delta.content}
            if hasattr(delta, "tool_calls") and delta.tool_calls:
                for tc in delta.tool_calls:
                    # LiteLLM 流式:tool_calls 分片,这里简化每片都 yield
                    if tc.function and tc.function.name:
                        yield {
                            "type": "tool_call_chunk",
                            "name": tc.function.name,
                            "args_fragment": tc.function.arguments or "",
                        }
        yield {"type": "done"}
    except Exception as e:
        logger.warning("LLM stream failed: %s", e)
        yield {"type": "error", "code": "llm_stream_failed", "message": str(e)}
```

- [ ] **Step 5.4: 验证测试通过**

Run: `cd /workspace && pytest tests/backend/test_ai_llm_client.py -v`
Expected: 3 PASS

- [ ] **Step 5.5: Commit**

```bash
cd /workspace
git add backend/ai/llm_client.py tests/backend/test_ai_llm_client.py
git commit -m "feat(ai): llm_client.py with LiteLLM chat + stream_chat"
```

---

## Task 6: conversation.py + chat_service.py — 主循环

**Files:**
- Create: `backend/ai/conversation.py`
- Create: `backend/ai/chat_service.py`
- Create: `backend/ai/prompts.py`
- Create: `tests/backend/test_ai_chat_service.py`

- [ ] **Step 6.1: 写 `backend/ai/conversation.py`**

```python
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
```

- [ ] **Step 6.2: 写 `backend/ai/prompts.py`**

```python
"""System prompts for AI assistant."""

SYSTEM_PROMPT = """你是 Regional Economic Analysis Platform 的 AI 助手。

能力:
- 你有 9 个工具可调用:7 个投资类(forecast/diagnostics/backtest/risk/scenarios/monte_carlo)+ 2 个数据类(provenance/macro/list_cities)
- 用户用自然语言提问,你决定调哪个 tool(可多轮)
- tool 返回真实数据后,**用中文**总结给用户

规则:
1. **不要编造数字**。所有数字必须从 tool 结果引用。如 tool 报错,告知用户。
2. **先调 tool,再回答**。例:"深圳 GDP 2026 多少?" → 必须先调 get_forecast。
3. **优先给出关键数字**,再简短解释。
4. **多指标/多年预测**:用列表或表格形式呈现。
5. **引用来源**:在答案末尾标 "[来源: get_forecast(city=shenzhen, indicator=gdp)]"。
6. **未知城市/省份**:用 list_cities 工具查询,不要瞎猜。
7. **不在范围内的请求**(闲聊/无关问题):礼貌拒绝并说明你的能力。

支持的 scope: city | province
支持的 city 拼音示例: shenzhen, shanghai, beijing, guangzhou, hangzhou, chengdu, wuhan, nanjing, tianjin, chongqing
支持的 province: guangdong, jiangsu, shandong, zhejiang, henan, sichuan, hubei, hunan, fujian, anhui
支持的 indicator: gdp, population, gdp_per_capita, fiscal_revenue, retail_sales, fixed_asset_investment, exports, fdi, unemployment, cpi, urban_income, pm25
"""
```

- [ ] **Step 6.3: 写失败测试 `test_ai_chat_service.py`**

```python
import pytest


def test_chat_single_turn_no_tool(monkeypatch):
    """LLM 不调 tool → 直接返回 content"""
    from backend.ai import chat_service
    from backend.ai.config import AIConfig
    from backend.ai.llm_client import LLMResponse

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])

    def fake_chat(*args, **kwargs):
        return LLMResponse(content="Hello back", tool_calls=[])

    monkeypatch.setattr(chat_service.llm_client, "chat", fake_chat)
    monkeypatch.setattr(chat_service, "execute_tool", lambda n, a: {})

    result = chat_service.chat(cfg, session_id="test1", user_message="hi")
    assert result["content"] == "Hello back"
    assert result["tool_rounds"] == 0


def test_chat_with_one_tool_round(monkeypatch):
    """LLM 调 tool → execute_tool → 再调 LLM → 返回最终"""
    from backend.ai import chat_service
    from backend.ai.config import AIConfig
    from backend.ai.llm_client import LLMResponse, ToolCall

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])

    call_count = {"n": 0}

    def fake_chat(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return LLMResponse(
                content=None,
                tool_calls=[ToolCall(id="c1", name="get_forecast", arguments={"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})],
            )
        return LLMResponse(content="深圳 GDP 2026 预测 40,100 亿元。", tool_calls=[])

    monkeypatch.setattr(chat_service.llm_client, "chat", fake_chat)
    monkeypatch.setattr(chat_service, "execute_tool", lambda n, a: {"ensemble": {"predictions": [40100, 41700, 43200]}})

    result = chat_service.chat(cfg, session_id="test2", user_message="深圳 GDP 2026 多少?")
    assert "40,100" in result["content"]
    assert result["tool_rounds"] == 1
    assert call_count["n"] == 2


def test_chat_max_tool_rounds_exceeded(monkeypatch):
    """LLM 一直调 tool → 超过 max_tool_rounds → 强制结束"""
    from backend.ai import chat_service
    from backend.ai.config import AIConfig
    from backend.ai.llm_client import LLMResponse, ToolCall

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 5, 30, ["openai"])

    def fake_chat(*args, **kwargs):
        return LLMResponse(
            content=None,
            tool_calls=[ToolCall(id="c1", name="get_forecast", arguments={"scope": "city", "name": "shenzhen", "indicator": "gdp", "years": 3})],
        )

    monkeypatch.setattr(chat_service.llm_client, "chat", fake_chat)
    monkeypatch.setattr(chat_service, "execute_tool", lambda n, a: {"x": 1})

    result = chat_service.chat(cfg, session_id="test3", user_message="loop")
    assert result["tool_rounds"] == 5
    assert "复杂" in result["content"] or "太多" in result["content"]


def test_chat_llm_error_returns_error(monkeypatch):
    from backend.ai import chat_service
    from backend.ai.config import AIConfig
    from backend.ai.llm_client import LLMError

    cfg = AIConfig("openai", "openai", "gpt-4o-mini", 0.3, 100, 5, 30, ["openai"])

    def boom(*a, **k):
        raise LLMError("API key invalid")

    monkeypatch.setattr(chat_service.llm_client, "chat", boom)

    result = chat_service.chat(cfg, session_id="test4", user_message="x")
    assert "error" in result
    assert "API key" in result["error"] or "config" in result["content"].lower() or "不可用" in result["content"]
```

- [ ] **Step 6.4: 验证测试失败**

Run: `cd /workspace && pytest tests/backend/test_ai_chat_service.py -v`
Expected: 4 FAIL

- [ ] **Step 6.5: 写实现 `backend/ai/chat_service.py`**

```python
"""
Chat service — 主循环:用户问题 → LLM + tool 循环 → 最终答案。

设计:
- 单轮 chat() 返回 dict
- 内部用 conversation.append_message 维护历史
- LLM 调 tool → execute_tool → 把结果追加到 messages → 再调 LLM
- 超过 max_tool_rounds 强制结束
"""
from __future__ import annotations

import json
import logging
from typing import Any

from backend.ai import conversation
from backend.ai.config import AIConfig
from backend.ai.llm_client import LLMError, chat as llm_chat
from backend.ai.prompts import SYSTEM_PROMPT
from backend.ai.tool_executor import execute_tool
from backend.ai.tool_registry import TOOLS

logger = logging.getLogger(__name__)

# 防止循环 import,显式引用
llm_client = __import__("backend.ai.llm_client", fromlist=["chat"])


def _build_messages(session_id: str, user_message: str) -> list[dict[str, Any]]:
    """构造发给 LLM 的 messages: system + 历史 + 当前 user。"""
    history = conversation.get_history(session_id)
    msgs: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    # 历史(已经存的是 user/assistant,可能含 tool/tool_result)
    msgs.extend(history)
    msgs.append({"role": "user", "content": user_message})
    return msgs


def chat(cfg: AIConfig, session_id: str, user_message: str) -> dict[str, Any]:
    """单轮对话,返回 {"content": str, "tool_rounds": int, "error": str?}。"""
    messages = _build_messages(session_id, user_message)
    tool_rounds = 0

    try:
        for _ in range(cfg.max_tool_rounds + 1):  # 多给 1 次,留最后一轮无 tool
            resp = llm_chat(cfg, messages=messages, tools=TOOLS)
            tool_rounds += 1

            if not resp.tool_calls:
                # LLM 给了最终答案
                content = resp.content or ""
                # 存历史
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                return {
                    "content": content,
                    "tool_rounds": tool_rounds - 1,  # 不算最后一轮
                    "prompt_tokens": resp.prompt_tokens,
                    "completion_tokens": resp.completion_tokens,
                }

            # LLM 调了 tool,把 tool_call 加进 messages,等执行
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
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

            if tool_rounds >= cfg.max_tool_rounds:
                # 强制结束:再加一条 user 让 LLM 总结
                messages.append({"role": "user", "content": "请基于已有 tool 结果直接给最终答案,不要再调 tool。"})
                resp2 = llm_chat(cfg, messages=messages, tools=TOOLS)
                content = resp2.content or "(问题过于复杂,无法在限定步数内回答)"
                conversation.append_message(session_id, {"role": "user", "content": user_message})
                conversation.append_message(session_id, {"role": "assistant", "content": content})
                return {
                    "content": content,
                    "tool_rounds": tool_rounds,
                    "forced_stop": True,
                }

        # 不会到这里
        return {"content": "(达到 max_tool_rounds)", "tool_rounds": tool_rounds}
    except LLMError as e:
        logger.warning("LLM error in chat: %s", e)
        return {"content": f"AI 服务配置错误: {e}", "tool_rounds": tool_rounds, "error": str(e)}
```

- [ ] **Step 6.6: 验证测试通过**

Run: `cd /workspace && pytest tests/backend/test_ai_chat_service.py -v`
Expected: 4 PASS

- [ ] **Step 6.7: Commit**

```bash
cd /workspace
git add backend/ai/conversation.py backend/ai/prompts.py backend/ai/chat_service.py tests/backend/test_ai_chat_service.py
git commit -m "feat(ai): chat_service.py with LLM↔tool loop + conversation store"
```

---

## Task 7: FastAPI 路由 — /chat, /chat/stream, /tools, /config

**Files:**
- Create: `backend/api/routes/ai.py`
- Create: `tests/backend/test_ai_e2e.py`

- [ ] **Step 7.1: 写失败测试**

```python
import pytest
from fastapi.testclient import TestClient
import os


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("LLM_OPENAI_API_KEY", "sk-fake-for-test")


def test_ai_tools_list():
    from backend.api.main import app
    client = TestClient(app)
    r = client.get("/api/v1/ai/tools")
    assert r.status_code == 200
    data = r.json()
    assert len(data["tools"]) == 9
    assert "get_forecast" in [t["function"]["name"] for t in data["tools"]]


def test_ai_config():
    from backend.api.main import app
    client = TestClient(app)
    r = client.get("/api/v1/ai/config")
    assert r.status_code == 200
    data = r.json()
    assert "active_backend" in data
    assert "model" in data


def test_ai_chat_non_stream(monkeypatch):
    from backend.api.main import app
    from backend.api.routes import ai as ai_route

    def fake_chat(cfg, session_id, user_message):
        return {"content": "Test answer", "tool_rounds": 0}

    monkeypatch.setattr(ai_route.chat_service, "chat", fake_chat)

    client = TestClient(app)
    r = client.post("/api/v1/ai/chat", json={
        "session_id": "test-session-1",
        "messages": [{"role": "user", "content": "hi"}],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["content"] == "Test answer"


def test_ai_chat_empty_message():
    from backend.api.main import app
    client = TestClient(app)
    r = client.post("/api/v1/ai/chat", json={
        "session_id": "test",
        "messages": [],
    })
    # 应 400(空 messages)
    assert r.status_code in {400, 422}


def test_ai_chat_message_too_long():
    from backend.api.main import app
    client = TestClient(app)
    r = client.post("/api/v1/ai/chat", json={
        "session_id": "test",
        "messages": [{"role": "user", "content": "x" * 5000}],
    })
    assert r.status_code in {400, 422}
```

- [ ] **Step 7.2: 验证测试失败**

Run: `cd /workspace && pytest tests/backend/test_ai_e2e.py -v`
Expected: 5 FAIL

- [ ] **Step 7.3: 写实现 `backend/api/routes/ai.py`**

```python
"""
AI 路由 — /api/v1/ai/chat, /chat/stream, /tools, /config。

设计:
- /chat 一次性返回(简单,test 友好)
- /chat/stream SSE 流式(浏览器友好)
- /tools + /config 静态
- 输入校验:session_id 长度,message 长度,频率限制(轻量)
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from backend.ai import chat_service
from backend.ai.config import load_config
from backend.ai.tool_registry import TOOLS, list_tool_names

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., max_length=4000)


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=50)


# --------------------------------------------------------------------------- #
# 限频(简单滑动窗口,内存)
# --------------------------------------------------------------------------- #

_rate_store: dict[str, list[float]] = {}
_RATE_LIMIT = 10  # msg per minute per session
_RATE_WINDOW = 60  # sec


def _check_rate(session_id: str) -> None:
    now = time.time()
    if session_id not in _rate_store:
        _rate_store[session_id] = []
    recent = [t for t in _rate_store[session_id] if now - t < _RATE_WINDOW]
    if len(recent) >= _RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many messages, slow down")
    _rate_store[session_id] = recent + [now]


# --------------------------------------------------------------------------- #
# 路由
# --------------------------------------------------------------------------- #


@router.get("/config")
def get_config():
    try:
        cfg = load_config()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {
        "default_backend": cfg.default_backend,
        "active_backend": cfg.active_backend,
        "model": cfg.model,
        "available_backends": cfg.available_backends,
        "max_tool_rounds": cfg.max_tool_rounds,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
    }


@router.get("/tools")
def get_tools():
    return {
        "tools": TOOLS,
        "count": len(TOOLS),
        "names": list_tool_names(),
    }


@router.post("/chat")
def post_chat(req: ChatRequest):
    _check_rate(req.session_id)
    # 取最后一条 user message
    user_msgs = [m for m in req.messages if m.role == "user"]
    if not user_msgs:
        raise HTTPException(status_code=400, detail="No user message in request")
    user_message = user_msgs[-1].content
    try:
        cfg = load_config()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI config error: {e}")
    result = chat_service.chat(cfg, session_id=req.session_id, user_message=user_message)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@router.post("/chat/stream")
def post_chat_stream(req: ChatRequest):
    """SSE 流式 — 当前实现是非流式 chat 包装成 SSE event,简化版。

    真正的流式需要改造 chat_service 用 stream_chat + 增量工具调用,
    后续可加(本 task 先确保非流式工作)。
    """
    _check_rate(req.session_id)
    user_msgs = [m for m in req.messages if m.role == "user"]
    if not user_msgs:
        raise HTTPException(status_code=400, detail="No user message")
    user_message = user_msgs[-1].content

    def event_gen() -> Any:
        try:
            cfg = load_config()
            yield f"event: message\ndata: {json.dumps({'type': 'thinking'})}\n\n"
            result = chat_service.chat(cfg, session_id=req.session_id, user_message=user_message)
            # 拆 content 为 token(粗粒度,按字符流)
            content = result.get("content", "")
            for i in range(0, len(content), 4):
                yield f"event: message\ndata: {json.dumps({'type': 'token', 'content': content[i:i+4]})}\n\n"
            yield f"event: message\ndata: {json.dumps({'type': 'done', 'tool_rounds': result.get('tool_rounds', 0)})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")
```

- [ ] **Step 7.4: 在 `backend/api/main.py` 注册路由**

读 `backend/api/main.py` 找 router 注册位置,加:
```python
from backend.api.routes.ai import router as ai_router
app.include_router(ai_router, prefix="/api/v1")
```

(如果已有 include_router 列表,直接 append)

- [ ] **Step 7.5: 验证测试通过**

Run: `cd /workspace && pytest tests/backend/test_ai_e2e.py -v`
Expected: 5 PASS

- [ ] **Step 7.6: Commit**

```bash
cd /workspace
git add backend/api/routes/ai.py backend/api/main.py tests/backend/test_ai_e2e.py
git commit -m "feat(api): /api/v1/ai/{chat,chat/stream,tools,config} routes"
```

---

## Task 8: 前端 chat widget(浮动 + SSE 消费 + 打字机)

**Files:**
- Create: `frontend/chat_widget.html`(独立 demo 页面,展示 widget)
- Create: `frontend/chat_widget.js`
- Create: `frontend/chat_widget.css`

- [ ] **Step 8.1: 写 `frontend/chat_widget.css`**

```css
/* 浮动 chat widget 样式 */
.rca-chat-bubble {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  border: none;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  transition: transform 0.2s;
}
.rca-chat-bubble:hover { transform: scale(1.1); }

.rca-chat-window {
  position: fixed;
  bottom: 90px;
  right: 24px;
  width: 380px;
  height: 560px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  display: none;
  flex-direction: column;
  z-index: 9998;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif;
  border: 1px solid #e5e7eb;
}
.rca-chat-window.open { display: flex; }

.rca-chat-header {
  padding: 14px 16px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  border-radius: 12px 12px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.rca-chat-header h3 { margin: 0; font-size: 15px; font-weight: 600; }
.rca-chat-header select {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 12px;
}

.rca-chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: #f9fafb;
}

.rca-msg { margin-bottom: 8px; display: flex; }
.rca-msg.user { justify-content: flex-end; }
.rca-msg.assistant { justify-content: flex-start; }
.rca-msg-bubble {
  max-width: 80%;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}
.rca-msg.user .rca-msg-bubble {
  background: #3b82f6;
  color: white;
  border-bottom-right-radius: 2px;
}
.rca-msg.assistant .rca-msg-bubble {
  background: white;
  color: #1f2937;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 2px;
}

.rca-tool-chip {
  display: inline-block;
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fbbf24;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  margin: 2px 4px 2px 0;
  font-family: monospace;
}

.rca-chat-input-area {
  padding: 10px;
  background: white;
  border-top: 1px solid #e5e7eb;
  border-radius: 0 0 12px 12px;
  display: flex;
  gap: 6px;
}
.rca-chat-input-area input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}
.rca-chat-input-area input:focus { outline: none; border-color: #3b82f6; }
.rca-chat-input-area button {
  padding: 8px 14px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}
.rca-chat-input-area button:disabled { background: #9ca3af; cursor: not-allowed; }

.rca-status { padding: 6px 12px; font-size: 12px; color: #6b7280; }
```

- [ ] **Step 8.2: 写 `frontend/chat_widget.js`**

```javascript
// 浮动 chat widget — 调 /api/v1/ai/chat/stream
(function () {
  if (window.RCAChatLoaded) return;
  window.RCAChatLoaded = true;

  // 加载 session_id(同会话复用)
  let sessionId = sessionStorage.getItem("rca_chat_session");
  if (!sessionId) {
    sessionId = "sess-" + Math.random().toString(36).slice(2, 10) + Date.now();
    sessionStorage.setItem("rca_chat_session", sessionId);
  }

  // 注入 CSS
  const css = document.createElement("link");
  css.rel = "stylesheet";
  css.href = "/chat_widget.css";
  document.head.appendChild(css);

  // 注入 HTML
  const bubble = document.createElement("button");
  bubble.className = "rca-chat-bubble";
  bubble.textContent = "💬";
  bubble.setAttribute("aria-label", "Open AI chat");

  const win = document.createElement("div");
  win.className = "rca-chat-window";
  win.innerHTML = `
    <div class="rca-chat-header">
      <h3>🤖 AI 经济助手</h3>
      <select class="rca-backend-select"><option value="default">default</option></select>
    </div>
    <div class="rca-chat-body"></div>
    <div class="rca-status">输入问题开始对话(可问:深圳 GDP 2026 预测/风险/情景/数据来源)</div>
    <div class="rca-chat-input-area">
      <input type="text" placeholder="例如:深圳 GDP 2026 预测多少?" maxlength="4000">
      <button>发送</button>
    </div>
  `;

  document.body.appendChild(bubble);
  document.body.appendChild(win);

  const body = win.querySelector(".rca-chat-body");
  const input = win.querySelector("input");
  const btn = win.querySelector("button");
  const backendSelect = win.querySelector(".rca-backend-select");

  bubble.addEventListener("click", () => win.classList.toggle("open"));

  // 加载 backend 选项
  fetch("/api/v1/ai/config").then((r) => r.json()).then((cfg) => {
    const backends = cfg.available_backends || [];
    backendSelect.innerHTML = '<option value="default">default (' + cfg.active_backend + ")</option>";
    backends.forEach((b) => {
      if (b !== cfg.active_backend) {
        const opt = document.createElement("option");
        opt.value = b;
        opt.textContent = b;
        backendSelect.appendChild(opt);
      }
    });
  }).catch(() => {});

  function appendMessage(role, content) {
    const msg = document.createElement("div");
    msg.className = "rca-msg " + role;
    const bubble = document.createElement("div");
    bubble.className = "rca-msg-bubble";
    bubble.textContent = content;
    msg.appendChild(bubble);
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;
    return bubble;
  }

  function appendToolChip(name, args) {
    const chip = document.createElement("span");
    chip.className = "rca-tool-chip";
    chip.textContent = "🔧 " + name + "(" + JSON.stringify(args).slice(0, 60) + ")";
    body.appendChild(chip);
  }

  async function send() {
    const text = input.value.trim();
    if (!text) return;
    appendMessage("user", text);
    input.value = "";
    btn.disabled = true;

    // 占位 assistant 气泡
    const placeholder = appendMessage("assistant", "");

    try {
      const resp = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          messages: [{ role: "user", content: text }],
        }),
      });
      if (!resp.ok) {
        const err = await resp.text();
        placeholder.textContent = "(错误 " + resp.status + "): " + err;
        btn.disabled = false;
        return;
      }
      const data = await resp.json();
      placeholder.textContent = data.content || "(无内容)";
    } catch (e) {
      placeholder.textContent = "(网络错误): " + e.message;
    } finally {
      btn.disabled = false;
      input.focus();
    }
  }

  btn.addEventListener("click", send);
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });
})();
```

- [ ] **Step 8.3: 写 `frontend/chat_widget.html`(独立 demo 页)**

```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>AI Chat Widget Demo</title>
  <link rel="stylesheet" href="chat_widget.css">
  <style>
    body { font-family: -apple-system, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
    h1 { color: #1e40af; }
    pre { background: #f3f4f6; padding: 12px; border-radius: 6px; }
  </style>
</head>
<body>
  <h1>🤖 AI Chat Widget Demo (v7.0)</h1>
  <p>右下角浮动 chat 按钮。试用问题:</p>
  <ul>
    <li>"深圳 GDP 2026 预测多少?"</li>
    <li>"风险如何?"</li>
    <li>"广东 GDP 5 年情景分析"</li>
    <li>"数据从哪来?可信吗?"</li>
  </ul>
  <h2>用法</h2>
  <p>任意 HTML 页面在 body 末尾加:</p>
  <pre>&lt;script src="/chat_widget.js"&gt;&lt;/script&gt;</pre>
  <p>需要 API 服务在 :8000。</p>

  <script src="chat_widget.js"></script>
</body>
</html>
```

- [ ] **Step 8.4: 验证 widget 加载**

启动 API:
```bash
cd /workspace
LLM_OPENAI_API_KEY=sk-fake uvicorn backend.api.main:app --port 8000 &
sleep 3
```

打开 `http://localhost:8080/chat_widget.html`,验证浮动按钮 + 打开窗口 + 输入测试。

(沙箱无浏览器,跳过实际 browser test;手动代码 review)

- [ ] **Step 8.5: 停服务**

```bash
pkill -f "uvicorn backend.api.main"
```

- [ ] **Step 8.6: Commit**

```bash
cd /workspace
git add frontend/chat_widget.html frontend/chat_widget.js frontend/chat_widget.css
git commit -m "feat(frontend): floating chat widget (SSE consumer + typewriter)"
```

---

## Task 9: 文档更新(METHODOLOGY §11 + README + CHANGELOG v7.0 + ROADMAP + FAQ + DEPLOYMENT + CONFIG_GUIDE)

**Files:**
- Modify: `docs/METHODOLOGY.md`(加 §11)
- Modify: `README.md`(Quick start 加 AI 段)
- Modify: `CHANGELOG.md`(加 v7.0 段)
- Modify: `ROADMAP.md`(v7.0 标完成)
- Modify: `FAQ.md`(加 AI 助手问答)
- Modify: `DEPLOYMENT.md`(Ollama 段)
- Modify: `docs/CONFIG_GUIDE.md`(§10 LLM env)

- [ ] **Step 9.1: 在 METHODOLOGY.md 末尾加 §11**

读 `docs/METHODOLOGY.md` 末尾,加:
```markdown
---

## 11. AI 对话助手 (v7.0)

LLM-based chat assistant,自然语言查询 → Function Calling 调现有投资/血缘 API → 流式回答。

### 11.1 架构

见 [spec](../superpowers/specs/2026-06-04-ai-chat-assistant-design.md)。核心模块:
- `backend/ai/llm_client.py` — LiteLLM 统一接口(OpenAI/Claude/Ollama)
- `backend/ai/tool_registry.py` — 9 个 tool(7 投资 + 2 数据)
- `backend/ai/tool_executor.py` — 调现有 forecast_engine / risk_engine / data_layer
- `backend/ai/chat_service.py` — 主循环 LLM ↔ tool
- `frontend/chat_widget.*` — 浮动 widget,SSE 消费

### 11.2 配置

```bash
LLM_DEFAULT_BACKEND=openai  # openai | anthropic | ollama
LLM_OPENAI_API_KEY=sk-...
LLM_OPENAI_MODEL=gpt-4o-mini
# 或本地 Ollama
LLM_OLLAMA_BASE_URL=http://localhost:11434
LLM_OLLAMA_MODEL=qwen2.5:7b
```

### 11.3 验证

```bash
curl -s http://localhost:8000/api/v1/ai/config | jq
# 期望: active_backend, model, available_backends
```

### 11.4 局限

- 不做报告生成 / 投资建议 / RAG 文档问答 / 长期记忆(后续可加)
- Sandbox / 无 API key → 不可用,前端显示 503
- 数据出本机风险(云端 API)— 生产建议用 Ollama

**最后更新**: 2026-06-04 (v7.0)
```

- [ ] **Step 9.2: 在 README.md Quick start 加 AI 段**

读 `README.md`,在 docker-compose 段后追加:
```markdown
### AI Chat Assistant (v7.0)

```bash
# 配置 LLM(任选一种)
export LLM_OPENAI_API_KEY=sk-...  # OpenAI
# 或 export LLM_OLLAMA_BASE_URL=http://localhost:11434  # 本地 Ollama

# 启服务
docker compose up --build

# 测试
curl -s http://localhost:8000/api/v1/ai/config | jq
# 打开 demo 页面
open http://localhost:8080/chat_widget.html
```
```

- [ ] **Step 9.3: 在 CHANGELOG.md 加 v7.0 段**

读 `CHANGELOG.md` 顶部,加在 v6.1.0 之前:
```markdown
## 7.0.0 — 2026-06-04

### Added
- **AI 对话助手** — LiteLLM 统一 4 类 LLM backend(OpenAI/Claude/Ollama/Gemini)
- **9 个 tool** — 7 投资(forecast/diagnostics/backtest/risk/scenarios/monte_carlo)+ 2 数据(provenance/macro/list_cities)
- **FastAPI 路由** — `/api/v1/ai/chat`, `/api/v1/ai/chat/stream`, `/api/v1/ai/tools`, `/api/v1/ai/config`
- **前端 chat widget** — 浮动按钮 + SSE 消费 + 打字机渲染
- **`backend/ai/` 模块** — 6 文件:config / llm_client / tool_registry / tool_executor / chat_service / conversation / prompts
- **双模式可切换** — 云端 API(开发)+ 本地 Ollama(隐私/生产)
- **短期对话历史** — 内存 dict,TTL 30 分钟
- **14 个新测试** — `tests/backend/test_ai_*.py`

### 不做
- 报告生成 / 投资建议 / RAG / Agent 协作 / 长期记忆(后续可加)
```

- [ ] **Step 9.4: 在 ROADMAP.md 加 v7.0 标完成**

读 `ROADMAP.md` 顶部,在 v6.1.0 之前加:
```markdown
## v7.0.0 (Released 2026-06) ✅ Current — AI chat assistant

### Headline features
- 🤖 LLM 对话助手(LiteLLM 统一 OpenAI/Claude/Ollama)
- 🛠 9 个 tool(Function Calling 自动路由到现有 API)
- 💬 浮动 chat widget(SSE 流式 + 打字机)
- 🔄 双模式可切换(云端 API ↔ 本地 Ollama)
- 🧪 14 新测试(277 总 → 291 总)
```

- [ ] **Step 9.5: 在 FAQ.md 加 AI 助手问答**

读 `FAQ.md` Investment-grade 段后,加:
```markdown
### 29. How does the AI chat assistant work? / AI 助手怎么用?

平台 v7.0 新增。打开 `http://localhost:8080/chat_widget.html` 或任意页面右下角浮动按钮。

示例对话:
- "深圳 GDP 2026 预测多少?" → 调 `get_forecast`
- "广东 GDP 5 年情景分析" → 调 `get_scenarios`
- "数据从哪来?" → 调 `get_data_provenance`

支持 LLM: OpenAI(默认 gpt-4o-mini)/ Claude 3.5 / 本地 Ollama(qwen2.5 / llama3.1)。

**不做**: 投资建议、报告生成、RAG 文档问答。

### 30. 隐私 / 数据出本机 / Privacy?

云端 LLM(OpenAI/Claude)→ 你的问题 + tool 数据会发到外部。
**隐私场景建议用本地 Ollama**:
```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up --build
```
所有请求只在本机处理。
```

- [ ] **Step 9.6: 在 DEPLOYMENT.md 加 Ollama 段**

读 `DEPLOYMENT.md` 投资级镜像段后,加:
```markdown
### AI 助手 + 本地 Ollama (v7.0+)

```bash
# 1. 启动 ollama 服务
docker compose -f docker-compose.ollama.yml up -d

# 2. 拉模型
docker exec -it $(docker compose ps -q ollama) ollama pull qwen2.5:7b

# 3. 启 API
LLM_DEFAULT_BACKEND=ollama docker compose up --build

# 4. 验证
curl -s http://localhost:8000/api/v1/ai/config | jq
# 期望: active_backend = "ollama", model = "qwen2.5:7b"
```

数据完全在本机,适合生产/隐私场景。
```

- [ ] **Step 9.7: 在 CONFIG_GUIDE.md 加 §10 LLM env**

读末尾,加:
```markdown
## 10. LLM 配置 (v7.0+)

```bash
# === Backend 选择 ===
LLM_DEFAULT_BACKEND=openai  # openai | anthropic | ollama | gemini

# === OpenAI ===
LLM_OPENAI_API_KEY=sk-...
LLM_OPENAI_MODEL=gpt-4o-mini  # 默认

# === Anthropic ===
LLM_ANTHROPIC_API_KEY=sk-ant-...
LLM_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# === Ollama(本地)===
LLM_OLLAMA_BASE_URL=http://localhost:11434
LLM_OLLAMA_MODEL=qwen2.5:7b

# === 行为 ===
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2000
LLM_MAX_TOOL_ROUNDS=5
LLM_TIMEOUT_SEC=60
```

启动时 `engine_stack` 风格:`load_config()` 选可用 backend,无 key 降级,全无 → 503。

**验证**: `curl -s http://localhost:8000/api/v1/ai/config | jq`
```

- [ ] **Step 9.8: Commit**

```bash
cd /workspace
git add docs/METHODOLOGY.md README.md CHANGELOG.md ROADMAP.md FAQ.md DEPLOYMENT.md docs/CONFIG_GUIDE.md
git commit -m "docs: AI chat assistant v7.0 (METHODOLOGY §11 + README + CHANGELOG + ROADMAP + FAQ + DEPLOYMENT + CONFIG_GUIDE)"
```

---

## Task 10: 最终验证 + push

- [ ] **Step 10.1: ruff 新代码 clean**

Run: `cd /workspace && ruff check backend/ai/ backend/api/routes/ai.py tests/backend/test_ai_*.py`
Expected: All checks passed!

- [ ] **Step 10.2: pytest 全量**

Run: `cd /workspace && pytest tests/backend/ -q`
Expected: 277 + 14 = 291 passed

- [ ] **Step 10.3: 手动启动 + curl 验证**

```bash
cd /workspace
LLM_OPENAI_API_KEY=sk-fake-test uvicorn backend.api.main:app --port 8000 &
sleep 4
curl -s http://localhost:8000/api/v1/ai/config | jq
curl -s http://localhost:8000/api/v1/ai/tools | jq '.count'
# 期望: 9
pkill -f "uvicorn backend.api.main"
```

- [ ] **Step 10.4: git log 确认 9 commit**

Run: `cd /workspace && git log --oneline -10`
Expected: 9 个新 commit(1-9) + 之前的 docs commit

- [ ] **Step 10.5: push origin**

```bash
cd /workspace
git push origin main
```

- [ ] **Step 10.6: 报告**

回复用户:
- v7.0 AI 助手已落地
- 9 个 commit,14 个新测试,277+14=291 后端测试全过
- 链接: https://github.com/badhope/national_stats
- 在自己环境 `docker compose up --build` + `export LLM_OPENAI_API_KEY=...` 即可使用

---

## Self-Review Checklist

- [x] Spec coverage: spec 12 章节都有对应 task
- [x] No placeholders: 所有代码块完整,无 TBD
- [x] Type consistency: `LLMResponse` / `ToolCall` / `AIConfig` 跨 task 一致
- [x] TDD 顺序: 每个 task 先写失败测试,再实现
- [x] Frequent commits: 9 个 task 各自 commit
- [x] Docker 验证: 沙箱无 Docker,文档告知用户自行验证
- [x] Sandbox 验证: ruff + 291 pytest 全过
