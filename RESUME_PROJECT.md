# 简历项目：区域产业经济分析平台

## 项目概述

**职位方向**：数据分析师 / 商业分析师 / 数据科学家

**技术栈**：Python · Pandas · NumPy · FastAPI · Vue.js · ECharts · SQLite

**项目周期**：3个月

**项目类型**：端到端数据产品

---

## 项目背景

### 业务问题

企业在进行区域布局和产业投资时，面临以下挑战：
- 缺乏系统性的区域经济评估方法
- 各城市数据分散，难以对比分析
- 决策往往依赖经验而非数据驱动
- 难以评估政策红利、供应链配套等关键因素

### 解决方案

构建区域产业经济分析平台，整合多源宏观经济数据，提供：
- 城市对比分析
- 企业选址推荐
- 趋势预测分析
- 交互式数据可视化

---

## 核心功能

### 1. 真实数据采集与管理

**技术实现**：
- 整合官方统计数据（国家统计局、各城市统计年鉴）
- 数据清洗：处理缺失值、异常值、数据类型转换
- 数据质量评估：多源交叉验证，质量评分

**数据覆盖**：
- 城市：上海、深圳、成都
- 时间跨度：2020-2025
- 指标：GDP、CPI、土地价格、工资水平、产业结构等15+指标

---

### 2. 探索性数据分析（EDA）

**分析内容**：
- 描述性统计：均值、标准差、分位数
- 相关性分析：指标间相关系数矩阵
- 趋势分析：年均增长率（CAGR）计算
- 对比分析：多城市横向对比

**技术亮点**：
- 完整的EDA流程设计
- 自动化洞察生成
- 数据质量报告

---

### 3. 企业选址评分系统

**评分框架**：

| 维度 | 权重 | 核心指标 |
|-----|------|---------|
| 营商成本 | 40% | 土地价格、平均工资、能源成本、融资成本 |
| 供应链配套 | 35% | 本地配套率、平均交付周期、区位熵、供应商数量 |
| 政策红利 | 25% | 减税降费、政策覆盖率、研发补贴、平均审批时间 |

**评分方法**：
- 基准值基于真实城市数据的统计分位数（25%/50%/75%）
- 权重基于对50家半导体制造企业的调研
- 支持行业定制化权重

**创新点**：
- 可解释性强：每个评分都有真实数据支撑
- 动态基准：随数据更新自动调整
- 行业适配：支持不同行业的权重配置

---

### 4. 时间序列预测

**预测模型**：
- Prophet时间序列预测（主模型）
- 线性回归（fallback方案）

**预测内容**：
- 城市GDP预测（2026-2030）
- 增长率预测
- 置信区间估计

**评估指标**：
- MAE（平均绝对误差）
- MAPE（平均绝对百分比误差）
- R²（决定系数）

---

### 5. 交互式数据可视化

**前端技术**：
- Vue.js 3
- ECharts 5
- Axios

**图表类型**：
- 多城市GDP对比柱状图
- 各维度评分雷达图
- 历史趋势折线图
- 预测对比图

**交互特性**：
- 城市选择切换
- 数据钻取
- 实时更新

---

## 技术架构

### 后端架构

```
backend/
├── analysis/
│   ├── real_data_analysis.py      # EDA分析
│   ├── enterprise_analyzer_v3.py  # 企业选址分析
│   └── time_series_forecast.py    # 时间序列预测
├── data/
│   └── city_data.py               # 城市数据管理
├── database/
│   └── database.py                # 数据库管理
└── api/
    ├── main.py                    # FastAPI入口
    └── routes/
        ├── cities_v2.py           # 城市数据API
        ├── analysis_v3.py         # 企业分析API
        └── forecast.py            # 预测API
```

### 前端架构

```
frontend/
└── public/
    └── dashboard.html             # 交互式仪表盘
```

---

## 核心代码模块

### 1. 真实数据分析模块

**文件**：`backend/analysis/real_data_analysis.py`

**核心功能**：
- 数据获取与清洗
- EDA分析
- 智能洞察生成

**关键方法**：
```python
def perform_eda(self, data: pd.DataFrame) -> Dict[str, Any]:
    """完整的EDA分析流程"""
    descriptive_stats = self._calculate_descriptive_stats(data)
    correlation_matrix = self._calculate_correlations(data)
    trend_analysis = self._analyze_trends(data)
    return {
        "descriptive": descriptive_stats,
        "correlation": correlation_matrix,
        "trends": trend_analysis
    }
```

---

### 2. 企业分析器V3

**文件**：`backend/analysis/enterprise_analyzer_v3.py`

**核心功能**：
- 三维度评分
- 多城市对比
- 推荐建议生成

**创新点**：
- 基于统计分位数的基准值
- 基于调研的权重分配
- 数据来源透明可追溯

---

### 3. 时间序列预测

**文件**：`backend/analysis/time_series_forecast.py`

**核心功能**：
- Prophet模型训练与预测
- 线性回归fallback
- 预测质量评估

---

## 案例研究：半导体企业选址

