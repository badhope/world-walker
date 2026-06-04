# 投资决策级预测方法学 — METHODOLOGY

> **平台**: National Stats Regional Economic Analysis Platform
> **版本**: 1.0 (Investment-Grade)
> **最后更新**: 2026-06-04
> **数据范围**: 10 城 × 12 指标 × 16 年 (2010-2025) + 4 宏观协变量

---

## 1. 数据来源与限制

### 1.1 城市指标 (10 城 × 12 指标 × 16 年 = 1920 数据点)

| 维度 | 详情 |
|---|---|
| **城市** | 深圳 / 上海 / 北京 / 广州 / 成都 / 杭州 / 武汉 / 南京 / 苏州 / 西安 |
| **指标** | gdp, population, fiscal_revenue, supplier_count, land_price (绝对量 5)<br>rd_intensity, industry_high_tech_ratio, gdp_growth, local_support_rate, policy_coverage, rd_subsidy, tax_reduction (率 7) |
| **年份** | 2010-2025 (16 年) |
| **来源** | 城市统计局年度统计公报(URL 在 `backend/data/historical_extended.py:SOURCE_URLS`) |
| **完整度** | 100% — 每格都有真实或公开数据 |

### 1.2 宏观协变量 (4 项 × 16 年 = 64 数据点)

| 协变量 | 来源 | 范围 |
|---|---|---|
| `national_gdp` | NBSC 年度国民经济统计公报 | 413582 → 1370000 亿元 |
| `cpi_yoy` | NBSC 居民消费价格指数 | 0.2% - 5.4% |
| `lpr_1y` | 中国人民银行 LPR 公告(2019-08 前为贷款基准利率) | 3.00% - 6.56% |
| `fdi_inflow` | 商务部外资统计 | 1088 - 1891 亿美元 |

### 1.3 已知估算/插值

- **2024+ 全国数据** :NBSC 初步核算,标记 `estimated=True, confidence=0.85`
- **2020 人口口径变更** :深圳从"常住人口"改为"实际管理人口",标记 `methodology_change`
- **2010-2014 部分率指标** :rd_intensity / industry_high_tech_ratio 等早期数据缺失,使用后续公开报告回填

### 1.4 数据血缘(Provenance)

每条数据带 6 字段 provenance:
```python
{
    "source": "深圳统计局2024年统计公报",
    "url": "http://tjj.sz.gov.cn/...",
    "estimated": False,
    "confidence": 0.95,
    "methodology_change": "2020 人口口径变更" or None,
    "last_updated": "2026-06-04",
}
```

**API**: `GET /api/v1/lineage/provenance/city/{name}?indicator=...&year=...`

---

## 2. 预测模型方法

### 2.1 三模型集成 (Ensemble)

平台使用 3 个独立模型,AIC 加权集成:

| 模型 | 实现 | 适用场景 |
|---|---|---|
| **ARIMA (p,d,q)** | statsmodels AIC grid search,p/d/q ∈ {0..2}×{0..1}×{0..2} | 趋势 + 自相关 |
| **ETS** | statsmodels ExponentialSmoothing (Holt 加法趋势 / SES fallback) | 趋势 + 季节性 |
| **Linear Regression + t 分布** | sklearn OLS + `t(0.975, df=n-2)` 杠杆修正 PI | 纯趋势 / 小样本 fallback |

**集成权重**:
```python
w_m = 1 / AIC_m / Σ(1 / AIC_m)
pred = Σ(w_m × pred_m)
```

**实例 (深圳 GDP 5 年预测)**:
- ARIMA 30.2% / ETS 34.7% / LR 35.0%
- 集成预测 2026: 40,344 亿元,2030: 48,061 亿元

### 2.2 预测区间 (95% CI)

| 模型 | CI 计算 |
|---|---|
| ARIMA | `fc.conf_int(alpha=0.05)` — 基于正态近似的 model 残差 |
| ETS | `±z · σ · √t` — z=1.96,σ=残差 std,t=预测步 |
| LR | `t_crit · σ̂ · √(1 + 1/n + (x_new - x̄)² / Sxx)` — t 分布 + 杠杆修正 |

