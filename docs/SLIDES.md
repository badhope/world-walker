---
marp: true
theme: default
paginate: true
backgroundColor: #fff
style: |
  section {
    font-family: 'Microsoft YaHei', 'Arial', sans-serif;
  }
  h1 {
    color: #667eea;
  }
  h2 {
    color: #764ba2;
  }
  code {
    background: #f5f7fa;
  }
---

# 区域产业经济分析平台

## Regional Industry Economic Analysis Platform

**面向求职的可复用分析工具**

---

<!-- _class: lead -->

# 项目概述

## 🎯 项目定位

一个**模块化**、**配置化**的区域产业经济分析平台

以**深圳半导体产业2025年**为具体示例

---

# 技术架构

## 🏗️ 系统架构

```
regional-economic-analysis-analyzer/
├── backend/          # 后端核心
│   ├── api/         # FastAPI接口
│   ├── analysis/    # 分析模块
│   └── utils/      # 工具模块
├── config/          # 配置系统
│   ├── regions/    # 地区配置
│   └── industries/  # 产业配置
└── examples/        # 示例代码
```

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **Web框架** | FastAPI + Uvicorn |
| **数据处理** | Pandas + NumPy + SciPy |
| **可视化** | Plotly + ECharts |
| **配置管理** | Pydantic-settings |
| **数据采集** | AKShare |
| **项目管理** | Git + Poetry/pip |

---

## 🎨 项目特色

1. ✅ **配置化设计** - 灵活切换地区和产业
2. ✅ **模块化架构** - 独立模块，便于维护
3. ✅ **双视角分析** - 企业端 + 政府端
4. ✅ **经济学模型** - 菲利普斯曲线、柯布-道格拉斯
5. ✅ **交互式可视化** - Plotly动态图表
6. ✅ **RESTful API** - 方便集成和扩展

---

<!-- _class: lead -->

# 功能演示

---

## 1️⃣ 环境检查

```bash
python main.py --mode check
```

**输出结果**:
- ✅ Python版本: 3.11.0
- ✅ 依赖包: 全部安装
- ✅ 目录结构: 完整
- ✅ 配置文件: 已就绪

---

## 2️⃣ 企业端分析

### 📊 分析维度

- **营商成本**: 土地、人力、能源、融资
- **供应链**: 本地化率、响应速度、集聚度
- **政策红利**: 税收优惠、补贴、政务效率

### 📈 关键指标

| 指标 | 数值 |
|------|------|
| 综合成本指数 | 100（全国第4） |
| 政策支持总额 | 158.5亿元 |
| 产业集聚度 | 区位熵2.85 |

---

## 3️⃣ 政府端分析

### 📊 分析维度

- **财政杠杆**: 投入强度、资金效率、杠杆效应
- **产业带动**: 就业、税收、乘数效应
- **产业链**: 覆盖度、瓶颈识别

### 📈 关键指标

| 指标 | 数值 |
|------|------|
| 财政杠杆倍数 | 1.68 |
| 带动就业 | 85,000人 |
| 投入产出比 | 2.35 |

---

## 4️⃣ 综合报告

### 📄 报告内容

- **执行摘要**: 核心发现汇总
- **企业端分析**: 营商环境评估
- **政府端分析**: 政策效果评估
- **产业链分析**: 补链强链建议

### 📊 可视化展示

- KPI数据卡片
- 交互式图表
- 雷达图对比
- 热力图分析

---

## 5️⃣ API服务

### 🔌 接口文档

访问 `http://localhost:8000/docs`

### 📡 主要接口

```bash
# 企业端分析
POST /api/v1/analysis/enterprise

# 政府端分析
POST /api/v1/analysis/government

# 经济学模型
GET /api/v1/inference/models/{model_name}
```

---

<!-- _class: lead -->

# 技术亮点

---

## 💡 亮点1: 模块化架构

```python
# 数据采集模块
from backend.data_collection.nbs_collector import NBSCollector

# 数据处理模块
from backend.data_processing.cleaner import DataCleaner

# 分析模块
from backend.analysis.enterprise_analyzer import EnterpriseAnalyzer

# 可视化模块
from backend.utils.visualizer import Visualizer
```

**优点**: 高内聚、低耦合、易扩展

---

## 💡 亮点2: 配置化设计

```python
# 地区配置
config/regions/shenzhen.py
config/regions/template.py

# 产业配置
config/industries/semiconductor.py
config/industries/template.py

# 分析配置
config/analysis_config.py
```

**优点**: 灵活切换、快速扩展

---

## 💡 亮点3: 经济学模型

```python
# 菲利普斯曲线
inflation = phillips_curve(unemployment_rate)

# 奥肯定律
employment_change = okun_law(gdp_growth)

# 柯布-道格拉斯生产函数
output = cobb_douglas(capital, labor, technology)
```

**优点**: 专业分析、理论支撑

---

## 💡 亮点4: 完整文档

| 文档 | 内容 |
|------|------|
| README.md | 项目主页 |
| USAGE_GUIDE.md | 使用指南 |
| CONFIG_GUIDE.md | 配置详解 |
| EXAMPLE_ANALYSIS.md | 案例分析 |
| DEVELOPER_GUIDE.md | 开发规范 |

**优点**: 易于上手、方便维护

---

<!-- _class: lead -->

# 项目成果

---

## 📊 深圳半导体产业分析结果

### 产业规模

- 总产值: **12,000亿元**
- 占全国比例: **28.5%**
- 企业数量: **2,000家**
- 从业人员: **28.5万人**

### 产业链覆盖

| 环节 | 覆盖度 | 描述 |
|------|--------|------|
| 上游 | 65% | 设计强，设备依赖进口 |
| 中游 | 85% | 制造能力强 |
| 下游 | 95% | 应用场景丰富 |

---

## 🔑 关键发现

### 企业端

1. 综合营商成本指数100，全国第四
2. 产业链配套完善，区位熵2.85
3. 政策支持力度大，满意度过88%

### 政府端

1. 财政杠杆效应显著，1元撬动1.68元
2. 投入产出比2.35，政策效果良好
3. 带动就业85,000人，社会效益明显

---

<!-- _class: lead -->

# 求职优势

---

## 🎯 为什么这个项目有价值？

### 1. 真实场景

- 以深圳半导体产业为案例
- 数据真实，分析有据可依
- 解决实际问题

### 2. 技术完整

- FastAPI、Pandas、Plotly主流技术
- RESTful API设计
- 模块化、配置化工程思维

### 3. 可扩展性

- 方便添加新地区、新产业
- 支持自定义分析维度
- 可集成到其他系统

---

## 📝 项目在简历中如何描述？

```markdown
## 区域产业经济分析平台

技术栈: Python, FastAPI, Pandas, Plotly

核心功能:
- 开发了企业端和政府端双视角分析系统
- 实现了配置化地区产业分析模块
- 集成了菲利普斯曲线等经济学模型
- 生成了交互式可视化报告

项目成果:
- 分析了深圳半导体产业发展现状
- 识别了产业链关键瓶颈环节
- 为政府决策提供数据支持
```

---

<!-- _class: lead -->

# 演示结束

## 感谢聆听！

### 📬 联系方式

- GitHub: github.com/your-org/regional-economic-analysis
- 邮箱: contact@example.com

### 📚 更多资源

- 完整文档: docs/
- 示例代码: examples/
- 配置指南: docs/CONFIG_GUIDE.md

---

**谢谢大家！** 🙏
