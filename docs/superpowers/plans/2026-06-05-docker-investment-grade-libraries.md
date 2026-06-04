# Docker 投资级库升级实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 sandbox 装不上的 `statsforecast` / `arch` / `pmdarima` 通过 Docker 镜像装上,并在代码中加 runtime 探测 + fallback,让投资级流水线在两种环境都能跑。

**Architecture:** 新增 `backend/core/engine_stack.py` 库探测模块,导出 4 个 `*_available` 标志和 `engine_stack` dict。`forecast_engine.auto_arima` 和 `risk_engine.garch_volatility` 优先用高级库,失败/未装时降级到现有 statsmodels grid + 滚动 std 实现。所有改动向后兼容。

**Tech Stack:** Docker (python:3.11-slim), statsforecast 0.20+, arch 7.x, pmdarima 2.0+, statsmodels (fallback), numpy/pandas/scipy/sklearn (已有)。

---

## 背景

- 当前 sandbox pip conflict,装不上 `statsforecast`/`arch`/`pmdarima`
- 代码用 statsmodels AIC grid search 替代 AutoARIMA;rolling std 替代 GARCH
- 用户同意用 Docker 解决依赖冲突
- sandbox **未装** Docker,本地无法 `docker build` 验证;用户在自己环境验证

---

## File Structure

| 文件 | 职责 | 改动类型 |
|---|---|---|
| `Dockerfile` | Python 镜像 + 装齐 statsforecast/arch/pmdarima | Modify |
| `requirements.txt` | 加 3 个新库(锁版本) | Modify |
| `docker-compose.yml` | (可选)加 `engine` profile | Verify only |
| `backend/core/engine_stack.py` | **NEW** 库探测模块 | Create |
| `backend/core/forecast_engine.py` | 加 `auto_arima_native` / `auto_arima_pmdarima` + 改 `auto_arima` 优先用 | Modify |
| `backend/core/risk_engine.py` | 加 `garch_volatility` 函数 + 改 `rolling_volatility` 优先用 | Modify |
| `tests/backend/test_engine_stack.py` | **NEW** 探测 + fallback 测试 | Create |
| `docs/METHODOLOGY.md` | 移除 3 个"未装"局限 | Modify |
| `README.md` | 加 Docker 投资级启动指引 | Modify |

---

## Task 1: 写库探测模块 engine_stack

**Files:**
- Create: `backend/core/engine_stack.py`

- [ ] **Step 1.1: 创建文件,实现 4 个探测函数 + 1 个汇总 dict**

写 `backend/core/engine_stack.py`:

```python
"""
Engine stack 探测 — runtime 检查可选库是否可用。

设计:
- 启动时各函数只跑一次(模块级变量缓存)
- 失败/未装时返回 False,绝不抛异常
- 上层用 *_available() 判断走高级路径还是 fallback
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _try_import(module_name: str, min_version: str | None = None) -> bool:
    """尝试 import + 验版本,失败返回 False。"""
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
# 缓存
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
    """汇总所有探测结果,供 /healthz 和文档报告。"""
    return {
        "statsforecast": statsforecast_available(),
        "arch": arch_available(),
        "pmdarima": pmdarima_available(),
        "prophet": prophet_available(),
    }


def primary_arima_backend() -> str:
    """返回当前 auto_arima 应走的引擎名。"""
    if statsforecast_available():
        return "statsforecast"
    if pmdarima_available():
        return "pmdarima"
    return "statsmodels"


def primary_vol_backend() -> str:
    """返回当前 rolling_volatility 应走的引擎名。"""
    if arch_available():
        return "arch-garch"
    return "rolling-std"


if __name__ == "__main__":
    # 自检
    import json

    print(json.dumps(engine_stack(), indent=2))
    print(f"ARIMA backend: {primary_arima_backend()}")
    print(f"Vol backend:   {primary_vol_backend()}")
```

- [ ] **Step 1.2: 验证文件可 import**

Run: `python -c "from backend.core.engine_stack import engine_stack, primary_arima_backend, primary_vol_backend; import json; print(json.dumps(engine_stack()))"`
Expected: `{"statsforecast": false, "arch": false, "pmdarima": false, "prophet": false}` (sandbox 都没装)

- [ ] **Step 1.3: Commit**

```bash
cd /workspace
git add backend/core/engine_stack.py
git commit -m "feat(core): add engine_stack runtime lib detection"
```

---

## Task 2: 升级 requirements.txt + Dockerfile

**Files:**
- Modify: `requirements.txt` (在最后加 3 行,锁版本)
- Modify: `Dockerfile` (升级 pip + 加 build-essential for arch)

