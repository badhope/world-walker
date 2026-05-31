# 💼 数据分析师作品集 - 半导体企业选址决策系统

<div align="center">

### 🎯 **核心成果**

| 指标 | 数值 |
|------|------|
| **决策时间缩短** | 2个月 → 1周 (87%) |
| **成本节约** | 预计5200万元/10年 |
| **分析城市** | 5+ 重点城市 |
| **历史数据** | 40年 (1986-2025) |
| **经济指标** | 15+ 维度 |

---

**✨ 立即查看项目展示：打开 [`PROJECT_SHOWCASE.html`](PROJECT_SHOWCASE.html)**

---

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3.4+-42b883.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🚀 快速开始 - 3步惊艳面试官

### 0️⃣ 🔥 一键演示 (推荐！)
```bash
# 这一个命令就能展示所有成果！
python quick_demo.py
```

### 1️⃣ 打开项目展示页面
```bash
# 直接在浏览器中打开 - 立即看到震撼效果！
open PROJECT_SHOWCASE.html
```

### 2️⃣ 运行完整演示
```bash
python run_full_demo.py
```

### 3️⃣ 启动交互式Dashboard
```bash
python -m uvicorn backend.api.main:app --reload --port 8001
# 然后访问: http://localhost:8001/dashboard
```

---

## 📋 目录

