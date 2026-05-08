
# national_stats

**AI驱动的经济数据分析平台** - 自动采集、分析、可视化、预警、报告生成

---

## 🌐 Language / 语言

- [中文](#特性)
- [English](#features)

---

## 特性

- 🤖 **多Agent协作** - 基于CrewAI的多智能体系统
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

```python
from backend.agents import CrewManager

manager = CrewManager(provider="ollama", model="llama3.2")
result = manager.run_full_analysis(topic="2024年中国宏观经济分析")
```

## 命令行

```bash
# 获取实时预警
python -c "from backend.agents.roles.alert import get_all_alerts; print(get_all_alerts())"

# 生成分析报告
python -c "from backend.agents.roles.report import generate_and_save_report; print(generate_and_save_report())"
```

## 本地模型

```bash
# 安装Ollama (免费)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

## 项目结构

```
backend/
├── agents/           # AI Agent系统
│   ├── roles/
│   │   ├── data_collector.py    # 数据采集
│   │   ├── analyst.py           # 经济分析
│   │   ├── visualization/       # 可视化
│   │   ├── alert/              # 预警系统
│   │   ├── verification/       # 数据验证
│   │   ├── comparison/         # 对比分析
│   │   └── report/            # 报告生成
│   └── crew_manager.py
└── services/          # 服务层
```

## 许可证

GPL-3.0

---

## Features

- 🤖 **Multi-Agent Collaboration** - CrewAI-based multi-agent system
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

```python
from backend.agents import CrewManager

manager = CrewManager(provider="ollama", model="llama3.2")
result = manager.run_full_analysis(topic="2024 China Macroeconomic Analysis")
```

## Command Line

```bash
# Get real-time alerts
python -c "from backend.agents.roles.alert import get_all_alerts; print(get_all_alerts())"

# Generate analysis report
python -c "from backend.agents.roles.report import generate_and_save_report; print(generate_and_save_report())"
```

## Local Models

```bash
# Install Ollama (free)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

## Project Structure

```
backend/
├── agents/           # AI Agent system
│   ├── roles/
│   │   ├── data_collector.py    # Data collection
│   │   ├── analyst.py           # Economic analysis
│   │   ├── visualization/       # Visualization
│   │   ├── alert/              # Alert system
│   │   ├── verification/       # Data verification
│   │   ├── comparison/         # Comparative analysis
│   │   └── report/            # Report generation
│   └── crew_manager.py
└── services/          # Service layer
```

## License

GPL-3.0
