
# national_stats

**经济数据分析平台** - 实时数据采集、分析、可视化、预警

---

## 🌐 Language / 语言

- [中文](#特性)
- [English](#features)

---

## 特性

- 📊 **实时数据** - 从国家统计局、人民银行获取数据
- 📈 **经济学模型** - 菲利普斯曲线、奥肯定律、柯布-道格拉斯、索洛增长
- 🎨 **可视化** - 热力图、雷达图、仪表盘、省际对比
- ⚠️ **预警系统** - 7项核心指标实时监控
- 📄 **自动报告** - Markdown格式完整分析报告

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

启动 API 服务：

```bash
python -m backend.main
```

访问 API 文档：http://localhost:8001/docs

## 技术架构

所有分析基于经济学公式和统计模型，无需外部 AI 模型

## 项目结构

```
backend/
├── api/              # API 路由
│   └── routes/       # 路由定义
├── core/             # 核心配置
│   ├── config.py     # 配置管理
│   └── database.py   # 数据库管理
├── models/           # 数据模型
│   └── schemas.py    # Pydantic 模型
├── services/         # 服务层
│   ├── data_cleaner.py       # 数据清理
│   ├── data_fetcher.py       # 数据获取
│   ├── inference_engine.py   # 推理引擎
│   └── visualizer.py         # 可视化服务
└── main.py          # FastAPI 主程序入口
```

## 许可证

GPL-3.0

---

## Features

- 📊 **Real-time Data** - Fetch data from NBS and PBOC
- 📈 **Economic Models** - Phillips curve, Okun's law, Cobb-Douglas, Solow growth
- 🎨 **Visualization** - Heatmaps, radar charts, dashboards, provincial comparison
- ⚠️ **Alert System** - Real-time monitoring for 7 core indicators
- 📄 **Auto Reporting** - Complete analysis reports in Markdown

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

Start the API service:

```bash
python -m backend.main
```

Access API documentation: http://localhost:8001/docs

## Technical Architecture

All analysis is based on economic formulas and statistical models, no external AI models required

## Project Structure

```
backend/
├── api/              # API routes
│   └── routes/       # route definitions
├── core/             # core configuration
│   ├── config.py     # config management
│   └── database.py   # database management
├── models/           # data models
│   └── schemas.py    # Pydantic models
├── services/         # service layer
│   ├── data_cleaner.py       # data cleaning
│   ├── data_fetcher.py       # data fetching
│   ├── inference_engine.py   # inference engine
│   └── visualizer.py         # visualization service
└── main.py          # FastAPI main entry point
```

## License

GPL-3.0
