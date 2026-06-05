"""SDK 9 tool wrapper — 把 backend.ai.tool_executor 的 dict 接口包装成 **kwargs 函数。

设计:
- 每个 tool 1 个公开函数,**kwargs 跟 tool schema 一致
- 内部直接 import + 调 execute_tool(不重写逻辑)
- 错误处理:tool_executor 返 {"error": "..."} 时,抛 ToolArgumentError
"""
from __future__ import annotations

from typing import Any

from backend.ai.tool_executor import execute_tool
from rca.errors import ToolArgumentError, ToolNotFoundError


def _invoke(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """统一 invoke — 处理 dispatch + 错误包装。

    Args:
        name: tool 名("get_forecast" 等)
        args: tool 参数字典

    Returns:
        tool_executor 返回的 dict(成功 {"data": ..., "navigate_to": ...})

    Raises:
        ToolNotFoundError: tool 名不在 _DISPATCH
        ToolArgumentError: tool 返 {"error": ...} 或缺必填字段
    """
    try:
        result = execute_tool(name, args)
    except KeyError as e:
        # execute_tool 内部不抛 KeyError,但 _DISPATCH 改了名要兼容
        raise ToolNotFoundError(name) from e

    if "error" in result:
        # tool_executor 把内部错包装成 {"error": "..."} — 转 ToolArgumentError 给 SDK
        raise ToolArgumentError(result["error"])

    return result


# --------------------------------------------------------------------------- #
# 9 tool wrapper — 名字对应 tool_registry 里的 snake_case
# --------------------------------------------------------------------------- #


def forecast(scope: str, name: str, indicator: str, years: int = 5) -> dict[str, Any]:
    """获取某城市/省份某指标的多年预测(含 ensemble + CI + diagnostics 摘要)。"""
    return _invoke("get_forecast", {
        "scope": scope, "name": name, "indicator": indicator, "years": years,
    })


def diagnostics(scope: str, name: str, indicator: str) -> dict[str, Any]:
    """获取某城市某指标的 5 项残差诊断(ADF/KPSS/Ljung-Box/Jarque-Bera/Breusch-Pagan) + verdict。"""
    return _invoke("get_diagnostics", {
        "scope": scope, "name": name, "indicator": indicator,
    })


def backtest(scope: str, name: str, indicator: str) -> dict[str, Any]:
    """获取 walk-forward 交叉验证结果(5 指标:MAPE/RMSE/MASE/sMAPE/Coverage)。"""
    return _invoke("get_backtest", {
        "scope": scope, "name": name, "indicator": indicator,
    })


def risk(scope: str, name: str, indicator: str) -> dict[str, Any]:
    """获取风险指标:VaR/CVaR 95/99、GARCH(1,1) 条件波动率、滚动波动率。"""
    return _invoke("get_risk", {
        "scope": scope, "name": name, "indicator": indicator,
    })


def scenarios(scope: str, name: str, indicator: str, years: int = 5) -> dict[str, Any]:
    """获取 4 档情景预测:baseline/optimistic +10%/pessimistic -10%/recession -25%。"""
    return _invoke("get_scenarios", {
        "scope": scope, "name": name, "indicator": indicator, "years": years,
    })


def monte_carlo(scope: str, name: str, indicator: str, years: int = 5) -> dict[str, Any]:
    """获取 Monte Carlo 1000 次模拟的分位数(P5/P50/P95)。"""
    return _invoke("get_monte_carlo", {
        "scope": scope, "name": name, "indicator": indicator, "years": years,
    })


def data_provenance(name: str) -> dict[str, Any]:
    """获取某城市所有数据点的来源信息(URL/来源/置信度/估算标记/方法学变更)。"""
    return _invoke("get_data_provenance", {"name": name})


def macro_data() -> dict[str, Any]:
    """获取 4 个宏观协变量的当前值和同比:national_gdp/cpi_yoy/lpr_1y/fdi_inflow。"""
    return _invoke("get_macro_data", {})


def list_cities() -> dict[str, Any]:
    """列出系统支持的所有城市和省份。"""
    return _invoke("list_cities", {})