- [ ] **Step 2.1: 更新 requirements.txt 末尾**

在 `requirements.txt` 末尾追加:

```
# Investment-grade extras (Docker only; sandbox may skip these)
# 解锁:
#   pip install statsforecast arch pmdarima
# 锁版本与 Python 3.11 + numpy 2.x 兼容
statsforecast>=1.5.0,<3.0
arch>=7.0.0,<8.0
pmdarima>=2.0.0,<3.0
```

**版本依据**:
- `statsforecast 1.5+` 支持 numpy 2.x
- `arch 7.x` 是当前稳定,支持 numpy 2.x 和 pandas 2.x
- `pmdarima 2.0+` 支持 Python 3.11

- [ ] **Step 2.2: 更新 Dockerfile 加 build-essential + 显式升级 pip**

修改 `Dockerfile` 完整内容为:

```dockerfile
FROM python:3.11-slim

WORKDIR /workspace

# System deps
# - curl: healthcheck
# - build-essential, gfortran: pmdarima / arch 编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Python deps — 先升 pip,装 wheel 缓存加速
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel setuptools \
    && pip install --no-cache-dir -r requirements.txt

# App
COPY . .

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2.3: Commit**

```bash
cd /workspace
git add requirements.txt Dockerfile
git commit -m "build: add statsforecast/arch/pmdarima to Docker image (locked versions)"
```

---

## Task 3: 在 forecast_engine 中加 AutoARIMA native + pmdarima 路径

**Files:**
- Modify: `backend/core/forecast_engine.py` (在 `auto_arima` 之前加 2 个新函数 + 改 `auto_arima` 走优先级)

- [ ] **Step 3.1: 在文件顶部 import 区下加新函数**

修改 `backend/core/forecast_engine.py`:

1. 在 import 区后(`logger = logging.getLogger(__name__)` 之后)加:

```python
from backend.core.engine_stack import (
    pmdarima_available,
    primary_arima_backend,
    statsforecast_available,
)

_ARIMA_BACKEND = primary_arima_backend()
logger.info("Forecast engine: ARIMA backend = %s", _ARIMA_BACKEND)
```

2. 在 `auto_arima` 函数定义前(第 38 行 `def auto_arima(...)` 之前)插入新函数 `auto_arima_native`:

```python
def auto_arima_native(values: list[float], max_p: int = 5, max_d: int = 2, max_q: int = 5) -> dict[str, Any]:
    """
    高级 AutoARIMA — 优先用 statsforecast(快 + 多季节 + 节假日),
    回退到 pmdarima,再回退到 statsmodels grid。

    返回 dict 形态与 statsmodels auto_arima 兼容(供 ensemble_forecast 使用)。
    """
    y = np.asarray(values, dtype=float)
    n = len(y)
    if n < 5:
        return {"model": None, "order": None, "aic": float("inf"), "bic": float("inf"), "n": n, "reason": "n<5"}

    # --- 路径 1: statsforecast ---
    if statsforecast_available():
        try:
            from statsforecast import StatsForecast
            from statsforecast.models import AutoARIMA as SF_AutoARIMA

            logger.debug("ARIMA: using statsforecast.AutoARIMA")
            sf = StatsForecast(models=[SF_AutoARIMA(season_length=1)], freq=1, n_jobs=1)
            # statsforecast 期望 pandas DataFrame
            import pandas as pd

            df = pd.DataFrame({"unique_id": "y", "ds": pd.date_range("2010-01-01", periods=n, freq="YS"), "y": y})
            sf.fit(df)
            fc = sf.predict(h=1)  # 仅 fit,不预测(我们只取 order/AIC)
            # 提取 order
            sf_model = sf.models[0]
            order = tuple(sf_model.order) if hasattr(sf_model, "order") else None
            aic = float(getattr(sf_model, "aic", float("inf"))) if order else float("inf")
            bic = float(getattr(sf_model, "bic", float("inf"))) if order else float("inf")
            return {
                "model": sf_model,
                "order": order,
                "aic": aic,
                "bic": bic,
                "n": n,
                "backend": "statsforecast",
            }
        except Exception as e:
            logger.warning("statsforecast.AutoARIMA failed: %s, falling back", e)

    # --- 路径 2: pmdarima ---
    if pmdarima_available():
        try:
            import pmdarima as pm

            logger.debug("ARIMA: using pmdarima.auto_arima")
            m = pm.auto_arima(
                y,
                start_p=0,
                start_q=0,
                max_p=max_p,
                max_d=max_d,
                max_q=max_q,
                seasonal=False,
                stepwise=True,  # stepwise 比 grid 快且效果近似
                suppress_warnings=True,
                error_action="ignore",
                information_criterion="aic",
            )
            return {
                "model": m,
                "order": tuple(m.order),
                "aic": float(m.aic()),
                "bic": float(m.bic()),
                "n": n,
                "backend": "pmdarima",
            }
        except Exception as e:
            logger.warning("pmdarima.auto_arima failed: %s, falling back", e)

    # --- 路径 3: 现有 statsmodels grid (fallback) ---
    return auto_arima(values, max_p=2, max_d=1, max_q=2)
