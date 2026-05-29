# 区域产业经济分析平台

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.4+-42b883.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**面向求职的可复用区域产业经济分析工具**

</div>

---

## 📋 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [API接口](#api接口)
- [使用示例](#使用示例)
- [开发指南](#开发指南)
- [部署说明](#部署说明)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)

---

## 🎯 项目简介

区域产业经济分析平台是一个**面向求职的专业级可复用分析工具**，旨在帮助用户快速构建区域产业经济分析项目。

本项目以**2025年深圳半导体产业**结合**财政数据**为示例，展示了如何将经济学模型应用于企业端和政府端的分析框架。

### 为什么使用这个项目？

- 📊 **专业分析能力**：展示了完整的经济分析模型实现（菲利普斯曲线、奥肯定律等）
- 🔧 **高度可复用**：模块化设计，易于扩展和定制
- 📈 **可视化展示**：精美的图表和交互式界面
- 💻 **全栈实现**：前后端分离，API驱动
- 🎓 **求职准备**：技术栈现代化，适合作为求职项目展示
- 🐍 **爬虫数据采集**：支持从国家统计局等数据源自动采集真实数据

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

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.115+ | Web 框架 |
| Uvicorn | 0.32+ | ASGI 服务器 |
| Pandas | 2.2+ | 数据处理 |
| NumPy | 1.26+ | 数值计算 |
| SciPy | 1.11+ | 科学计算 |
| Statsmodels | 0.14+ | 统计建模 |
| SQLAlchemy | 2.0+ | ORM 框架 |
| Pydantic | 2.5+ | 数据验证 |

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4+ | 前端框架 |
| TypeScript | 5.0+ | 类型安全 |
| Vite | 5.0+ | 构建工具 |
| Element Plus | 2.5+ | UI 组件库 |
| Pinia | 2.1+ | 状态管理 |
| Vue Router | 4.2+ | 路由管理 |
| ECharts | 5.4+ | 图表库 |

---

## 📁 项目结构

```
national_stats/
├── backend/                          # 后端核心代码
│   ├── api/                          # API 层
│   │   ├── main.py                   # API 主入口
│   │   └── routes/                   # 路由模块
│   │       ├── analysis.py           # 分析接口
│   │       ├── data.py               # 数据接口
│   │       └── cities.py             # 城市数据接口
│   ├── analysis/                     # 分析引擎
│   │   ├── indicator_registry.py     # 指标注册系统
│   │   ├── economic_models.py        # 经济模型实现
│   │   ├── enterprise_analyzer.py    # 企业端分析器
│   │   └── government_analyzer.py    # 政府端分析器
│   ├── data_collection/              # 数据采集模块
│   │   ├── web_crawler.py            # 网络爬虫
│   │   ├── nbs_collector.py          # 国家统计局采集器
│   │   └── industry_collector.py     # 产业数据采集器
│   ├── data_processing/              # 数据处理模块
│   ├── models/                       # 数据模型
│   └── utils/                        # 工具函数
├── config/                           # 配置管理
│   ├── regions/                      # 区域配置
│   └── industries/                   # 产业配置
├── frontend/                         # 前端可视化系统
│   ├── src/
│   │   ├── views/                    # 页面组件
│   │   ├── components/               # 通用组件
│   │   ├── stores/                   # Pinia 状态管理
│   │   └── api/                      # API 接口封装
│   └── package.json
├── examples/                         # 示例分析
├── docs/                             # 项目文档
├── tests/                            # 测试文件
├── requirements.txt                  # Python 依赖
├── setup.py                          # Python 包配置
├── pyproject.toml                    # 现代 Python 配置
├── docker-compose.yml                # Docker Compose 配置
├── .env.example                      # 环境变量示例
├── .gitignore                        # Git 忽略配置
├── LICENSE                           # 许可证
└── README.md                         # 项目说明
```

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.9 或更高版本
- **Node.js**: 18 或更高版本
- **npm**: 9 或更高版本

### 本地开发环境

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
```

#### 4. 启动后端服务

```bash
# 使用 Uvicorn 启动
python -m uvicorn backend.api.main:app --reload --port 8001
```

后端服务将在 `http://localhost:8001` 启动

#### 5. 前端安装依赖和启动

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器将在 `http://localhost:5173` 启动

### 使用 Docker

```bash
# 启动后端服务
docker-compose up -d backend

# 查看服务状态
docker-compose ps
```

---

## 📡 API 接口

### 数据接口

**获取基础数据**
```http
GET /api/v1/data/basic
```

**获取趋势数据**
```http
GET /api/v1/data/trend?region=深圳&industry=半导体
```

**获取地图数据**
```http
GET /api/v1/data/map?indicator=output&year=2025
```

### 分析接口

**企业端分析**
```http
POST /api/v1/analysis/enterprise
Content-Type: application/json

{
  "region": "深圳",
  "industry": "半导体",
  "year": 2025
}
```

**政府端分析**
```http
POST /api/v1/analysis/government
Content-Type: application/json

{
  "region": "深圳",
  "industry": "半导体",
  "year": 2025
}
```

**获取真实爬虫数据**
```http
GET /api/v1/analysis/real-data?year=2025
```

### 城市数据接口

**获取城市列表**
```http
GET /api/v1/interactive/cities
```

---

## 💡 使用示例

### Python 脚本使用

```python
from backend.analysis.enterprise_analyzer import EnterpriseAnalyzer
from backend.analysis.government_analyzer import GovernmentAnalyzer

# 企业端分析
enterprise_analyzer = EnterpriseAnalyzer()
result = enterprise_analyzer.analyze(
    region="深圳",
    industry="半导体",
    year=2025
)
print(result)

# 政府端分析
gov_analyzer = GovernmentAnalyzer()
result = gov_analyzer.analyze(
    region="深圳",
    industry="半导体",
    year=2025
)
print(result)
```

### API 调用示例

```bash
# 使用 curl 调用企业端分析接口
curl -X POST http://localhost:8001/api/v1/analysis/enterprise \
  -H "Content-Type: application/json" \
  -d '{"region":"深圳","industry":"半导体","year":2025}'

# 获取爬虫数据
curl http://localhost:8001/api/v1/analysis/real-data?year=2025
```

---

## 🔧 开发指南

### 添加新分析模块

1. 在 `backend/analysis/` 创建新分析器类
2. 在 `backend/api/routes/` 添加新路由
3. 在 `config/` 目录下添加配置文件

### 前端开发

1. 在 `frontend/src/views/` 创建新组件
2. 在 `frontend/src/router/index.ts` 添加路由
3. 在 `frontend/src/stores/` 添加状态管理

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/backend/test_analysis.py -v
```

---

## 📦 部署说明

### 生产环境部署

#### 使用 Gunicorn + Uvicorn

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.api.main:app --bind 0.0.0.0:8000
```

#### 使用 Nginx 反向代理

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
    }
}
```

---

## ❓ 常见问题

### Q: 如何添加新的数据源？
A: 在 `backend/data_collection/` 下继承 `BaseCollector` 类，实现自定义的数据收集器。

### Q: 如何自定义图表样式？
A: 在 `frontend/src/utils/charts.ts` 中修改图表配置。

### Q: 爬虫数据获取失败怎么办？
A: 爬虫模块已配置自动降级机制，当真实数据源不可用时会自动切换到模拟数据。

### Q: 如何添加新的分析指标？
A: 使用 `backend/analysis/indicator_registry.py` 中的 `register_indicator` 函数注册新指标。

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT License 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- 国家统计局公开数据
- Apache ECharts 社区
- Vue.js 社区
- FastAPI 社区

---

**注意**: 本项目仅用于学习和研究目的。请遵守相关数据使用法律法规。

---

<div align="center">
如果这个项目对你有帮助，请给我们一个 ⭐ Star！
</div>