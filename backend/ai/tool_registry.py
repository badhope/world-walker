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
