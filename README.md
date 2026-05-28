# 区域产业经济分析平台

## 项目简介

面向区域产业经济的智能分析平台，实现从数据采集到可视化分析的完整自动化流程。以 2025 年深圳半导体产业结合财政数据为示例，为企业和政府提供专业的产业经济分析工具。

## 📋 目录

- [项目简介](#项目简介)
- [技术架构](#技术架构)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [功能特性](#功能特性)
- [使用示例](#使用示例)
- [API 文档](#api-文档)
- [开发指南](#开发指南)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🚀 技术架构

### 后端技术栈
- **Web 框架**: FastAPI 0.104+
- **数据处理**: Pandas, NumPy, SciPy
- **可视化**: Plotly, Matplotlib
- **配置管理**: Pydantic-settings
- **机器学习**: Scikit-learn, Statsmodels
- **数据源**: Akshare (可选数据源)
- **数据库**: SQLAlchemy (数据存储)
- **经济模型**: 菲利普斯曲线、奥肯定律、柯布-道格拉斯生产函数

### 前端技术栈
- **框架**: Vue 3 + TypeScript 5.x
- **构建工具**: Vite 5.x
- **UI 组件库**: Element Plus 2.x
- **状态管理**: Pinia 2.x
- **图表库**: Apache ECharts 5.x
- **路由**: Vue Router 4.x
- **HTTP 客户端**: Axios
- **工具库**: Lodash-es, Day.js

## 📁 项目结构

```
national_stats/
├── backend/                  # 后端核心代码
│   ├── api/                 # FastAPI 接口层
│   │   ├── main.py         # API 主入口
│   │   └── routes/          # 路由模块
│   │       ├── data.py      # 数据接口
│   │       └── analysis.py  # 分析接口
│   ├── analysis/            # 分析引擎
│   │   ├── indicator_registry.py   # 指标注册系统
│   │   ├── custom_indicators.py    # 自定义指标计算引擎
│   │   ├── dimension_analysis.py   # 维度分析框架
│   │   ├── economic_models.py      # 经济模型实现
│   │   ├── enterprise_analyzer.py  # 企业端分析
│   │   └── government_analyzer.py  # 政府端分析
│   ├── data_collection/     # 数据采集模块
│   │   ├── base_collector.py
│   │   ├── data_source_manager.py
│   │   ├── nbs_collector.py
│   │   ├── industry_collector.py
│   │   └── finance_collector.py
│   ├── data_processing/     # 数据处理模块
│   │   ├── cleaner.py
│   │   ├── transformer.py
│   │   └── validator.py
│   ├── utils/               # 工具函数
│   │   ├── report_generator.py
│   │   ├── visualizer.py
│   │   └── export_utils.py
│   ├── models/              # 数据模型
│   └── core/                # 核心模块
├── config/                  # 配置管理
│   ├── settings.py          # 全局配置
│   ├── loader.py            # 配置加载器
│   ├── analysis_config.py   # 分析配置
│   ├── scenario_manager.py  # 场景管理系统
│   ├── regions/             # 区域配置
│   │   ├── shenzhen.py
│   │   └── template.py
│   └── industries/          # 产业配置
│       ├── semiconductor.py
│       └── template.py
├── frontend/                # 前端可视化系统
│   ├── src/
│   │   ├── api/            # API 调用封装
│   │   ├── components/     # 通用组件
│   │   │   ├── charts/     # 图表组件
│   │   │   ├── widgets/    # 小部件
│   │   │   └── layout/     # 布局组件
│   │   ├── views/          # 页面组件
│   │   │   ├── Home.vue
│   │   │   ├── Enterprise.vue
│   │   │   ├── Government.vue
│   │   │   ├── Map.vue
│   │   │   └── DataManager.vue
│   │   ├── stores/         # Pinia 状态管理
│   │   │   ├── analysis.ts
│   │   │   └── ui.ts
│   │   ├── utils/          # 工具函数
│   │   ├── types/          # TypeScript 类型定义
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── examples/               # 示例分析
│   ├── shenzhen_semiconductor_2025/
│   │   ├── enterprise_analysis.py
│   │   ├── government_analysis.py
│   │   └── generate_report.py
│   └── template/
├── docs/                   # 项目文档
│   ├── PROJECT_INTRO.md    # 项目介绍
│   ├── DEVELOPER_GUIDE.md  # 开发者指南
│   ├── USAGE_GUIDE.md      # 使用指南
│   ├── CONFIG_GUIDE.md     # 配置指南
│   ├── EXAMPLE_ANALYSIS.md # 示例分析文档
│   ├── VISUALIZATION_PLAN.md # 可视化计划
│   ├── DEMO_GUIDE.md       # 演示指南
│   ├── SLIDES.md           # 演示幻灯片
│   └── VIDEO_SCRIPT.md     # 视频脚本
├── scripts/                # 脚本工具 (如适用)
├── main.py                # 统一启动入口
├── setup.py               # Python 包配置
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
├── .gitignore            # Git 忽略配置
├── LICENSE               # 许可证
└── VERSION               # 版本信息
```

## ⚡ 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+  (推荐 20.x)
- npm 或 yarn 或 pnpm

### 1. 克隆项目

```bash
git clone <your-repository-url>
cd national_stats
```

### 2. 后端设置

#### 安装依赖

```bash
# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 配置环境变量

```bash
# 复制示例环境变量
cp .env.example .env
# 根据需要编辑 .env 文件
```

#### 启动后端服务

```bash
# 方式 1: 使用 FastAPI 直接启动
python -m uvicorn backend.api.main:app --reload --port 8001

# 方式 2: 使用主入口
python main.py
```

后端服务将在 `http://localhost:8001` 启动

### 3. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

前端开发服务器将在 `http://localhost:5173` 启动

### 4. 访问应用

打开浏览器访问：
- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8001
- **API 文档**: http://localhost:8001/docs (自动生成的 Swagger 文档)

## ✨ 功能特性

### 1. 灵活的指标注册系统
- 支持动态注册各类分析指标
- 预置宏观经济、产业分析、营商环境等 39 个指标
- 按分类、标签管理和检索
- 阈值配置和警示功能

### 2. 自定义指标计算引擎
- 支持通过公式或自定义函数计算指标
- 预置复合年均增长率、赤字率、财政自给率等 20+ 常用公式
- 支持数据依赖关系管理
- 自动计算和缓存结果

### 3. 数据源管理系统
- 支持多种数据源（JSON、CSV、API、数据库）
- 数据源优先级配置
- 数据缓存机制
- 统一数据接口抽象

### 4. 维度分析框架
- 描述性分析、对比分析、趋势分析、相关性分析
- 支持自定义分析维度
- 自动生成洞察和建议
- 可扩展的分析插件

### 5. 场景配置系统
- 多场景配置快速切换
- 预置深圳半导体、上海新能源汽车等场景
- 场景克隆和修改
- 配置版本管理

### 6. 企业端分析
- 土地成本、人力成本、能源成本综合分析
- 供应链配套覆盖度评估
- 政策红利分析
- 综合成本指数计算
- 企业选址优化建议

### 7. 政府端分析
- 财政杠杆分析
- 产业带动效应评估
- 产业链完整性分析
- 产业政策建议
- 投资回报预测

### 8. 可视化展示
- KPI 卡片实时展示
- 趋势图、柱状图、饼图、雷达图
- 产业地图可视化
- 响应式布局适配
- 多种输出格式（HTML、Markdown、JSON）

### 9. 报告生成系统
- 一键生成分析报告
- 支持多种报告模板
- 可定制的报告内容
- 多种导出格式

## 📖 使用示例

### 运行深圳半导体产业分析

```python
# 企业端分析
from examples.shenzhen_semiconductor_2025.enterprise_analysis import EnterpriseAnalysisRunner
runner = EnterpriseAnalysisRunner()
report = runner.generate_report()
print(report)

# 政府端分析
from examples.shenzhen_semiconductor_2025.government_analysis import GovernmentAnalysisRunner
runner = GovernmentAnalysisRunner()
report = runner.generate_report()
print(report)
```

### 灵活扩展功能演示

```bash
python demo_flexibility.py
```

### 使用 API

```bash
# 获取基础数据
curl http://localhost:8001/api/v1/data/basic

# 企业端分析
curl -X POST http://localhost:8001/api/v1/analysis/enterprise \
  -H "Content-Type: application/json" \
  -d '{"region":"深圳","industry":"半导体"}'
```

## 🎨 页面功能说明

### 1. 概览页面 (`/`)
- 实时显示 GDP、增速、就业、财政收入等核心 KPI 指标
- 经济指标趋势图和产业结构分布图
- 各模块快速操作入口
- 最近分析记录和推荐报告

### 2. 企业端分析 (`/enterprise`)
- 营商成本多维分析（土地、人力、能源、融资）
- 供应链配套覆盖度评估
- 政策红利匹配分析
- 综合成本指数和排名
- 企业选址优化建议

### 3. 政府端分析 (`/government`)
- 财政杠杆和政策效率分析
- 产业带动效应评估
- 产业链完整性和瓶颈分析
- 产业政策建议
- 投资回报预测模型

### 4. 产业地图 (`/map`)
- 区域产业发展热力图
- 多维度指标筛选和对比
- 时间趋势分析
- 区域间对比分析

### 5. 数据管理 (`/data`)
- 数据查询与高级筛选
- 数据上传与批量导入
- 数据质量检查
- 数据导出和备份

## 📚 API 文档

启动后端服务后，访问 Swagger 文档：http://localhost:8001/docs

### 主要 API 端点

#### 数据接口
- `GET /api/v1/data/basic` - 获取基础数据
- `GET /api/v1/data/trend` - 获取趋势数据
- `GET /api/v1/data/map` - 获取地图数据

#### 分析接口
- `POST /api/v1/analysis/enterprise` - 企业端分析
- `POST /api/v1/analysis/government` - 政府端分析

#### 配置接口
- `GET /api/v1/config` - 获取配置信息
- `GET /api/v1/config/scenarios` - 获取场景列表

更多详细 API 文档请参考 [API 文档](http://localhost:8001/docs)

## 🔧 开发指南

### 添加新指标

```python
from backend.analysis.indicator_registry import register_indicator, IndicatorCategory

register_indicator(
    code='custom_ratio',
    name='自定义比率',
    category=IndicatorCategory.INDUSTRY,
    unit='%',
    description='自定义指标描述',
    threshold_high=80.0
)
```

### 添加新分析维度

```python
from backend.analysis.dimension_analysis import register_analysis_dimension, AnalysisType

register_analysis_dimension(
    code='custom_analysis',
    name='自定义分析',
    data_fields=['field1', 'field2'],
    analysis_type=AnalysisType.TREND
)
```

### 注册自定义指标计算公式

```python
from backend.analysis.custom_indicators import register_custom_formula

register_custom_formula(
    code='cost_effectiveness',
    formula='{output} / ({cost} * {time}) * 100',
    dependencies=['output', 'cost', 'time']
)
```

### 前端开发

#### 添加新页面

1. 在 `frontend/src/views/` 创建新组件
2. 在 `frontend/src/router/index.ts` 添加路由
3. 在 `AppLayout.vue` 更新导航菜单

#### 状态管理

使用 Pinia 进行状态管理，参考 `frontend/src/stores/` 下的示例文件。

### 配置自定义场景

在 `config/` 目录下添加新的区域或产业配置文件，参考现有的模板文件。

## 📄 项目文档

项目包含详细的文档，位于 `docs/` 目录：

- [项目介绍](docs/PROJECT_INTRO.md) - 完整的项目介绍和背景
- [开发者指南](docs/DEVELOPER_GUIDE.md) - 详细的开发说明
- [使用指南](docs/USAGE_GUIDE.md) - 用户使用手册
- [配置指南](docs/CONFIG_GUIDE.md) - 配置文件说明
- [示例分析](docs/EXAMPLE_ANALYSIS.md) - 分析示例详解
- [可视化计划](docs/VISUALIZATION_PLAN.md) - 可视化设计方案
- [演示指南](docs/DEMO_GUIDE.md) - 如何进行项目演示

## 🎯 项目开发里程碑

- ✅ **第一阶段**: 代码模块化拆分
- ✅ **第二阶段**: 参数可配置化改造  
- ✅ **第三阶段**: 深圳半导体产业分析脚本
- ✅ **第四阶段**: 优化启动流程和文档、边缘功能
- ✅ **第五阶段**: 可视化开发 (Vue 3 + TypeScript)
- ⏳ **第六阶段**: 补充完整的测试用例
- ⏳ **第七阶段**: 部署测试和最终验证

## 🔮 后续工作

1. 完善产业地图的 GeoJSON 数据和可视化
2. 补充完整的单元测试和集成测试
3. 接入真实数据源 API (如统计局公开数据)
4. Docker 容器化部署方案
5. CI/CD 自动化流程配置
6. 性能优化和智能缓存策略
7. 用户权限和认证系统
8. 多语言国际化支持

## 🤝 贡献指南

我们欢迎任何形式的贡献！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

请确保：
- 代码符合项目的编码规范
- 添加必要的测试用例
- 更新相关的文档

## 📄 许可证

本项目采用 MIT License 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 深圳统计局公开数据
- 国家统计局公开数据
- Apache ECharts 社区
- Vue.js 社区
- FastAPI 社区
- 所有为开源社区做出贡献的开发者

## 📞 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交 Issue
- 发送邮件

---

**注意**: 本项目仅用于学习和研究目的。请遵守相关数据使用法律法规。
