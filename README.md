# National Stats — 国家经济数据分析平台

**多场景产业经济智能分析与预测系统**

支持零售门店选址、销售预测、企业营商环境评估、政府产业政策分析四个垂直场景，覆盖 8 个中国主要城市，提供 REST API + Vue 3 交互式前端。

---

## 技术定位

| 维度 | 说明 |
|------|------|
| **项目类型** | 全栈数据科学平台（后端 Python + 前端 Vue 3） |
| **核心能力** | 多场景分析器、ML 模型训练/调优/版本管理、多格式报告生成 |
| **安全等级** | JWT 认证、HMAC 模型签名、AST 安全表达式求值 |
| **质量保证** | 159 个 pytest 用例、vue-tsc 类型检查、GitHub Actions CI/CD |

---

## 系统架构

```
┌──────────────────────────────────────────────┐
│                 Vue 3 前端                    │
│  Enterprise / Government / CityComparison    │
│  Element Plus + ECharts + Pinia              │
└──────────────────┬───────────────────────────┘
                   │ HTTP/WebSocket
┌──────────────────┴───────────────────────────┐
│              FastAPI 后端 (8001)              │
│  Auth (JWT) / Cities / Analysis / Forecast   │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────┴───────────────────────────┐
│              分析引擎层                        │
│  ┌──────────┐ ┌───────────┐ ┌─────────────┐  │
│  │ Retail   │ │ Sales     │ │ Enterprise  │  │
│  │ Location │ │ Forecast  │ │ Analyzer    │  │
│  └──────────┘ └───────────┘ └─────────────┘  │
│  ┌──────────┐ ┌───────────┐ ┌─────────────┐  │
│  │ Gov      │ │ ML Core   │ │ Report Gen  │  │
│  │ Analyzer │ │ (Models)  │ │ (PDF/Excel) │  │
│  └──────────┘ └───────────┘ └─────────────┘  │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────┴───────────────────────────┐
│              数据层                            │
│  8城市经济指标 / 历史时序 / 评分基准 / 统计年鉴 │
└──────────────────────────────────────────────┘
```

---

## 四个垂直场景

### 1. 零售门店选址分析
- 基于流量、竞品、租金等特征预测门店营收
- RandomForest/GBM 模型 + GridSearchCV 超参数调优
- 嵌套交叉验证防数据泄漏

### 2. 销售预测
- 时序特征工程 + 多模型对比
- StatsForecast AutoARIMA 真实预测（非硬编码假数据）
- 预测结果可视化 + 置信区间

### 3. 企业营商环境评估（企业端）
- 营商成本 / 供应链配套 / 政策红利 三维度评分
- 基于 8 城市统计分位数基准的动态评分
- 城市对比排序 + 针对性建议

### 4. 政府产业政策分析（政府端）
- 财政杠杆 / 产业带动 / 产业链完整性 三维度
- 投入产出分析 + 产业链瓶颈识别
- 政策建议自动生成

---

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行完整演示
python demo_complete.py

# 启动 API 服务
uvicorn backend.api.main:app --host 0.0.0.0 --port 8001

# 启动前端开发服务器
cd frontend && npm install && npm run dev
```

---

## 项目结构

```
/workspace/
├── backend/
│   ├── api/                  # FastAPI 路由 + JWT 认证
│   │   ├── main.py
│   │   ├── auth.py
│   │   └── routes/           # cities, analysis, forecast, interactive
│   ├── analysis/             # 分析器引擎
│   │   ├── base_analyzer.py  # 抽象基类（统一接口）
│   │   ├── enterprise_analyzer.py
│   │   ├── government_analyzer.py
│   │   └── custom_indicators.py
│   ├── retail_location/      # 零售选址场景
│   │   ├── analyzer.py
│   │   ├── model_trainer.py
│   │   └── visualizer.py
│   ├── sales_forecast/       # 销售预测场景
│   │   ├── analyzer.py
│   │   ├── model_trainer.py
│   │   └── visualizer.py
│   ├── ml/                   # 通用 ML 层（9 种模型）
│   ├── data/                 # 城市经济数据（8 城市）
│   ├── data_processing/      # 数据清洗 + 验证
│   ├── data_collection/      # NBS/AKShare 数据采集
│   ├── core/                 # 缓存、配置、数据库
│   ├── utils/                # 模型安全（HMAC 签名）
│   ├── report_generator.py   # 多格式报告（PDF/Excel/JSON/Text）
│   └── model_versioning.py   # 模型版本管理 + 反馈闭环
├── frontend/
│   └── src/
│       ├── views/            # Enterprise / Government / CityComparison / DataManager
│       ├── stores/           # Pinia 状态管理
│       ├── api/              # API 接口定义
│       └── components/       # ECharts 图表 / KPI 卡片 / 布局
├── tests/
│   └── backend/              # 159 个 pytest 测试
├── config/
│   └── settings.py           # 全局配置（环境变量驱动）
├── .github/workflows/        # CI/CD（Python + Node.js）
├── pyproject.toml            # 项目元数据 + pytest/ruff/mypy 配置
├── requirements.txt
└── demo_complete.py          # 端到端完整演示
```

---

## 安全特性

| 特性 | 实现 |
|------|------|
| JWT 认证 | python-jose + OAuth2PasswordBearer |
| 模型签名 | HMAC-SHA256 签名校验 |
| 表达式安全 | numexpr + AST 白名单（替代 eval） |
| API 防护 | traceback 不泄露、CORS 白名单 |
| DEBUG 模式 | 默认关闭，环境变量控制 |

---

## 验证结果

```
✅ pytest: 159 passed, 0 failed (19.05s)
✅ vue-tsc: 0 type errors
✅ Vite build: 成功 (9.06s)
✅ 端到端演示: 10/10 通过
```

---

MIT License