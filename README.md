# 🚀 通用数据分析系统 - 完整数据分析师作品集

**一个通用的、生产级的数据驱动分析框架，支持任意行业和地区，包含完整机器学习功能！**

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg">
  <img src="https://img.shields.io/badge/ML-Scikit--learn%20%7C%20Prophet%20%7C%20XGBoost-orange.svg">
  <img src="https://img.shields.io/badge/License-MIT-green.svg">
</div>

---

## ✨ 核心亮点

- **🎯 完全通用化**：支持任意行业、任意地区，通过配置定制
- **🤖 完整机器学习库**：8+算法（LinearRegression、RandomForest、GBDT、Prophet等）
- **⚡ AutoML自动优化**：自动模型选择、自动超参数调优
- **📊 多源数据支持**：CSV、Excel、JSON、SQL数据库
- **🎨 模块化配置**：YAML配置文件，灵活定义业务逻辑
- **📈 生产级质量**：完整错误处理、测试覆盖、可扩展架构

---

## 🚀 3分钟快速开始

### 1. 一键运行演示

```bash
python test_universal_system.py
```

### 2. 基础使用

```python
from backend import UniversalAnalyzer, create_sample_data

# 创建分析器
analyzer = UniversalAnalyzer()

# 创建示例数据
df = create_sample_data()

# 加载数据
dataset = analyzer.load_data_from_dataframe(df, name='my_data')

# 运行完整分析
result = analyzer.analyze(
    run_ml=True,
    target_column='market_size',
    feature_columns=['land_price', 'labor_cost', 'energy_cost'],
    model_names=['random_forest', 'gbdt', 'linear_regression']
)

# 查看结果
print(f"最佳模型: {result.ml_result.best_model.model_name}")
print(f"R²: {result.ml_result.best_model.metrics.r2:.4f}")
```

### 3. 查看文档

- **完整使用指南**：[UNIVERSAL_FRAMEWORK.md](UNIVERSAL_FRAMEWORK.md)
- **配置系统文档**：查看 `configs/default.yaml`
- **简历项目描述**：[RESUME_PROJECT.md](RESUME_PROJECT.md)
- **项目展示页面**：打开 [PROJECT_SHOWCASE.html](PROJECT_SHOWCASE.html)

---

## 📊 可用机器学习模型

| 模型 | 名称 | 特点 |
|------|------|------|
| `linear_regression` | 线性回归 | 快速、可解释 |
| `ridge` | 岭回归 | L2正则化 |
| `lasso` | Lasso回归 | L1正则化、特征选择 |
| `random_forest` | 随机森林 | 高准确率、抗过拟合 |
| `gbdt` | 梯度提升树 | 高性能集成学习 |
| `svr` | 支持向量回归 | 非线性建模 |
| `knn` | K近邻回归 | 简单直观 |
| `prophet` | Prophet时间序列 | 专业时间序列预测 |
| `xgboost` | XGBoost (可选) | 极速、高性能 |
| `lightgbm` | LightGBM (可选) | 高性能、轻量 |

---

## 📁 项目结构

```
/workspace/
├── backend/                    # 核心框架
│   ├── core/
│   │   ├── config.py          # 配置系统
│   │   ├── data_manager.py    # 数据管理
│   │   └── analyzer.py        # 通用分析器
│   └── ml/
│       ├── models.py          # 机器学习模型库
│       └── trainer.py         # AutoML训练器
├── configs/                   # 配置文件
│   └── default.yaml
├── data/                      # 数据目录
├── models/                    # 保存的模型
├── output/                    # 输出结果
├── frontend/                  # 前端展示
├── notebooks/                 # Jupyter notebooks
├── test_universal_system.py  # 测试脚本
├── quick_demo.py            # 快速演示
├── UNIVERSAL_FRAMEWORK.md    # 完整使用指南
├── PROJECT_SHOWCASE.html    # 项目展示页面
├── RESUME_PROJECT.md        # 简历项目描述
├── requirements.txt          # 依赖列表
└── README.md                # 本文件
```

---

## 🛠️ 安装依赖

```bash
# 核心依赖
pip install pandas numpy scikit-learn joblib pyyaml prophet

# 完整安装（推荐）
pip install -r requirements.txt
```

---

## 🎯 核心功能详解

### 1. 配置系统

通过YAML配置文件定制任意行业分析：