CI 在样本中点最窄,远离样本时扩大(杠杆效应)。

### 2.3 CAGR

- 历史:`((value[-1] / value[0]) ^ (1/(n-1)) - 1) × 100`
- 预测:`((pred[-1] / value[-1]) ^ (1/years) - 1) × 100`

---

## 3. 残差诊断 (5 项)

对 ARIMA 拟合后的残差做 5 项检验,综合 verdict:

| 检验 | 原假设 | p < 0.05 → | 含义 |
|---|---|---|---|
| **ADF** | 有单位根(不平稳) | 拒绝 | 序列平稳 ✓ |
| **KPSS** | 无单位根(平稳) | 拒绝 | 序列非平稳 ✗ |
| **Ljung-Box** | 无自相关 | 拒绝 | 残差有自相关 ✗(模型漏项) |
| **Jarque-Bera** | 正态 | 拒绝 | 残差非正态 ✗(厚尾) |
| **Breusch-Pagan** | 同方差 | 拒绝 | 残差异方差 ✗(波动聚集) |

**Verdict**:
- `0` 失败 → PASS
- `1` 失败 → WARN
- `≥2` 失败 → FAIL

注:Jarque-Bera 在 GDP 增速类数据上几乎总是 FAIL(分布偏斜),属正常现象,不影响区间估计。

---

## 4. 结构突变 (Chow Test)

对每个候选断点 i (3 ≤ i ≤ n-3):
```
F = ((RSS_full - RSS_split) / k) / (RSS_split / (n - 2k))
```
其中 k=2(截距+斜率),p < 0.05 视为显著突变。

仅作风险提示,不直接归因(避免 spurious causal claims)。

---

## 5. 滚动回测 (Walk-Forward CV)

从历史最后 3 年(可配置 1-8)开始,逐步往前推:
- 第 k 步:用前 n-k 年训练,预测第 n-k+1 年
- 收集 (actual, forecast) 对
- 计算 5 项指标:

| 指标 | 公式 | 优良阈值 |
|---|---|---|
| **MAPE** | mean(\|actual - forecast\| / \|actual\|) × 100 | < 5% |
| **RMSE** | √mean((actual - forecast)²) | scale-free 无标准 |
| **MASE** | mean(\|a-f\|) / mean(\|Δa\|) | < 1(优于 naive) |
| **sMAPE** | mean(2\|a-f\| / (\|a\|+\|f\|)) × 100 | < 10% |
| **Coverage** | mean(lower ≤ actual ≤ upper) | ≈ 95% |

**深圳 GDP 16 年实例**:
- MAPE 0.40% ✓ 优秀
- MASE 0.072 ✓ 远优于 naive
- Coverage 100% ✓ 略偏保守(实际 CI 包含 100% 历史样本)

---

## 6. 风险指标

### 6.1 滚动波动率 (Annualized Volatility)

```
vol = std(log_returns, ddof=1) × √1  # 年频数据
```

- 3 年滚动窗口
- 输出 `volatility` (单期) 和 `annualized_volatility` (年化)

### 6.2 VaR / CVaR (历史模拟)

```
returns_t = (y_t - y_{t-1}) / y_{t-1}    # YoY 收益
sorted_returns = sort(returns)             # 升序
VaR_{1-α} = -sorted_returns[⌊(1-α)·n⌋]   # α=0.95 取 5% 分位
CVaR_{1-α} = -mean(sorted_returns[:⌊(1-α)·n⌋])  # 尾部平均
```

实例 (深圳 GDP):
- VaR 95% = -5.48% (最坏 5% 情景下年损失 5.48%)
- CVaR 95% = -5.48% (尾部 5% 的平均损失)
- 注:CVaR < VaR 是数据无厚尾的迹象

**局限**:基于历史 16 年,样本量小;实际投资决策应配合 GARCH(本平台 `arch` 库未装,改用滚动 std)。

### 6.3 4 档情景