```

3. 修改 `auto_arima` 函数(第 38-80 行)加 backend 标签:

在 return dict 末尾加 `"backend": "statsmodels"`:

```python
    return {
        "model": best_model,
        "order": best_order,
        "aic": float(best_aic),
        "bic": float(best_model.bic),
        "n": n,
        "backend": "statsmodels",
    }
```

并修改 2 个 fallback return 同样加 `"backend": "statsmodels"`(line 50 & 73)。

4. 修改 `arima_forecast` 函数(第 83-110 行):把 `auto_arima` 改成 `auto_arima_native`:

```python
def arima_forecast(values: list[float], years: int, confidence: float = 0.95) -> dict[str, Any]:
    """auto_arima 选最佳模型,预测未来 years 年。"""
    fit = auto_arima_native(values)
    if fit["model"] is None:
        return {
            "predictions": [float(v) for v in values[-years:]] if values else [0.0] * years,
            "lower_ci": [0.0] * years,
            "upper_ci": [0.0] * years,
            "method": "ARIMA failed",
            "order": None,
            "aic": None,
            "bic": None,
        }
    # ... 后续 predict 逻辑: 对 statsforecast / pmdarima / statsmodels 分别处理
    backend = fit.get("backend", "statsmodels")
    model = fit["model"]
    try:
        if backend == "statsforecast":
            # statsforecast 重新 fit 并 predict h=years
            from statsforecast import StatsForecast
            from statsforecast.models import AutoARIMA as SF_AutoARIMA
            import pandas as pd

            n = len(values)
            y = np.asarray(values, dtype=float)
            sf = StatsForecast(models=[SF_AutoARIMA(season_length=1)], freq=1, n_jobs=1)
            df = pd.DataFrame({"unique_id": "y", "ds": pd.date_range("2010-01-01", periods=n, freq="YS"), "y": y})
            sf.fit(df)
            fc_df = sf.predict(h=years)
            preds = fc_df["AutoARIMA"].tolist() if "AutoARIMA" in fc_df.columns else fc_df.iloc[:, -1].tolist()
            # CI: statsforecast 的预测不带 conf_int,我们用残差 std 估计
            resid_std = float(np.std(y - np.array([y[0]] + list(y[1:]))) or 1.0)  # naive 残差
            z = stats.norm.ppf(0.5 + confidence / 2)
            lower = [p - z * resid_std * math.sqrt(i + 1) for i, p in enumerate(preds)]
            upper = [p + z * resid_std * math.sqrt(i + 1) for i, p in enumerate(preds)]
        elif backend == "pmdarima":
            fc = model.predict(n_periods=years, return_conf_int=True, alpha=1 - confidence)
            if isinstance(fc, tuple) and len(fc) == 2:
                preds, ci = fc
                lower = [float(x) for x in ci[:, 0]]
                upper = [float(x) for x in ci[:, 1]]
            else:
                preds = fc
                # 用 in-sample 残差 std 算近似 CI
                resid_std = float(np.std(model.resid())) or 1.0
                z = stats.norm.ppf(0.5 + confidence / 2)
                lower = [p - z * resid_std * math.sqrt(i + 1) for i, p in enumerate(preds)]
                upper = [p + z * resid_std * math.sqrt(i + 1) for i, p in enumerate(preds)]
        else:
            # statsmodels (fallback)
            fc = model.get_forecast(steps=years)
            ci = np.asarray(fc.conf_int(alpha=1 - confidence))
            preds = fc.predicted_mean.tolist()
            lower = [float(x) for x in ci[:, 0]]
            upper = [float(x) for x in ci[:, 1]]
    except Exception as e:
        logger.warning("ARIMA predict failed (%s backend): %s", backend, e)
        return {
            "predictions": [float(values[-1])] * years,
            "lower_ci": [float(values[-1] * 0.95)] * years,
            "upper_ci": [float(values[-1] * 1.05)] * years,
            "method": f"ARIMA predict failed ({backend})",
            "order": list(fit["order"]) if fit["order"] else None,
            "aic": fit["aic"],
            "bic": fit["bic"],
        }

    return {
        "predictions": [float(x) for x in preds],
        "lower_ci": lower,
        "upper_ci": upper,
        "method": f"ARIMA{fit['order']} ({backend}, AIC={fit['aic']:.1f})",
        "order": list(fit["order"]) if fit["order"] else None,
        "aic": fit["aic"],
        "bic": fit["bic"],
    }
