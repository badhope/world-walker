# 架构总览

> 本文档面向开发者与运维人员，说明系统的设计原则、模块划分、数据流与扩展点。

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| **API First** | 一切功能通过 REST API 暴露；前端只是 API 的可视化层 |
| **零前端构建** | 前端是单 HTML 文件 + CDN，零 npm / 零 webpack / 零 node_modules |
| **配置外置** | 所有可调参数（端口、密钥、CORS、模型权重）通过环境变量注入 |
| **关注点分离** | `api`（路由）/ `core`（业务）/ `data`（数据）三层严格分离 |
| **可测试性** | 所有业务逻辑纯函数化，便于 pytest |

## 2. 系统组件图

```
                       ┌─────────────────────────────────────┐
                       │  Browser (Chrome / Edge / Firefox)  │
                       │   ↳ http://localhost:8080/index.html │
                       └──────────┬──────────────────────────┘
                                  │ fetch + JSON
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application (port 8000)            │
│                                                                 │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐ │
│  │  routes/       │  │  core/          │  │  data/           │ │
│  │  cities        │  │  analyzer       │  │  city_data.py    │ │
│  │  analysis      │  │  forecaster     │  │  8 城市数据     │ │
│  │  forecast      │  │  city_manager   │  │  缓存层          │ │
│  │  static        │  │  city_aggregator│  └──────────────────┘ │
│  │  favicon       │  └─────────────────┘                       │
│  └────────┬───────┘          │                                  │
│           │                  ▼                                  │
│           │       ┌─────────────────────┐                       │
│           │       │  analysis/          │                       │
│           │       │  enterprise_v3      │                       │
│           │       │  government         │                       │
│           │       │  retail_location    │                       │
│           │       │  sales_forecast     │                       │
│           │       └─────────────────────┘                       │
│           ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Middleware: CORS / GZip / Logging / Auth (optional)     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                       ┌────────────────────────┐
                       │  SQLite / In-Memory    │
                       │  8 城市数据集 (HARDCODE)│
                       └────────────────────────┘
```

## 3. 目录结构

```
backend/
├── api/                  # FastAPI 路由层（HTTP 边界）
│   ├── main.py          # 应用入口 + 中间件
│   ├── dependencies.py  # 依赖注入
│   └── routes/
│       ├── cities.py        # 城市列表/对比/时间序列
│       ├── cities_v2.py     # 城市数据/历史
│       ├── analysis.py      # 企业/政府分析
│       ├── forecast.py      # GDP 预测
│       └── static.py        # 静态文件
├── core/                 # 业务核心（纯逻辑，无 HTTP）
│   ├── analyzer.py      # 评分基类
│   ├── city_aggregation.py  # 城市聚合
│   ├── forecaster.py    # 预测模型
│   └── city_manager.py  # 城市数据访问
├── analysis/             # 业务分析器（继承 BaseAnalyzer）
│   ├── enterprise_analyzer_v3.py
│   ├── government_analyzer.py
│   ├── retail_location_analyzer.py
│   └── sales_forecast_analyzer.py
├── data/                 # 数据访问层
│   └── city_data.py     # 8 城市综合数据（~10K 行）
└── config/               # 后端配置加载

frontend/
├── index.html           # 单页应用（64KB，所有 JS/CSS 内联）
└── favicon.ico          # 站点图标

config/                   # 全局配置
└── settings.py          # Pydantic Settings（环境变量加载）

docs/                     # 详细文档
tests/backend/            # pytest 单元测试
screenshots/              # 浏览器测试输出
scripts/                  # 辅助脚本（启动/停止/诊断）
```

## 4. 核心数据流

### 4.1 企业选址分析

```
Client → POST /api/v1/analysis/enterprise/v3/{city}
        ↓
routes/cities.py::analyze_enterprise_v3
        ↓
analysis/enterprise_analyzer_v3.py::EnterpriseAnalyzerV3
        ├─ 加载城市数据 (data/city_data.py)
        ├─ 计算 12 个指标的归一化得分
        ├─ 加权聚合 → 3 维度分（成本/供应/政策）
        ├─ 加权聚合 → 总分 (0-100)
        └─ 返回 JSON
        ↓
Client ← 200 OK
        ├─ 总分
        ├─ 3 维度明细
        ├─ 12 指标明细
        └─ 优化建议
```