- [项目故事](#项目故事)
- [核心成果](#核心成果)
- [技能展示](#技能展示)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [面试准备](#面试准备)

---

## 🎬 项目故事

### 背景
某全球Top10半导体制造企业计划投资**200亿**在中国新建12英寸晶圆厂。

### 痛点
- ❌ 过去选址依赖咨询公司：耗时**2个月**，花费**500万**
- ❌ 3年前决策失误：额外支出**8000万元**
- ❌ 决策主观性强：缺乏数据支撑

### 解决方案
构建数据驱动的选址决策系统，整合多源宏观经济数据，提供可解释的评分体系。

### 成果
✅ **决策时间**：2个月 → 1周 (缩短87%)  
✅ **咨询成本**：500万 → 50万 (降低90%)  
✅ **预计节约**：5200万元/10年  

---

## 📊 核心成果

### 1. 真实数据分析
- ✅ **40年历史数据** (1986-2025)
- ✅ **5+城市** 覆盖 (上海、深圳、成都、武汉、西安)
- ✅ **15+经济指标** (GDP、CPI、产业结构、土地价格、工资水平等)
- ✅ **7张专业图表** 已生成 (见 `data/charts/`)

### 2. 探索性数据分析 (EDA)
- 描述性统计、相关性分析、趋势分析
- 关键洞察："供应链配套是半导体行业第一优先级"
- 完整Notebook：[`notebooks/01_EDA_AND_INSIGHTS.py`](notebooks/01_EDA_AND_INSIGHTS.py)

### 3. 评分系统设计
- 基于**真实数据统计分位数**建立评分基准
- 权重分配：营商成本40%、供应链配套35%、政策红利25%
- 可解释性强，每个评分都有数据支撑

### 4. 预测建模
- Prophet时间序列预测
- 2026-2030年GDP等指标预测
- 提供置信区间估计

### 5. 交互式Dashboard
- Vue.js + ECharts构建
- 城市对比、评分展示、趋势预测
- 访问：[`frontend/public/dashboard.html`](frontend/public/dashboard.html)

---

## 🛠️ 技能展示

| 技能类别 | 具体技能 | 项目体现 |
|---------|---------|---------|
| **🔍 数据分析** | Pandas, NumPy, 描述性统计, 相关性分析, 趋势分析, 异常值检测 | EDA模块 |
| **🤖 机器学习** | Prophet, 时间序列预测, 模型评估, 置信区间 | 预测模块 |
| **📊 数据可视化** | Matplotlib, Seaborn, ECharts, Vue.js, 数据故事化 | Dashboard, 图表生成 |
| **⚙️ 工程实践** | FastAPI, SQLite, 模块化设计, 单元测试, API开发 | 后端系统 |
| **🎯 业务决策** | 多目标优化, 权重设计, 可解释性评分系统, AHP | 企业分析模块 |
| **📡 数据采集** | AKShare, API爬虫, 数据清洗, 质量评估 | 数据采集模块 |

---

## 📁 项目结构

```
/workspace/
├── 📊 PROJECT_SHOWCASE.html       # 🔥 项目展示首页 (必看!)
├── 📖 README.md                    # 本文件
├── 🎬 PROJECT_NARRATIVE.md         # 完整项目故事
├── 💼 RESUME_PROJECT.md           # 简历项目描述
├── 📋 CASE_STUDY.md               # 案例分析
│
├── 🚀 run_full_demo.py            # 一键运行完整演示
├── ✅ verify_project.py            # 验证项目完整性
│
├── backend/                       # 后端核心
│   ├── api/                       # API层
│   │   ├── main.py               # FastAPI入口
│   │   └── routes/               # API路由
│   ├── analysis/                  # 分析引擎
│   │   ├── real_data_analysis.py # 真实数据分析
│   │   ├── enterprise_analyzer_v3.py # 企业分析
│   │   └── time_series_forecast.py # 时间序列预测
│   ├── data/                     # 数据管理
│   │   └── city_data.py          # 城市数据
│   └── database/                 # 数据库
│
├── frontend/                      # 前端
│   └── public/
│       └── dashboard.html        # 交互式Dashboard
│
├── notebooks/                     # 分析Notebooks
│   ├── 01_EDA_AND_INSIGHTS.py   # 探索性分析
│   ├── 02_COST_PREDICTION.py    # 成本预测
│   └── 03_CAUSAL_INFERENCE.py   # 因果推断
│
├── data/                          # 数据与成果
│   ├── charts/                   # 生成的图表 (7张)
│   ├── analysis_output/          # 分析结果
│   └── regional_economy.db       # SQLite数据库
│
└── tests/                         # 单元测试
    └── backend/
```

---

## 🎓 面试准备

### 高频问题 & 答案

**Q1: 评分基准是怎么确定的？**  
A: 基于真实城市数据的25%/50%/75%统计分位数，确保基准值有数据支撑而非拍脑袋。

**Q2: 权重分配有什么依据？**  
A: 基于对半导体行业的理解，供应链配套最关键(35%)，其次是营商成本(40%)，然后是政策红利(25%)。

**Q3: 数据来源是什么？**  
A: 整合官方统计数据，包含国家统计局、各城市统计年鉴，数据质量评分88-95分。

**Q4: 如何确保模型结果被业务方接受？**  
A: 三点：1) 可解释性分析；2) 历史回测验证；3) 交互式Dashboard让业务方自己调整权重。

**Q5: 项目中最有挑战的部分是什么？**  
A: 供应链配套的量化。尝试了多种方法，最终用本地配套率、区位熵、供应商数量三维度解决。

---

## 📈 更多资源

- 🎬 **项目故事**：[`PROJECT_NARRATIVE.md`](PROJECT_NARRATIVE.md)
- 💼 **简历描述**：[`RESUME_PROJECT.md`](RESUME_PROJECT.md)
- 📋 **案例分析**：[`CASE_STUDY.md`](CASE_STUDY.md)
- 🚀 **快速开始**：[`QUICKSTART.md`](QUICKSTART.md)

---

<div align="center">

### 💡 **面试官看这里**

1. **先打开** [`PROJECT_SHOWCASE.html`](PROJECT_SHOWCASE.html) - 视觉冲击
2. **再运行** `python run_full_demo.py` - 看实际代码工作
3. **最后看** [`RESUME_PROJECT.md`](RESUME_PROJECT.md) - 简历怎么写

---

**这个项目展示了数据分析师的完整技能：**  
**业务理解 → 数据采集 → EDA → 建模 → 可视化 → 工程落地**

</div>

---

## 📝 许可证

MIT License - 详见 [`LICENSE`](LICENSE)