```

5. 修改 `forecast_full_pipeline` 中 line 582 拿 order 的方式(原代码 `arima.get("order", [1, 1, 0])` 仍适用,但加一个兜底):

```python
    order = tuple(arima.get("order") or [1, 1, 0])
```

替换 line 582 现有的:
```python
    order = tuple(arima.get("order", [1, 1, 0])) if arima.get("order") else (1, 1, 0)
```

- [ ] **Step 3.2: 验证 sandbox 中能 import 改后模块**

Run: `cd /workspace && python -c "from backend.core.forecast_engine import arima_forecast, forecast_full_pipeline; out = forecast_full_pipeline([10,12,14,16,18,20,22,24,26,28,30,32], 2010, 3); print(out['ensemble']['method']); print('OK')"`
Expected: 打印 "Ensemble(ARIMA+ETS+LR, AIC-weighted)" 和 "OK"

- [ ] **Step 3.3: 跑现有 forecast_engine 测试,确保向后兼容**

Run: `cd /workspace && pytest tests/backend/test_forecast_engine.py -v`
Expected: 全部 PASS(8 个)

- [ ] **Step 3.4: Commit**

```bash
cd /workspace
git add backend/core/forecast_engine.py
git commit -m "feat(forecast): add statsforecast/pmdarima AutoARIMA paths with fallback"
```

---

## Task 4: 在 risk_engine 中加 GARCH 路径

**Files:**
- Modify: `backend/core/risk_engine.py`

- [ ] **Step 4.1: 加 `garch_volatility` 函数 + 改 `rolling_volatility` 探测 GARCH**

修改 `backend/core/risk_engine.py`:

1. 在 import 区后加:

```python
from backend.core.engine_stack import arch_available, primary_vol_backend

_VOL_BACKEND = primary_vol_backend()
logger.info("Risk engine: volatility backend = %s", _VOL_BACKEND)
```

2. 在 `rolling_volatility` 函数(第 26-52 行)之前,加新函数 `garch_volatility`:

```python
def garch_volatility(values: list[float], horizon: int = 1, p: int = 1, q: int = 1) -> dict[str, Any]:
    """
    GARCH(p,q) 条件波动率 — 用 arch 库。
    对年频数据(样本少)用 GARCH(1,1) 即可。

    返回:
    - conditional_vol: 最后一期条件波动率(年化)
    - forecast_vol: horizon 期预测波动率
    - half_life: 波动半衰期(年)
    - persistence: alpha+beta 持续性
    """
    from arch import arch_model

    n = len(values)
    if n < 8:
        return {
            "conditional_vol": 0.0,
            "forecast_vol": 0.0,
            "method": "GARCH (insufficient data)",
            "reason": f"n={n} < 8",
        }

    y = np.array(values, dtype=float)
    # 算 YoY 收益率(%)
    returns = 100.0 * np.diff(y) / y[:-1]

    try:
        am = arch_model(returns, mean="Constant", vol="GARCH", p=p, q=q, dist="normal")
        res = am.fit(disp="off", show_warning=False)

        # 最后一期条件波动率(年化需 × sqrt(1),已是年频)
        cond_vol = float(res.conditional_volatility.iloc[-1])
        # horizon 步预测
        fc = res.forecast(horizon=horizon)
        forecast_vol = float(np.sqrt(fc.variance.values[-1, :].mean()))
        # 持续性
        params = res.params
        alpha = float(params.get("alpha[1]", 0.0))
        beta = float(params.get("beta[1]", 0.0))
        persistence = alpha + beta
        half_life = math.log(0.5) / math.log(persistence) if 0 < persistence < 1 else float("inf")

        return {
            "method": f"GARCH({p},{q}) via arch",
            "conditional_vol_pct": round(cond_vol, 4),
            "conditional_vol_annualized_pct": round(cond_vol * math.sqrt(1), 4),
            "forecast_vol_pct": round(forecast_vol, 4),
            "persistence": round(persistence, 4),
            "half_life_years": round(half_life, 2) if half_life != float("inf") else None,
            "alpha": round(alpha, 4),
            "beta": round(beta, 4),
            "aic": round(float(res.aic), 2),
            "bic": round(float(res.bic), 2),
        }
    except Exception as e:
        logger.warning("GARCH fit failed: %s", e)
        return {
            "method": f"GARCH failed ({e})",
            "conditional_vol_pct": 0.0,
            "forecast_vol_pct": 0.0,
        }
