# 区域产业经济分析平台

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.4+-42b883.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/badhope/national_stats?style=social)](https://github.com/badhope/national_stats)

**面向求职的可复用区域产业经济分析工具

[English | [中文](README.md) | [文档](./docs/)

</div>

---

## 📋 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [安装部署](#安装部署)
- [功能详解](#功能详解)
- [API文档](#api文档)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 🎯 项目简介

区域产业经济分析平台是一个**面向求职的专业级可复用分析工具，旨在帮助用户快速构建区域产业经济分析项目。

本项目以**2025年深圳半导体产业**结合**财政数据**为示例，展示了如何将经济学模型的企业端和政府端分析框架。

### 为什么使用这个项目？

- 📊 **专业分析能力**：展示了完整的经济分析模型实现
- 🔧 **高度可复用**：模块化设计，易于扩展和定制
- 📈 **可视化展示**：精美的图表和交互式界面
- 💻 **全栈实现**：前后端分离，API驱动
- 🎓 **求职准备**：为技术栈现代化，适合作为求职项目展示

---

## ✨ 核心特性

### 🏢 企业端分析
- **营商成本分析**：土地、人力、能源、融资成本多维度评估
- **供应链配套**：本地配套率、平均交付周期、区位熵分析
- **政策红利**：税收减免、补贴、审批效率评估
- **综合成本指数**：多因素加权评分

### 🏛️ 政府端分析
- **财政杠杆**：财政收支、专项债、杠杆率分析
- **产业带动**：就业带动、税收贡献、相关产业产值
- **产业链分析**：上游、中游、下游覆盖度
- **政策建议**：基于数据驱动的政策建议

### 🔄 灵活扩展功能
- **指标注册系统**：动态注册各类经济分析指标
- **自定义指标计算**：通过公式或自定义函数
- **数据源管理**：多数据源支持和动态切换
- **维度分析框架**：多维度分析和洞察生成
- **场景配置系统**：多场景配置快速切换

### 📊 可视化功能
- **KPI 指标卡片**：实时展示关键指标
- **趋势图表**：折线图、柱状图、饼图、雷达图
- **产业地图**：区域热力图和对比分析
- **响应式设计**：适配各种屏幕尺寸

---

## 🏗️ 技术架构

### 后端技术栈

```
┌─────────────────────────────────────────────────────────┐
│                     前端层 (Vue 3 + TypeScript)          │
│  ┌──────────┐  ┌─────────┐  ┌──────────────────┐ │
│  │ Element  │  │ Vue    │  │ ECharts         │ │
│  │ Plus    │  │ Router  │  │ (可视化图表)    │ │
│  └──────────┘  └─────────┘  └──────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Pinia 状态管理                      │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           │ HTTP/REST API
                           ↓
┌─────────────────────────────────────────────────────────┐
│                  API 层 (FastAPI)                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 数据接口    │ 分析接口    │ 配置接口    │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│               业务逻辑层                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ 指标管理  │ │ 分析引擎 │ │ 数据处理  │         │
│  └──────────┘ └──────────┘ └──────────┘         │
│  ┌─────────────────────────────────────────────────┐  │
│  │           经济模型 (菲利普斯曲线、奥肯定律等)    │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────┐
│              数据层 (Data Layer                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ JSON/CSV  │ │ SQLite  │ │ API 数据源│         │
│  └──────────┘ └──────────┘ └──────────┘         │
└─────────────────────────────────────────────────────────┘
```

### 技术栈详情

#### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.104+ | Web 框架 |
| Uvicorn | 0.24+ | ASGI 服务器 |
| Pandas | 2.1+ | 数据处理 |
| NumPy | 1.26+ | 数值计算 |
| SciPy | 1.11+ | 科学计算 |
| Plotly | 5.18+ | 可视化 |
| Matplotlib | 3.8+ | 绘图库 |
| Scikit-learn | 1.3+ | 机器学习 |
| Statsmodels | 0.14+ | 统计建模 |
| SQLAlchemy | 2.0+ | ORM 框架 |
| Pydantic | 2.5+ | 数据验证 |
| Pydantic-settings | 2.0+ | 配置管理 |

#### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4+ | 前端框架 |
| TypeScript | 5.0+ | 类型安全 |
| Vite | 5.0+ | 构建工具 |
| Element Plus | 2.5+ | UI 组件库 |
| Pinia | 2.1+ | 状态管理 |
| Vue Router | 4.2+ | 路由管理 |
| ECharts | 5.4+ | 图表库 |
| Axios | 1.6+ | HTTP 客户端 |

---

## 📁 项目结构

```
national_stats/
├── backend/                          # 后端核心代码
│   ├── api/                      # API 层
│   │   ├── main.py              # API 主入口
│   │   └── routes/             # 路由模块
│   │       ├── data.py          # 数据接口
│   │       ├── analysis.py      # 分析接口
│   │       └── inference.py     # 推理接口
│   ├── analysis/                  # 分析引擎
│   │   ├── indicator_registry.py    # 指标注册系统
│   │   ├── custom_indicators.py # 自定义指标计算引擎
│   │   ├── dimension_analysis.py   # 维度分析框架
│   │   ├── economic_models.py      # 经济模型实现
│   │   ├── enterprise_analyzer.py  # 企业端分析器
│   │   └── government_analyzer.py # 政府端分析器
│   ├── data_collection/          # 数据采集模块
│   │   ├── base_collector.py
│   │   ├── data_source_manager.py
│   │   ├── nbs_collector.py
│   │   ├── industry_collector.py
│   │   └── finance_collector.py
│   ├── data_processing/         # 数据处理模块
│   │   ├── cleaner.py
│   │   ├── transformer.py
│   │   └── validator.py
│   ├── utils/                    # 工具函数
│   │   ├── report_generator.py
│   │   ├── visualizer.py
│   │   └── export_utils.py
│   ├── models/                   # 数据模型
│   └── core/                     # 核心模块
├── config/                         # 配置管理
│   ├── settings.py               # 全局配置
│   ├── loader.py               # 配置加载器
│   ├── analysis_config.py      # 分析配置
│   ├── scenario_manager.py    # 场景配置系统
│   ├── regions/                 # 区域配置
│   │   ├── shenzhen.py
│   │   └── template.py
│   └── industries/              # 产业配置
│       ├── semiconductor.py
│       └── template.py
├── frontend/                        # 前端可视化系统
│   ├── src/
│   │   ├── api/                  # API 接口封装
│   │   ├── components/           # 通用组件
│   │   │   ├── charts/         # 图表组件
│   │   │   ├── widgets/       # 小部件
│   │   │   └── layout/        # 布局组件
│   │   ├── views/               # 页面组件
│   │   │   ├── Home.vue
│   │   │   ├── Enterprise.vue
│   │   │   ├── Government.vue
│   │   │   ├── Map.vue
│   │   │   └── DataManager.vue
│   │   ├── stores/               # Pinia 状态管理
│   │   ├── utils/                # 工具函数
│   │   ├── types/               # TypeScript 类型定义
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile.dev
├── examples/                       # 示例分析
│   ├── shenzhen_semiconductor_2025/
│   │   ├── enterprise_analysis.py
│   │   ├── government_analysis.py
│   │   ├── generate_report.py
│   │   └── data/
│   └── template/
├── docs/                           # 项目文档
│   ├── PROJECT_INTRO.md         # 项目介绍
│   ├── DEVELOPER_GUIDE.md       # 开发者指南
│   ├── USAGE_GUIDE.md           # 使用指南
│   ├── CONFIG_GUIDE.md         # 配置指南
│   ├── EXAMPLE_ANALYSIS.md   # 示例分析文档
│   ├── VISUALIZATION_PLAN.md    # 可视化计划
│   ├── DEMO_GUIDE.md           # 演示指南
│   ├── SLIDES.md              # 演示幻灯片
│   └── VIDEO_SCRIPT.md         # 视频脚本
├── tests/                          # 测试文件
├── main.py                        # 统一启动入口
├── setup.py                       # Python 包配置
├── pyproject.toml                # 现代 Python 配置
├── requirements.txt               # Python 依赖
├── Dockerfile                     # Docker 镜像
├── docker-compose.yml            # Docker Compose 配置
├── .env.example                 # 环境变量示例
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🚀 快速开始

### 环境要求

确保你的环境满足以下要求：

- **Python**: 3.9 或更高版本
- **Node.js**: 18 或更高版本（推荐 20.x）
- **npm**: 9 或更高版本
- **操作系统**: Windows、macOS 或 Linux

### 方式一：本地开发环境

#### 1. 克隆项目

```bash
git clone https://github.com/badhope/national_stats.git
cd national_stats
```

#### 2. 后端安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑 .env 文件，根据需要修改配置
```

#### 4. 启动后端服务

```bash
# 方式一：使用 Uvicorn 直接启动
python -m uvicorn backend.api.main:app --reload --port 8001

# 方式二：使用主入口启动
python main.py
```

后端服务将在 `http://localhost:8001` 启动，访问 Swagger 文档：`http://localhost:8001/docs`

#### 5. 前端安装依赖和启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端开发服务器将在 `http://localhost:5173` 启动。

### 方式二：使用 Docker

#### 使用 Docker Compose 快速启动：

```bash
# 构建并启动后端服务
docker-compose up -d backend

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

#### 开发环境（包含前端）：

```bash
# 启动后端 + 前端开发服务器
docker-compose --profile dev up -d
```

### 方式三：使用 pip 安装

```bash
# 安装项目
pip install -e .

# 启动服务
national-stats-api
```

---

## 📦 安装部署

### 生产环境部署

#### 1. 环境变量配置

在生产环境中，请确保正确配置以下环境变量：

```env
# 基础配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/national_stats

# 安全配置（生产环境必须修改）
SECRET_KEY=your-production-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 数据目录
DATA_DIR=/app/data
EXPORT_DIR=/app/exports
```

#### 2. 使用 Gunicorn + Uvicorn 部署

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.api.main:app --bind 0.0.0.0:8000
```

#### 3. 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 💡 功能详解

### 企业端分析

企业端分析模块帮助企业评估区域营商环境，主要功能：

#### 1. 营商成本分析

- **土地成本**: 工业用地价格、商业用地价格
- **人力成本**: 平均工资水平、社保缴费比例
- **能源成本**: 电价、水价、气价
- **融资成本**: 贷款利率、融资便利性

#### 2. 供应链配套分析

- **本地配套率**: 本地供应商占比
- **平均交付周期**: 供应链响应速度
- **区位熵**: 产业集聚度指标

#### 3. 政策红利分析

- **税收减免**: 税收优惠政策
- **补贴政策**: 各类产业补贴
- **审批效率**: 行政审批时间

#### 使用示例

```python
from examples.shenzhen_semiconductor_2025.enterprise_analysis import EnterpriseAnalysisRunner

# 创建分析器
runner = EnterpriseAnalysisRunner()

# 生成分析报告
report = runner.generate_report()

# 查看报告
print(report)
```

### 政府端分析

政府端分析模块帮助政府评估产业政策效果，主要功能：

#### 1. 财政杠杆分析

- **财政收支**: 一般公共预算收支
- **专项债**: 专项债券发行和使用
- **杠杆率**: 政府债务率、企业杠杆率

#### 2. 产业带动效应分析

- **就业带动**: 产业就业人数、带动系数
- **税收贡献**: 产业税收收入、占比
- **相关产业**: 相关产业产值、影响力系数

#### 3. 产业链分析

- **上游覆盖度**: 上游产业本地配套
- **中游覆盖度**: 中游产业本地配套
- **下游覆盖度**: 下游产业本地配套
- **瓶颈识别**: 产业链短板识别

#### 使用示例

```python
from examples.shenzhen_semiconductor_2025.government_analysis import GovernmentAnalysisRunner

# 创建分析器
runner = GovernmentAnalysisRunner()

# 生成分析报告
report = runner.generate_report()

# 查看报告
print(report)
```

### 灵活扩展功能

#### 1. 指标注册系统

```python
from backend.analysis.indicator_registry import register_indicator, IndicatorCategory
from backend.analysis.indicator_registry import register_indicator, IndicatorCategory
from backend.analysis.indicator_registry import Indicator, IndicatorCategory


# 注册新指标
register_indicator(
    code="custom_gdp_growth",
    name="GDP增长率",
    category=IndicatorCategory.MACRO,
    unit="%",
    description="国内生产总值同比增长率",
    formula="(current_gdp / previous_gdp - 1) * 100",
    threshold_high=10.0,
    threshold_low=3.0
)
```

#### 2. 自定义指标计算

```python
from backend.analysis.custom_indicators import register_custom_formula

# 注册自定义计算公式
register_custom_formula(
    code="cost_effectiveness",
    formula="output / (cost * time) * 100",
    dependencies=["output", "cost", "time"]
)

# 使用自定义公式计算
from backend.analysis.custom_indicators import calculate_custom_indicator
result = calculate_custom_indicator(
    code="cost_effectiveness",
    data={"output": 1000, "cost": 50, "time": 2}
)
```

#### 3. 维度分析框架

```python
from backend.analysis.dimension_analysis import (
    register_analysis_dimension,
    AnalysisType
)

# 注册分析维度
register_analysis_dimension(
    code="trend_analysis",
    name="趋势分析",
    data_fields=["year", "value"],
    analysis_type=AnalysisType.TREND
)
```

---

## 📡 API 文档

### 数据接口

#### 获取基础数据

```http
GET /api/v1/data/basic
```

**响应示例:**

```json
{
  "region": "深圳",
  "industry": "半导体",
  "year": 2025,
  "gdp": 35000.0,
  "gdp_growth": 5.8,
  "population": 1750.0
}
```

#### 获取趋势数据

```http
GET /api/v1/data/trend
```

### 分析接口

#### 企业端分析

```http
POST /api/v1/analysis/enterprise
Content-Type: application/json

{
  "region": "深圳",
  "industry": "半导体",
  "year": 2025
}
```

#### 政府端分析

```http
POST /api/v1/analysis/government
Content-Type: application/json

{
  "region": "深圳",
  "industry": "半导体",
  "year": 2025
}
```

### 配置接口

#### 获取配置

```http
GET /api/v1/config
```

#### 获取场景列表

```http
GET /api/v1/config/scenarios
```

---

## 🔧 开发指南

### 本地开发

#### 设置开发环境

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit hooks
pre-commit install

# 运行测试
pytest

# 代码格式化
black .

# 代码检查
flake8
```

### 添加新分析模块

#### 1. 创建新分析器

```python
from backend.analysis.base_analyzer import BaseAnalyzer

class MyCustomAnalyzer(BaseAnalyzer):
    """自定义分析器
    
    def analyze(self, data):
        # 实现分析逻辑
        pass
    
    def generate_report(self):
        # 生成报告
        pass
```

#### 2. 添加配置

在 `config/` 目录下添加配置文件。

#### 3. 注册到 API

在 `backend/api/routes/` 下添加新路由。

### 前端开发

#### 添加新页面

1. 在 `frontend/src/views/` 创建新组件
2. 在 `frontend/src/router/index.ts` 添加路由
3. 在 `AppLayout.vue` 更新导航菜单

---

## ❓ 常见问题

### Q: 如何添加新的数据源？

A: 在 `backend/data_collection/` 下继承 `BaseCollector` 类，实现自定义的数据收集器。

### Q: 如何自定义图表样式？

A: 在 `frontend/src/utils/charts.ts` 中修改图表配置。

### Q: 项目是否支持多语言？

A: 目前主要使用中文，可通过 i18n 扩展支持多语言。

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

请确保：
- 代码符合项目的编码规范
- 添加必要的测试用例
- 更新相关的文档

---

## 📄 许可证

本项目采用 MIT License 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- 深圳统计局公开数据
- 国家统计局公开数据
- Apache ECharts 社区
- Vue.js 社区
- FastAPI 社区
- 所有为开源社区做出贡献的开发者们

---

## 📞 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交 [Issue](https://github.com/badhope/national_stats/issues)
- 发送邮件

---

**注意**: 本项目仅用于学习和研究目的。请遵守相关数据使用法律法规。

---

<div align="center">
如果这个项目对你有帮助，请给我们一个 ⭐ Star！
</div>