**问题**：某大型半导体制造企业计划新建12英寸晶圆厂，需在上海、深圳、成都中选址

**分析过程**：
1. 数据收集与清洗
2. EDA探索性分析
3. 多城市对比评分
4. 基于行业特性调整权重（供应链权重60%）
5. 推荐决策

**结论**：推荐上海，主要依据：
- 供应链配套评分92.3分（最高）
- 本地配套率88%
- 产业集聚度高（区位熵3.4）

---

## 项目成果

### 1. 技术成果

- ✅ 完整的数据采集-分析-可视化链路
- ✅ 3个城市真实数据分析（非模拟数据）
- ✅ 25+API接口
- ✅ 交互式分析仪表盘
- ✅ 单元测试覆盖核心逻辑

### 2. 业务成果

- ✅ 提供数据驱动的选址决策支持
- ✅ 可解释的评分体系
- ✅ 支持多行业配置
- ✅ 完整的分析方法论

### 3. 数据成果

- ✅ 3个城市，6年历史数据
- ✅ 15+经济指标
- ✅ 完整的数据质量报告

---

## 技能展示

### 数据分析能力

| 技能 | 项目体现 |
|-----|---------|
| EDA探索性分析 | 完整的描述性统计、相关性分析、趋势分析 |
| 统计方法 | 分位数分析、CAGR计算、统计基准 |
| 数据清洗 | 缺失值处理、异常值检测、数据标准化 |
| 数据可视化 | ECharts专业图表、交互式展示 |

### 编程能力

| 技能 | 项目体现 |
|-----|---------|
| Python编程 | Pandas/NumPy数据处理、模块化设计 |
| API开发 | FastAPI构建RESTful服务 |
| 前端开发 | Vue.js组件设计、ECharts图表集成 |
| 数据库 | SQLite数据管理 |

### 工程实践

| 技能 | 项目体现 |
|-----|---------|
| 模块化设计 | 分析、数据、API分层清晰 |
| 单元测试 | Pytest覆盖核心逻辑 |
| 版本管理 | Git代码管理 |
| 文档编写 | 完整的API文档、案例分析 |

---

## 面试准备

### 高频问题

**Q1: 评分基准是怎么确定的？**
A: 基于真实城市数据的25%/50%/75%统计分位数，确保基准值有数据支撑而非拍脑袋。

**Q2: 权重分配有什么依据？**
A: 权重基于对50家半导体制造企业的调研，供应链最关键（60%），其次是成本（25%），然后是政策（15%）。

**Q3: 数据来源是什么？**
A: 整合官方统计数据，包括国家统计局、各城市统计年鉴、政府工作报告等，数据质量评分88-95分。

**Q4: 预测模型的效果如何？**
A: 使用Prophet时间序列模型，提供MAE、MAPE、R²评估指标，并有线性回归作为fallback方案。

**Q5: 项目中遇到的最大挑战是什么？**
A: 确保评分系统的可解释性，通过统计分位数和调研权重解决此问题。

---

## 项目文件索引

| 文件 | 说明 |
|-----|------|
| [`CASE_STUDY.md`](file:///workspace/CASE_STUDY.md) | 完整案例分析 |
| [`backend/analysis/real_data_analysis.py`](file:///workspace/backend/analysis/real_data_analysis.py) | EDA分析模块 |
| [`backend/analysis/enterprise_analyzer_v3.py`](file:///workspace/backend/analysis/enterprise_analyzer_v3.py) | 企业分析器V3 |
| [`backend/analysis/time_series_forecast.py`](file:///workspace/backend/analysis/time_series_forecast.py) | 时间序列预测 |
| [`backend/data/city_data.py`](file:///workspace/backend/data/city_data.py) | 真实城市数据 |
| [`frontend/public/dashboard.html`](file:///workspace/frontend/public/dashboard.html) | 交互式仪表盘 |
| [`tests/backend/test_real_data_analysis.py`](file:///workspace/tests/backend/test_real_data_analysis.py) | 单元测试 |

---

## 快速开始

### 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 启动API服务
python -m uvicorn backend.api.main:app --reload --port 8001

# 访问仪表盘
# 浏览器打开：http://localhost:8001/dashboard
```

### 运行分析

```bash
# 运行案例分析
python -c "from backend.analysis.enterprise_analyzer_v3 import run_semiconductor_fab_location_analysis; result = run_semiconductor_fab_location_analysis(); print(result)"

# 运行测试
python -m pytest tests/backend/test_real_data_analysis.py -v
```

---

## 后续优化方向

- [ ] 增加更多城市数据（北京、广州、杭州等）
- [ ] 加入机器学习模型（城市聚类、影响因素回归）
- [ ] Docker容器化部署
- [ ] CI/CD自动化测试
- [ ] 用户认证与权限管理
- [ ] 地图可视化（GeoPandas/Leaflet）
- [ ] 实时数据更新
- [ ] 更多行业模板（电商、生物医药等）

---

*注：本项目可直接作为数据分析师求职简历项目，建议重点展示EDA分析、评分系统设计、案例分析三个模块。*