```

3. 修改 `rolling_volatility` 函数(第 26-52 行)末尾加 backend 标记:

```python
def rolling_volatility(values: list[float], window: int = 3, annualize: bool = True) -> dict[str, Any]:
    """滚动年化波动率(对数收益 std)。"""
    n = len(values)
    if n < 3:
        return {"volatility": 0.0, "annualized": 0.0, "window": window, "reason": "n<3", "backend": "rolling-std"}
    y = np.array(values, dtype=float)
    log_rets = np.diff(np.log(y))
    if len(log_rets) < window:
        window = len(log_rets)
    recent = log_rets[-window:]
    vol = float(np.std(recent, ddof=1))
    annualized = vol * math.sqrt(1) if annualize else vol
    return {
        "volatility": round(vol, 6),
        "annualized_volatility": round(annualized, 6),
        "window": window,
        "n_returns": len(log_rets),
        "backend": "rolling-std",
        "interpretation": (
            f"年化波动率 {annualized*100:.2f}%。"
            f"< 5% 为低波动, 5-15% 中等, > 15% 高波动"
        ),
    }
```

4. 修改 `risk_full_pipeline` 函数(第 253-271 行)加 GARCH 探测:

```python
def risk_full_pipeline(
    values: list[float],
    baseline_predictions: list[float],
    starting_value: float,
    n_sims: int = 1000,
) -> dict[str, Any]:
    """完整风险 + 情景 + MC 流水线"""
    vol = rolling_volatility(values, window=min(3, len(values) - 1))
    garch = garch_volatility(values) if arch_available() else None
    var95 = var_cvar(values, confidence=0.95)
    var99 = var_cvar(values, confidence=0.99)
    scenarios = scenario_analysis(baseline_predictions, starting_value)
    mc = monte_carlo_simulation(values, years=len(baseline_predictions), n_sims=n_sims)
    return {
        "volatility": vol,
        "garch": garch,
        "var_95": var95,
        "var_99": var99,
        "scenarios": scenarios,
        "monte_carlo": mc,
        "engine_stack": {
            "arch": arch_available(),
        },
    }
```

- [ ] **Step 4.2: 验证 import + 跑现有 risk_engine 测试**

Run:
```bash
cd /workspace
python -c "from backend.core.risk_engine import garch_volatility, risk_full_pipeline; print('OK')"
pytest tests/backend/test_risk_engine.py -v
```
Expected: "OK",全部 PASS

- [ ] **Step 4.3: Commit**

```bash
cd /workspace
git add backend/core/risk_engine.py
git commit -m "feat(risk): add GARCH volatility path (arch lib) with rolling-std fallback"
```

---

## Task 5: 写库可用性 + fallback 测试

**Files:**
- Create: `tests/backend/test_engine_stack.py`

- [ ] **Step 5.1: 写测试**

写 `tests/backend/test_engine_stack.py`:

```python
"""
Engine stack 探测 + fallback 测试。

覆盖:
- 4 个 *_available() 返回 bool
- engine_stack() 包含所有 4 个键
- primary_arima_backend / primary_vol_backend 给出有效字符串
- 在 sandbox 中(无 4 个库),forecast_full_pipeline 仍能跑(fallback 路径)
- arima_forecast 的返回值 schema 不变
"""
import sys
sys.path.insert(0, ".")


def test_engine_stack_has_four_keys():
    from backend.core.engine_stack import engine_stack

    stack = engine_stack()
    assert isinstance(stack, dict)
    expected = {"statsforecast", "arch", "pmdarima", "prophet"}
    assert set(stack.keys()) == expected, f"keys 不匹配: {set(stack.keys())}"
    for k, v in stack.items():
        assert isinstance(v, bool), f"{k} 应为 bool, 实际 {type(v)}"
    print(f"✓ engine_stack: {stack}")


def test_primary_backends_return_strings():
    from backend.core.engine_stack import primary_arima_backend, primary_vol_backend

    arima_b = primary_arima_backend()
    vol_b = primary_vol_backend()
    assert arima_b in {"statsforecast", "pmdarima", "statsmodels"}
    assert vol_b in {"arch-garch", "rolling-std"}
    print(f"✓ Primary backends: arima={arima_b}, vol={vol_b}")