### 4.2 GDP 预测

```
Client → GET /api/v1/forecast/gdp/{city}?forecast_years=5
        ↓
routes/cities.py::forecast_gdp
        ↓
core/forecaster.py::Forecaster
        ├─ 取历史 N 年 GDP
        ├─ 尝试 LinearRegression
        │   └─ 失败 → 简单平均
        ├─ 计算 95% 置信区间（残差标准差 × 1.96）
        └─ 返回 {years, actual, forecast, lower, upper}
        ↓
Client ← 200 OK
```

### 4.3 多城市对比

```
Client → POST /api/v1/cities/compare  ["深圳","上海","北京"]
        ↓
routes/cities.py::compare_cities
        ├─ 解析 city_codes（兼容简单数组）
        ├─ 拉取每城市指标
        ├─ core/city_aggregation.py::compare_cities
        │   ├─ 排名计算
        │   └─ 洞察生成（规则引擎）
        └─ 返回 {cities, rankings, insights}
        ↓
Client ← 200 OK
        ├─ 前端 ECharts 渲染时序图
        ├─ ECharts 渲染热力图
        └─ DOM 渲染对比表
```

## 5. 关键技术决策

| 决策 | 替代方案 | 选择理由 |
|------|---------|---------|
| 单 HTML + CDN | Vue 3 + Vite | 零构建依赖、即开即用、容器化更小 |
| FastAPI | Flask / Django | 自动 OpenAPI、类型注解、Pydantic 集成 |
| ECharts 5.4 | Chart.js / D3 | 中文文档完善、置信区间/雷达/热力图原生支持 |
| SQLite | PostgreSQL | 8 城市数据集硬编码足够，无需 DB |
| 内存缓存 | Redis | 延迟 < 1ms，零运维 |
| Pydantic Settings | python-decouple | 类型安全、IDE 提示、自动 .env 加载 |

## 6. 扩展点

### 6.1 新增分析场景

1. 在 `backend/analysis/` 创建 `*_analyzer.py`，继承 `BaseAnalyzer`
2. 在 `backend/api/routes/` 注册路由
3. 在 `frontend/index.html` 添加 Tab + 渲染函数
4. 在 `tests/backend/test_analysis.py` 添加用例

### 6.2 新增城市

1. 在 `backend/data/city_data.py` 添加数据集
2. 在 `backend/core/city_manager.py` 注册
3. 在 `frontend/index.html` 的 `populateCitySelects` 自动读取

### 6.3 接入数据库

1. 在 `backend/data/` 创建 `db_client.py`（SQLAlchemy）
2. 修改 `city_manager.py` 替换内存数据源
3. 添加 `DATABASE_URL` 到 `.env.example`

## 7. 性能特征

| 端点 | 平均响应 | P99 | 备注 |
|------|--------|-----|------|
| `/health` | 2ms | 5ms | 内存读取 |
| `/api/v1/cities/list` | 8ms | 15ms | 8 城市硬编码 |
| `/api/v1/analysis/enterprise/v3/{city}` | 35ms | 80ms | 12 指标计算 |
| `/api/v1/forecast/gdp/{city}` | 50ms | 120ms | sklearn LR |
| `/api/v1/cities/compare` (8 城市) | 110ms | 250ms | 聚合 + 排名 |

## 8. 安全模型

- **CORS**: 默认白名单模式（`CORS_ORIGINS` 环境变量）
- **XSS**: 前端所有用户输入通过 `esc()` 转义；`innerHTML` 仅用于可信静态字符串
- **CSRF**: 纯 GET 端点为主，POST 端点无副作用
- **认证**: 当前版本无认证（公开 API），生产部署建议加 JWT（代码已预留）
- **模型签名**: 加载的 ML 模型使用 HMAC-SHA256 签名校验

## 9. 部署架构

详见 [DEPLOYMENT.md](DEPLOYMENT.md)。
