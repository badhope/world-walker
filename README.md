# Urban Pulse — 城市经济智能分析平台

> **10 个中国主要城市 × 12 项经济指标 × 16 年真实数据**
>
> 一个端到端的数据产品：数据采集 → 清洗 → 时间序列建模 → FastAPI 后端 → ECharts 可视化

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)

---

## 📖 概述

Urban Pulse 是一个**面向中国城市经济的端到端数据分析平台**，覆盖从原始数据采集到决策支持的全链路。

### 为什么做这个项目

中国城市经济数据分散在统计年鉴、政府公报、金融数据库等多个源头。即使拿到数据，如何做可比较的时间序列预测、风险分析和场景推演，也需要一个端到端的工程解决方案。

### 它解决什么问题

- **「这 10 个城市哪个经济增长最快？」** → 16 年真实数据 + 集成预测
- **「这个零售选址值不值得？」** → 客流量/竞品/租金多因子分析
- **「GDP 5 年后会在什么区间？」** → 蒙特卡洛模拟 + VaR 风险量化

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────┐
│  FastAPI (single process, port 8000)                │
├─────────────────────────────────────────────────────┤
│  /dashboard     ECharts Dashboard (SPA)            │
│  /docs          Swagger UI                         │
│  /api/v1/...    REST API (50+ endpoints)           │
│    ├── /cities      城市经济数据                    │
│    ├── /analysis    产业与企业分析                    │
│    ├── /forecast    时间序列预测 / 风险 / 场景        │
│    └── /data        数据管理                         │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│  Core Engine (layered)                              │
│  ┌──────────┐ ┌─────────┐ ┌──────────┐             │
│  │ Forecast │ │ Risk    │ │Scenario  │             │
│  │ ARIMA+ETS│ │ VaR/GARCH│ │MonteCarlo│             │
│  └──────────┘ └─────────┘ └──────────┘             │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│  Data Layer                                         │
│  ┌──────────┐ ┌──────────┐ ┌────────────────────┐  │
│  │Collectors│ │Processors│ │10 cities × 16 years│  │
│  │akshare   │ │cleaner/  │ │20+ indicators      │  │
│  │NBS       │ │validator │ │                    │  │
│  └──────────┘ └──────────┘ └────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端
uvicorn backend.api.main:app --reload --port 8000

# 打开浏览器
# http://localhost:8000/dashboard  ← 可视化面板
# http://localhost:8000/docs        ← API 文档
```

### 数据采集

```bash
# 从 akshare 拉取最新城市经济数据
python -c "from backend.data_collection.nbs_collector import nbs_collector; nbs_collector.collect_all()"
```

---

## 📊 核心功能

### 1. 时间序列预测

- **模型**: ARIMA (statsforecast AutoARIMA / statsmodels grid fallback) + ETS + Ridge 集成
- **加权**: AIC 加权 ensemble
- **诊断**: ADF / KPSS / Ljung-Box / Jarque-Bera / Breusch-Pagan 五项残差检验
- **回测**: 5 指标评估 (MAPE / RMSE / MASE / sMAPE / Coverage)
- **风险**: VaR / CVaR / GARCH(1,1) / 波动率持续性

### 2. 城市对比分析

- 多城市经济指标横向对比
- 产业完备度 / 财政效率评估
- 零售选址多因子分析

### 3. 数据管道

- **采集**: akshare / 国家统计局 / 金融数据 多源集成
- **清洗**: 缺失值处理 / 异常检测 / 一致性校验
- **存储**: YAML + CSV 结构化静态数据集

---

## 📂 项目结构

```
urban-pulse/
├── backend/
│   ├── api/           # FastAPI 路由层
│   │   ├── main.py    # 应用入口
│   │   └── routes/    # 按功能拆分的 API 端点
│   │       ├── cities.py      # 城市数据
│   │       ├── analysis.py    # 分析服务
│   │       ├── forecast.py    # 预测/风险/场景
│   │       └── data.py        # 数据管理
│   ├── core/          # 核心引擎
│   │   ├── forecast_engine.py  # 集成预测
│   │   ├── risk_engine.py      # 风险评估
│   │   ├── engine_stack.py     # 模型降级策略
│   │   └── data_manager.py     # 数据管理
│   ├── analysis/      # 领域分析模块
│   ├── data/          # 城市经济数据集
│   ├── data_collection/  # 数据采集器
│   ├── data_processing/  # 数据清洗/转换
│   ├── models/        # Pydantic 数据模型
│   └── utils/         # 工具函数
├── frontend/
│   └── index.html     # ECharts Dashboard (零构建 SPA)
├── notebooks/         # Jupyter 分析笔记
├── tests/             # 测试套件
├── docs/
│   ├── METHODOLOGY.md # 预测方法论
│   ├── API.md         # API 参考
│   └── ARCHITECTURE.md# 架构文档
├── config/            # 应用配置
├── data/              # 静态数据集 (YAML + CSV)
├── Dockerfile
└── requirements.txt
```

---

## 🧪 测试

```bash
python -m pytest tests -q
# 核心测试通过后查看覆盖率
python -m pytest tests --cov=backend -q
```

---

## 🐳 Docker 部署

```bash
docker build -t urban-pulse .
docker run -p 8000:8000 urban-pulse
```

---

## 🗺️ 覆盖城市

| 城市 | 数据年限 | 指标数 |
|------|---------|-------|
| 北京 | 2010-2025 | 20+ |
| 上海 | 2010-2025 | 20+ |
| 深圳 | 2010-2025 | 20+ |
| 广州 | 2010-2025 | 20+ |
| 成都 | 2010-2025 | 20+ |
| 杭州 | 2010-2025 | 20+ |
| 武汉 | 2010-2025 | 20+ |
| 南京 | 2010-2025 | 20+ |
| 苏州 | 2010-2025 | 20+ |
| 重庆 | 2010-2025 | 20+ |

---

## 📚 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | FastAPI (Pydantic v2, Async) |
| 时间序列 | statsforecast, statsmodels, arch |
| 数据采集 | akshare, requests, BeautifulSoup |
| 数据处理 | pandas, numpy, scipy |
| 可视化 | ECharts 5 (CDN, 零构建) |
| 测试 | pytest, hypothesis |
| 部署 | Docker, uvicorn |
| 数据格式 | YAML, CSV, JSON |

---

## 📜 许可

GPL-3.0-or-later — 详见 [LICENSE](LICENSE)。

---

*Built from 10 Chinese cities × 16 years of real public economic data. Started as a side project, grew into a data product.*
