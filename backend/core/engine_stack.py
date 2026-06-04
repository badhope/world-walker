"""
Engine stack 探测 — runtime 检查可选库是否可用。

设计:
- 启动时各函数只跑一次(模块级变量缓存)
- 失败/未装时返回 False,绝不抛异常
- 上层用 *_available() 判断走高级路径还是 fallback

支持的探测:
- statsforecast (nixtla) — 高速 AutoARIMA + 多季节 + 节假日
- arch (bashtage) — GARCH / EGARCH / GJR 波动率建模
- pmdarima (alkaline-ml) — auto_arima + 季节性 + 平稳检验
- prophet (facebook) — 自动节假日 + 季节性(可选)

典型使用:
    from backend.core.engine_stack import engine_stack, primary_arima_backend
    print(engine_stack())
    if primary_arima_backend() == "statsforecast":
        # 走快路径
        ...
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _try_import(module_name: str, min_version: str | None = None) -> bool:
    """尝试 import + 验版本,失败返回 False。绝不抛异常。"""
    try:
        m = __import__(module_name)
    except Exception as e:
        logger.info("Optional lib %s unavailable: %s", module_name, e)
        return False
    if min_version is None:
        return True
    try:
        from packaging.version import Version

        return Version(getattr(m, "__version__", "0")) >= Version(min_version)
    except Exception:
        # packaging 缺失或版本号奇怪 → 视为可用(避免误判)
        return True


# --------------------------------------------------------------------------- #
# 缓存(模块级,各函数首次调用时探测一次)
# --------------------------------------------------------------------------- #

_STATSFORECAST_OK: bool | None = None
_ARCH_OK: bool | None = None
_PMDARIMA_OK: bool | None = None
_PROPHET_OK: bool | None = None


def statsforecast_available() -> bool:
    """nixtla/statsforecast — 高速 AutoARIMA + 多季节 + 节假日"""
    global _STATSFORECAST_OK
    if _STATSFORECAST_OK is None:
        _STATSFORECAST_OK = _try_import("statsforecast", min_version="1.0.0")
    return _STATSFORECAST_OK


def arch_available() -> bool:
    """bashtage/arch — GARCH / EGARCH / GJR 波动率建模"""
    global _ARCH_OK
    if _ARCH_OK is None:
        _ARCH_OK = _try_import("arch", min_version="5.0.0")
    return _ARCH_OK


def pmdarima_available() -> bool:
    """alkaline-ml/pmdarima — auto_arima + 季节性 + 平稳检验"""
    global _PMDARIMA_OK
    if _PMDARIMA_OK is None:
        _PMDARIMA_OK = _try_import("pmdarima", min_version="2.0.0")
    return _PMDARIMA_OK


def prophet_available() -> bool:
    """facebook/prophet — 自动节假日 + 季节性(可选)"""
    global _PROPHET_OK
    if _PROPHET_OK is None:
        _PROPHET_OK = _try_import("prophet", min_version="1.0.0")
    return _PROPHET_OK


def engine_stack() -> dict[str, bool]:
    """汇总所有探测结果,供 /healthz 和文档报告。

    Returns:
        dict like {"statsforecast": True, "arch": False, "pmdarima": True, "prophet": False}
    """
    return {
        "statsforecast": statsforecast_available(),
        "arch": arch_available(),
        "pmdarima": pmdarima_available(),
        "prophet": prophet_available(),
    }


def primary_arima_backend() -> str:
    """返回当前 auto_arima 应走的引擎名。

    优先级:statsforecast > pmdarima > statsmodels
    """
    if statsforecast_available():
        return "statsforecast"
    if pmdarima_available():
        return "pmdarima"
    return "statsmodels"


def primary_vol_backend() -> str:
    """返回当前 rolling_volatility 应走的引擎名。

    优先级:arch > rolling-std
    """
    if arch_available():
        return "arch-garch"
    return "rolling-std"


def stack_summary() -> dict[str, Any]:
    """扩展版摘要,带 backend 优先级 + 适合前端展示。"""
    return {
        "available": engine_stack(),
        "primary_arima_backend": primary_arima_backend(),
        "primary_vol_backend": primary_vol_backend(),
    }


if __name__ == "__main__":
    # 自检
    import json

    print(json.dumps(stack_summary(), indent=2))