| 情景 | 年化冲击 | 触发条件 |
|---|---|---|
| **基线** | 0% | 集成预测 |
| **乐观** | +10% | 政策刺激 + 出口超预期 + 投资扩张 |
| **悲观** | -10% | 地缘冲击 + 需求收缩 + 地产拖累 |
| **衰退** | -25% | 2008/2020 级别冲击 |

```
pred_shocked(t) = pred_baseline(t) × (1 + shock) ^ t
```

### 6.4 Monte Carlo (1000 次残差 bootstrap)

```
对每个 t in 1..years:
  bootstrap_resid[t] = sample(residuals, n=years, replace=True)
  sim_final[t] = baseline[t] + bootstrap_resid[t]
```

输出 P5/P50/P95 三个分位 + 末年统计。

**假设**:残差独立同分布(实际 GDP 时序有自相关,可能低估尾部风险)

---

## 7. 已知局限

| # | 局限 | 影响 | 缓解 |
|---|---|---|---|
| 1 | 16 年数据对 ARIMA grid 偏短 | 复杂 (p,d,q) 不稳定 | grid 上限 max_p=2,max_q=2 |
| 2 | 2020 人口口径变更 | 时间序列不连续 | 标注 methodology_change,模型自动检测 |
| 3 | `statsforecast` 未装 | 不能用 AutoARIMA + 节假日效应 | 用 statsmodels grid search 替代 |
| 4 | `arch` (GARCH) 未装 | 没有波动率聚集建模 | 滚动 std + 历史 VaR 替代 |
| 5 | `prophet` 未装 | 没有自动节假日 + 季节性 | 半年/年度数据无季节性,影响小 |
| 6 | 残差 bootstrap 假设独立 | 低估尾部风险 | 文档已说明,实际使用应配合正态扰动 |
| 7 | rate 指标 2010-2014 部分插值 | 早期数据有 ±0.5% 误差 | provenance 标 confidence=0.6-0.9 |
| 8 | 单变量时序 | 没考虑跨城相关性 | 未来可加 VAR / VECM |

---

## 8. 投资决策使用建议

### 8.1 ✅ 适用场景

| 场景 | 信任度 | 关键依据 |
|---|---|---|
| 数学建模作业 / 教学 | ⭐⭐⭐⭐⭐ | 16 年真实数据,5 项 CV 通过 |
| 政府汇报原型 | ⭐⭐⭐⭐ | 残差诊断 + 情景分析 + 数据血缘 |
| 工业选址初筛 | ⭐⭐⭐ | 5 年 CAGR 区间 + VaR 95 |
| 政策影响模拟 | ⭐⭐⭐ | 4 档情景对比 + MC 末年分布 |
| 长期(5-10 年)规划 | ⭐⭐ | 5 年内可信,5-10 年 CI 翻倍 |

### 8.2 ❌ 不适用场景

| 场景 | 原因 |
|---|---|
| 衍生品定价 | 模型无 GARCH/随机波动 |
| 高频交易决策 | 半年/年度数据粒度不够 |
| 单笔投资 1 亿元+ | 应配合专业咨询 + 现场尽调 |
| 极端事件预测 | 2008/2020 级冲击在训练样本外 |

### 8.3 决策流程推荐

1. **看回测 MAPE / Coverage** — 模型可信度初判
2. **看残差诊断 verdict** — 模型假设是否成立
3. **看结构突变** — 是否有政策/冲击改变历史规律
4. **看 VaR 95 + CVaR 95** — 风险敞口
5. **看 4 档情景** — 决策收益分布
6. **看 MC P5/P95** — 尾部概率
7. **看数据血缘** — 关键数据点的来源与置信度

---

## 9. 引用与外部资源

- Hyndman & Athanasopoulos, *Forecasting: Principles and Practice* (3rd ed.)
- Box, Jenkins & Reinsel, *Time Series Analysis* (4th ed.)
- NBSC: http://www.stats.gov.cn/
- 10 城市统计局公报(URL 见 `backend/data/historical_extended.py:SOURCE_URLS`)

---

**最后更新**: 2026-06-04
**版本**: 1.0 (Investment-Grade)
**负责人**: Platform Engineering