```yaml
project_name: my_analysis
industry:
  industry_name: 零售行业
  dimensions:
    - name: cost
      weight: 0.4
      metrics: [rent, labor_cost]
ml:
  target_metric: revenue
  models: [random_forest, gbdt, linear_regression]
```

### 2. 数据管理

支持多种数据源：

```python
from backend import get_data_manager

data_manager = get_data_manager()

# 从不同格式加载
dataset = data_manager.load_csv("data.csv")
dataset = data_manager.load_excel("data.xlsx")
dataset = data_manager.load_json("data.json")
dataset = data_manager.load_database("db.sqlite", "table")

# 数据处理
cleaned = data_manager.clean_data(dataset)
normalized = data_manager.normalize_data(dataset)
```

### 3. AutoML自动机器学习

```python
from backend import AutoML

automl = AutoML(
    target_column='market_size',
    feature_columns=['land_price', 'labor_cost', 'energy_cost'],
    model_names=['random_forest', 'gbdt', 'linear_regression'],
    hyperparameter_tuning=True,  # 自动调优
    test_size=0.2
)

result = automl.fit(df)
print(f"最佳模型: {result.best_model.model_name}")
print(f"R²: {result.best_model.metrics.r2}")
```

---

## 📈 原始项目（半导体选址）

这个通用框架是从原始的半导体企业选址分析项目演进而来。

### 查看原始项目

- **交互式Dashboard**：[frontend/analysis_dashboard.html](frontend/analysis_dashboard.html)
- **Notebook分析**：[notebooks/01_EDA_AND_INSIGHTS.py](notebooks/01_EDA_AND_INSIGHTS.py)
- **原始后端**：[backend/data/](backend/data/), [backend/analysis/](backend/analysis/)

### 运行原始演示

```bash
python run_full_demo.py
```

---

## 🎓 这对数据分析师面试有什么帮助？

### 展示技术深度

1. **完整ML pipeline**：数据清洗 → 特征工程 → 模型训练 → 评估 → 部署
2. **多算法掌握**：显示你知道何时、如何使用不同算法
3. **AutoML能力**：展示你理解模型选择和超参数调优
4. **工程能力**：模块化设计、配置系统、可复用架构

### 准备面试问题

查看 [RESUME_PROJECT.md](RESUME_PROJECT.md) 获取：
- 项目描述（可以直接复制到简历）
- 常见面试问题和答案
- 技术亮点总结

---

## 📖 文档索引

| 文档 | 说明 |
|------|------|
| [UNIVERSAL_FRAMEWORK.md](UNIVERSAL_FRAMEWORK.md) | 完整使用指南（必读） |
| [PROJECT_SHOWCASE.html](PROJECT_SHOWCASE.html) | 项目展示页面（视觉冲击） |
| [RESUME_PROJECT.md](RESUME_PROJECT.md) | 简历项目描述 |
| [configs/default.yaml](configs/default.yaml) | 配置文件示例 |
| [README.md](README.md) | 本文档 |

---

## 🏆 项目成就

- **✨ 8+机器学习算法** 完整实现
- **🎯 通用化架构** 支持任意行业
- **📦 生产级代码** 完整错误处理和模块化
- **📊 可视化展示** 交互式Dashboard和展示页面
- **🎓 面试准备** 完整文档和常见问题

---

## 🤝 扩展和定制

### 添加新模型

在 `backend/ml/models.py` 中：

```python
class MyModel(BaseModel):
    def __init__(self):
        super().__init__('my_model')
    
    def build_model(self, **kwargs):
        return MyMLAlgorithm(**kwargs)
    
    def get_default_params(self):
        return {'param1': 10}
    
    def get_param_grid(self):
        return {'param1': [5, 10, 20]}

MODEL_REGISTRY['my_model'] = MyModel()
```

### 定制行业配置

在 `configs/` 目录下创建新的YAML文件，然后：

```python
analyzer = UniversalAnalyzer(config_name='my_industry')
```

---

## 📜 许可证

MIT License - 完全自由使用、修改和分发！

---

## 🎉 开始使用

```bash
# 1. 运行演示
python test_universal_system.py

# 2. 查看展示页面
open PROJECT_SHOWCASE.html

# 3. 阅读文档
cat UNIVERSAL_FRAMEWORK.md
```

---

**祝数据顺利！** 🚀✨

---