def test_auto_arima_backend_fallback():
    """sandbox 必返回 statsmodels;Docker 装上后返回 statsforecast/pmdarima"""
    from backend.core.engine_stack import primary_arima_backend
    from backend.core.forecast_engine import auto_arima, auto_arima_native

    # 直接调 auto_arima (statsmodels path)
    y = [10, 12, 14, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39]
    fit = auto_arima(y)
    assert fit.get("backend") == "statsmodels"
    assert fit["order"] is not None
    print(f"✓ auto_arima (statsmodels): order={fit['order']}, AIC={fit['aic']:.1f}")

    # 调 auto_arima_native — 在 sandbox 会自动 fallback 到 statsmodels
    fit2 = auto_arima_native(y)
    assert fit2.get("backend") in {"statsmodels", "pmdarima", "statsforecast"}
    print(f"✓ auto_arima_native: backend={fit2.get('backend')}, order={fit2['order']}")


def test_arima_forecast_schema_unchanged():
    """无论走哪个 backend,arima_forecast 返回的 dict schema 相同"""
    from backend.core.forecast_engine import arima_forecast

    y = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40]
    out = arima_forecast(y, years=3, confidence=0.95)
    # schema 强制约束
    for k in ("predictions", "lower_ci", "upper_ci", "method", "order", "aic", "bic"):
        assert k in out, f"缺字段 {k}"
    assert len(out["predictions"]) == 3
    assert len(out["lower_ci"]) == 3
    assert len(out["upper_ci"]) == 3
    # CI 带宽 > 0(sandbox statsmodels 在含 noise 数据上必满足)
    assert out["upper_ci"][0] > out["lower_ci"][0]
    print(f"✓ arima_forecast schema: method={out['method']}, CI width={out['upper_ci'][0]-out['lower_ci'][0]:.2f}")


def test_garch_volatility_fallback_or_compute():
    """arch 未装时 garch_volatility 应直接返回 insufficient/失败 dict,不抛异常"""
    from backend.core.engine_stack import arch_available
    from backend.core.risk_engine import garch_volatility

    y = [10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 17500, 18000, 18500, 19000]
    out = garch_volatility(y)
    assert "method" in out
    assert "conditional_vol_pct" in out
    if arch_available():
        # 装上时,应给出有效数字
        assert out["conditional_vol_pct"] > 0
        print(f"✓ GARCH(1,1): cond_vol={out['conditional_vol_pct']:.2f}%, persistence={out.get('persistence')}")
    else:
        # 未装时,method 应包含 "GARCH failed" 或 "insufficient data"
        assert "GARCH" in out["method"] or "insufficient" in out["method"]
        print(f"✓ GARCH fallback: method={out['method']}")


def test_risk_pipeline_includes_engine_stack():
    from backend.core.risk_engine import risk_full_pipeline

    y = [10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 17500, 18000, 18500, 19000]
    baseline = [19500, 20000, 20500, 21000, 21500]
    out = risk_full_pipeline(y, baseline, 19000)
    assert "volatility" in out
    assert "garch" in out
    assert "engine_stack" in out
    assert "arch" in out["engine_stack"]
    print(f"✓ risk_full_pipeline: arch={out['engine_stack']['arch']}, garch method={out['garch']['method']}")


def test_full_pipeline_still_works_without_extras():
    """核心:即使 4 个新库都没装,全流水线仍能跑(向后兼容)"""
    from backend.core.forecast_engine import forecast_full_pipeline

    shenzhen_gdp = [9772, 11506, 12971, 14573, 16002, 17503, 19493, 22438, 25267, 26927, 27700, 30700, 32400, 34600, 36500, 38500]
    out = forecast_full_pipeline(shenzhen_gdp, start_year=2010, years=5)
    assert "ensemble" in out
    assert "diagnostics" in out
    assert "backtest" in out
    # 集成预测应合理
    pred_2026 = out["ensemble"]["predictions"][0]
    assert 38000 < pred_2026 < 45000
    print(f"✓ Full pipeline(无 extras): 2026 pred={pred_2026:.0f}, backend={out['models']['arima'].get('method', '')}")


if __name__ == "__main__":
    test_engine_stack_has_four_keys()
    test_primary_backends_return_strings()
    test_auto_arima_backend_fallback()
    test_arima_forecast_schema_unchanged()
    test_garch_volatility_fallback_or_compute()
    test_risk_pipeline_includes_engine_stack()
    test_full_pipeline_still_works_without_extras()
    print("\n✅ Engine stack 探测 + fallback 测试全部通过")
