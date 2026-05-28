# 🔬 区域产业经济分析平台

> 面向求职的可复用区域产业经济分析工具 | 2025年深圳半导体产业结合财政数据示例

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 项目简介

本项目是一个**区域产业经济分析平台**，采用模块化架构设计，实现了数据采集、数据处理、产业分析、指标推演、可视化展示的完整流程。项目以**2025年深圳半导体产业结合财政数据**为具体示例，展示如何进行区域产业经济分析。

### 🎯 项目特色

1. **配置化设计** - 通过配置文件灵活切换地区、产业、分析年份
2. **模块化架构** - 数据采集、处理、分析、可视化独立模块
3. **双视角分析** - 企业端（营商成本）与政府端（政策效果）
4. **经济学模型** - 集成菲利普斯曲线、奥肯定律、柯布-道格拉斯生产函数
5. **交互式可视化** - 基于Plotly的动态图表和仪表盘
6. **RESTful API** - 基于FastAPI的Web服务接口

## 🚀 快速开始

### 方式一：一键安装（推荐）

```bash
# 克隆项目
git clone https://github.com/your-project/national-stats-analyzer.git
cd national-stats-analyzer

# 一键安装（使用虚拟环境）
bash scripts/setup.sh --venv

# 运行示例分析
bash scripts/run_example.sh
```

### 方式二：手动安装

```bash
# 安装依赖
pip install -r requirements.txt

# 运行示例分析
python main.py --mode example

# 启动API服务
python main.py --mode api
```

## 📊 功能特性

### 🔍 企业端分析

- **营商成本分析**
  - 土地成本：区域对比、全国对比
  - 人力成本：薪资分布、社会保险、招聘成本
  - 能源成本：工业用电、用水、用气
  - 融资成本：贷款利率、政府贴息、股权融资

- **供应链配套效率**
  - 本地化配套率
  - 供应链响应速度
  - 产业集聚度（区位熵）

- **政策红利兑现**
  - 税收优惠统计
  - 补贴政策落实
  - 政务服务效率

### 🏛️ 政府端分析

- **财政杠杆率**
  - 财政投入强度
  - 资金使用效率
  - 杠杆效应评估

- **产业带动系数**
  - 就业带动效应
  - 税收贡献
  - 投入产出乘数

- **产业链补全度**
  - 产业链图谱构建
  - 瓶颈环节识别
  - 优势短板分析

## 🏗️ 项目架构

```
national-stats-analyzer/
├── backend/                    # 后端核心模块
│   ├── api/                    # API接口层
│   │   ├── main.py            # FastAPI应用入口
│   │   └── routes/            # 路由模块
│   ├── data_collection/       # 数据采集模块
│   │   ├── base_collector.py
│   │   └── nbs_collector.py
│   ├── data_processing/        # 数据处理模块
│   │   └── cleaner.py
│   ├── analysis/              # 分析模块
│   │   ├── base_analyzer.py
│   │   ├── enterprise_analyzer.py
│   │   ├── government_analyzer.py
│   │   └── economic_models.py
│   └── utils/                 # 工具模块
│       └── visualizer.py
├── config/                     # 配置模块
│   ├── settings.py            # 基础配置
│   ├── analysis_config.py     # 分析配置
│   ├── loader.py              # 配置加载器
│   ├── regions/               # 地区配置
│   │   ├── template.py
│   │   └── shenzhen.py
│   └── industries/            # 产业配置
│       ├── template.py
│       └── semiconductor.py
├── examples/                  # 示例模块
│   └── shenzhen_semiconductor_2025/
│       ├── data/             # 示例数据
│       ├── outputs/         # 分析输出
│       ├── enterprise_analysis.py
│       ├── government_analysis.py
│       └── generate_report.py
├── scripts/                   # 便捷脚本
│   ├── setup.sh              # 一键安装
│   ├── run_example.sh        # 运行示例
│   └── start_api.sh         # 启动API
├── docs/                      # 文档
│   ├── USAGE_GUIDE.md
│   ├── CONFIG_GUIDE.md
│   ├── EXAMPLE_ANALYSIS.md
│   └── DEVELOPER_GUIDE.md
├── main.py                    # 统一入口
├── setup.py                   # pip安装配置
├── requirements.txt           # 依赖清单
└── .env.example              # 环境变量示例
```

## 📚 使用文档

- [📖 使用指南](docs/USAGE_GUIDE.md) - 详细的安装配置教程
- [⚙️ 配置指南](docs/CONFIG_GUIDE.md) - 如何配置地区和产业参数
- [📊 示例分析文档](docs/EXAMPLE_ANALYSIS.md) - 深圳半导体产业分析案例
- [👨‍💻 开发者指南](docs/DEVELOPER_GUIDE.md) - 代码规范和开发指导

## 🔌 API接口

启动API服务后，访问 `http://localhost:8001/docs` 查看交互式API文档。

### 主要接口

- `GET /api/v1/health` - 健康检查
- `POST /api/v1/analysis/enterprise` - 企业端分析
- `POST /api/v1/analysis/government` - 政府端分析
- `GET /api/v1/inference/models/{model_name}` - 经济学模型推演
- `POST /api/v1/visualization/{chart_type}` - 可视化图表生成

## 🛠️ 技术栈

- **核心框架**: Python 3.9+, FastAPI, Pydantic
- **数据分析**: Pandas, NumPy, SciPy
- **可视化**: Plotly, ECharts
- **数据采集**: AKShare
- **配置管理**: pydantic-settings
- **API服务**: Uvicorn, Starlette
- **项目工具**: setuptools, pip

## 📈 示例分析

以**深圳半导体产业2025年**为例：

- **产业规模**: 产值12000亿元，占全国28.5%
- **企业集聚**: 2000家企业，区位熵2.85
- **政策支持**: 财政投入158.5亿元，撬动社会资本425亿元
- **就业带动**: 直接+间接就业28.5万人

查看详细分析：[示例分析文档](docs/EXAMPLE_ANALYSIS.md)

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

详细指南请参考：[开发者指南](docs/DEVELOPER_GUIDE.md)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 数据来源：[国家统计局](http://www.stats.gov.cn/)、[AKShare](https://github.com/akfamily/akshare)
- 分析框架：[FastAPI](https://fastapi.tiangolo.com/)、[Plotly](https://plotly.com/)
- 项目灵感：区域产业经济分析方法论

## 📞 联系方式

- 项目主页：https://github.com/your-project/national-stats-analyzer
- 问题反馈：https://github.com/your-project/national-stats-analyzer/issues
- 技术交流：contact@example.com

---

<div align="center">

**如果这个项目对你有帮助，请给我们一个 ⭐**

Made with ❤️ by 区域产业经济分析团队

</div>