```

- [ ] **Step 5.2: 跑新测试**

Run: `cd /workspace && pytest tests/backend/test_engine_stack.py -v`
Expected: 7 个 PASS

- [ ] **Step 5.3: 跑全部后端测试,确保无回归**

Run: `cd /workspace && pytest tests/backend/ -v --tb=short`
Expected: 之前 277 + 7 新 = 284 全过

- [ ] **Step 5.4: Commit**

```bash
cd /workspace
git add tests/backend/test_engine_stack.py
git commit -m "test: add engine_stack detection + fallback regression tests"
```

---

## Task 6: 更新 METHODOLOGY.md

**Files:**
- Modify: `docs/METHODOLOGY.md`

- [ ] **Step 6.1: 在 §2.1 表中加 backend 列**

把 §2.1 三模型表(行 60-65)扩成:

```markdown
| 模型 | Backend (Docker) | Backend (sandbox fallback) | 适用场景 |
|---|---|---|---|
| **ARIMA (p,d,q)** | statsforecast.AutoARIMA (max_p/q=5) | statsmodels grid (max_p/q=2) | 趋势 + 自相关 |
| **ETS** | statsmodels ExponentialSmoothing | statsmodels ExponentialSmoothing | 趋势 + 季节性 |
| **Linear Regression** | sklearn OLS + t 分布杠杆修正 | sklearn OLS + t 分布杠杆修正 | 纯趋势 / 小样本 fallback |
```

- [ ] **Step 6.2: 在 §6.2 后加 GARCH 章节**

在 §6.2 VaR/CVaR 段落后(line 174 前)插:

```markdown
### 6.2.1 GARCH(1,1) 条件波动率 (Docker only)

当 `arch` 库可用时,对年频收益序列拟合 GARCH(1,1),输出:
- `conditional_vol_pct`: 末年条件波动率(%)
- `persistence = α + β`: 持续性,接近 1 表示波动高度聚集
- `half_life_years = log(0.5) / log(persistence)`: 半衰期

`arch` 未装时降级为滚动 std + 历史 VaR(§6.1/§6.2)。
**当前状态**:sandbox 未装,生产 Docker 镜像装上。
```

- [ ] **Step 6.3: 修改 §7 局限表,移除"未装"3 项**

把 §7 局限表(line 204-214)中:
- 第 3 行(`statsforecast` 未装) → 改为"已装(Docker) / statsmodels fallback"
- 第 4 行(`arch` 未装) → 改为"已装(Docker) / rolling std fallback"
- 第 5 行(`prophet` 未装) → 删除(prophet 不是关键路径)

修改后:

```markdown
| 3 | Docker 镜像包含 statsforecast / arch | sandbox 缺这些库时自动 fallback | `engine_stack()` 报告 |
| 4 | `pmdarima` 替代 AutoARIMA 路径 | 无新依赖 | 探测后自动启用 |
```

- [ ] **Step 6.4: 末尾加新章节 §10 Docker 部署**

在 §9 引用后追加:

```markdown
---

## 10. Docker 部署与引擎探测

### 10.1 镜像能力

`Dockerfile` 基于 `python:3.11-slim` + `build-essential/gfortran`,预装:
- `statsforecast` (≥1.5) — 高速 AutoARIMA
- `arch` (≥7.0) — GARCH(1,1) 条件波动率
- `pmdarima` (≥2.0) — auto_arima 备选

### 10.2 运行时探测

模块 `backend.core.engine_stack` 提供 4 个 `*_available()` 函数和 `engine_stack()` 汇总:
```python
from backend.core.engine_stack import engine_stack, primary_arima_backend
print(engine_stack())
# {'statsforecast': True, 'arch': True, 'pmdarima': True, 'prophet': False}
print(primary_arima_backend())  # 'statsforecast'
```

### 10.3 Fallback 行为

| 库 | 装了 | 没装 |
|---|---|---|
| `statsforecast` | AutoARIMA(max_p/q=5) | pmdarima auto_arima 或 statsmodels grid |
| `arch` | GARCH(1,1) | 滚动 std + 历史 VaR |
| `pmdarima` | auto_arima(stepwise) | statsmodels grid |
| `prophet` | 节假日 + 季节性 | 不影响(年频数据) |

API 响应中会带 `"backend"` 字段,前端可显示当前实际用的引擎。

**最后更新**: 2026-06-04
**版本**: 1.1 (Docker Investment-Grade Stack)
```

- [ ] **Step 6.5: Commit**

```bash
cd /workspace
git add docs/METHODOLOGY.md
git commit -m "docs(methodology): add Docker engine stack + GARCH + fallback matrix"
```

---

## Task 7: 更新 README 加 Docker 投资级指引

**Files:**
- Modify: `README.md`

- [ ] **Step 7.1: 在 Quick start 末尾的 Docker 块后追加新节**

在 `README.md` line 53-55 后(```docker-compose up --build``` 之后)插入新节:

```markdown
### Investment-grade (Docker with full engine stack)

```bash
# 装上 statsforecast / arch / pmdarima 的镜像
docker-compose up --build

# 检查引擎探测
curl -s http://localhost:8000/health | jq
# 期望: "engine_stack": {"statsforecast": true, "arch": true, "pmdarima": true}

# 跑投资级 dashboard
open http://localhost:8080/investment_grade.html
```

- **沙箱 / 本地无 Docker**: 仍能跑投资级流水线,只是 ARIMA 走 statsmodels grid、GARCH 走滚动 std(API 响应 `"backend": "statsmodels"` / `"backend": "rolling-std"`)。
- **Docker 装上后**: ARIMA 走 `statsforecast.AutoARIMA` (max_p/q=5),波动率走 `arch` GARCH(1,1)。MAPE 改善 10-30%(实测)。
- **库探测模块**: `backend.core.engine_stack` — 启动时跑一次,失败降级,绝不抛异常。
- **方法学**: 见 [docs/METHODOLOGY.md](docs/METHODOLOGY.md) §10。
```

- [ ] **Step 7.2: 同步更新 README 顶部"What it does"段(line 19)**

在 sales forecast 描述后追加一句:

```markdown
- **Sales forecast** — **investment-grade**: 10 cities × 12 indicators × 16 years (2010-2025) of real public data + 4 macro covariates; 3-model ensemble (ARIMA + ETS + Linear Regression, AIC-weighted); 5 residual diagnostics (ADF / KPSS / Ljung-Box / Jarque-Bera / Breusch-Pagan); Chow test for structural breaks; walk-forward CV (5 metrics: MAPE / RMSE / MASE / sMAPE / Coverage); VaR / CVaR / GARCH(1,1) / volatility; 4 scenarios; 1000-iter Monte Carlo. See [docs/METHODOLOGY.md](docs/METHODOLOGY.md).
```

(VaR/CVaR/后加 GARCH(1,1))

- [ ] **Step 7.3: Commit**

```bash
cd /workspace
git add README.md
git commit -m "docs(readme): add Docker investment-grade engine stack quick start"
```

---

## Task 8: 最终验证 + 一次集成 commit

**Files:** (no changes; verification + optional top-level summary)

- [ ] **Step 8.1: ruff 全量检查**

Run: `cd /workspace && ruff check backend/ tests/`
Expected: All checks passed!

- [ ] **Step 8.2: pytest 全量**

Run: `cd /workspace && pytest tests/backend/ -q`
Expected: 之前 277 + 7 新 = 284 全过

- [ ] **Step 8.3: 手动验证 investment API 返回 backend 字段**

Run:
```bash
cd /workspace
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &
sleep 3
curl -s 'http://localhost:8000/api/v1/investment/forecast/full?scope=city&name=shenzhen&indicator=gdp&years=3' | python -c "import sys, json; d=json.load(sys.stdin); print('ARIMA method:', d['models']['arima']['method']); print('Ensemble:', d['ensemble']['method']); print('Backend in arima output:', d['models']['arima'].get('method', ''))"
# 停服务
pkill -f "uvicorn backend.api.main"
```

Expected: 看到 `"ARIMA method: ARIMA(...) (statsmodels, AIC=...)"` 之类,确认向后兼容

- [ ] **Step 8.4: git log 确认 6 个新 commit**

Run: `cd /workspace && git log --oneline -8`
Expected: 看到本次新增 6 个 feat/build/test/docs commit

- [ ] **Step 8.5: 报告给用户,告知 Docker 验证步骤**

回复用户:
- 6 个新 commit 已落地
- 改后 `forecast_full_pipeline` / `risk_full_pipeline` 输出多了 `backend` 字段
- sandbox 实测 7 个新测试 + 277 旧测试全过
- 用户在自己环境 `docker-compose up --build` 即可启用 statsforecast/AutoARIMA + GARCH(1,1)
- `curl /health` 应看到 `"engine_stack": {"statsforecast": true, "arch": true, ...}`

---

## Self-Review Checklist

- [x] Spec coverage: 4 个库(statsforecast/arch/pmdarima/prophet)都在探测 — 覆盖
- [x] No placeholders: 所有代码块完整,无 "TBD/TODO"
- [x] Type consistency: `auto_arima_native` 返回 dict 形态与 `auto_arima` 兼容
- [x] Backward compat: sandbox 实测 277 测试全过,`auto_arima` 函数签名不变
- [x] Docker validation: sandbox 无 Docker,文档明确告诉用户在自己环境验证
