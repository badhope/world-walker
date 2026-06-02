# 通用数据分析系统 - 完整使用指南

## 🚀 项目概述

这是一个完整的、可通用的数据分析框架，支持任意行业和地区的数据驱动分析。

### 核心特性

- **完全通用化设计**：支持任意行业、任意地区
- **完整ML模型库**：8+机器学习算法（LinearRegression、RandomForest、GBDT、Prophet等）
- **AutoML自动优化**：自动模型选择、自动超参数调优
- **模块化配置**：YAML配置文件，灵活定义行业、指标、权重
- **多源数据支持**：CSV、Excel、JSON、SQL数据库
- **生产级质量**：完整的错误处理、测试覆盖

---

## 📋 快速开始（3分钟）

### 1. 运行演示

```bash
# 一键运行完整演示
python -c "from backend import quick_start_demo; quick_start_demo()"

# 或者运行测试脚本
python test_universal_system.py
```

### 2. 基础使用

```python
from backend import UniversalAnalyzer, create_sample_data

# 创建分析器
analyzer = UniversalAnalyzer()

# 创建示例数据（或加载你自己的数据）
df = create_sample_data()

# 加载数据
dataset = analyzer.load_data_from_dataframe(df, name='my_data')

# 运行完整分析（包含机器学习）
result = analyzer.analyze(
    run_ml=True,
    target_column='market_size',  # 你要预测的指标
    feature_columns=['land_price', 'labor_cost', 'energy_cost'],  # 特征
    model_names=['random_forest', 'gbdt', 'linear_regression'],  # 模型
    test_size=0.2
)

# 查看结果
print(f"最佳模型: {result.ml_result.best_model.model_name}")
print(f"R²: {result.ml_result.best_model.metrics.r2}")
```

---

## 🎯 核心模块详解

### 1. 配置系统 (`backend.core.config`)

#### 创建自定义配置

```python
from backend import get_config_manager

config_manager = get_config_manager()

# 配置已经在初始化时创建在 configs/default.yaml
config = config_manager.load_config()

print(f"项目名: {config.project_name}")
print(f"行业: {config.industry.industry_name}")
print(f"地区: {config.regions}")
print(f"ML模型: {config.ml_config.models}")
```

#### YAML配置结构

```yaml
project_name: default_project
regions:
  - 北京
  - 上海
  - 广州
  - 深圳

industry:
  industry_id: default
  industry_name: 通用行业
  industry_type: services
  description: 适用于各类企业的通用分析模板
  dimensions:
    - name: cost
      display_name: 成本维度
      description: 评估运营成本
      weight: 0.40
      metrics:
        - land_price
        - labor_cost
        - energy_cost
      metric_weights:
        land_price: 0.35
        labor_cost: 0.45
        energy_cost: 0.20
      higher_is_better:
        land_price: false
        labor_cost: false
        energy_cost: false
  
  metrics:
    land_price:
      name: land_price
      display_name: 土地价格
      unit: 元/㎡
      description: 工业用地价格
      data_source: 统计年鉴
    market_size:
      name: market_size
      display_name: 市场规模
      unit: 亿元
      description: GDP规模
      data_source: 统计局
  
  success_metrics:
    - market_size
    - talent_pool
    - tax_incentive
  
  data_requirements:
    - land_price
    - labor_cost
    - energy_cost
    - market_size
    - talent_pool
    - infrastructure

ml:
  models:
    - linear_regression
    - ridge
    - lasso
    - random_forest
    - gbdt
    - svr
    - knn
    - prophet
  target_metric: market_size
  feature_columns:
    - land_price
    - labor_cost
    - energy_cost
    - talent_pool
    - infrastructure
  time_column: year
  id_column: region_id
  train_size: 0.8
  validation_size: 0.2
  hyperparameter_tuning: true
  cross_validation_folds: 5
```

---

### 2. 数据管理 (`backend.core.data_manager`)

#### 支持的数据格式

```python
from backend import get_data_manager

data_manager = get_data_manager()

# 从CSV加载
dataset = data_manager.load_csv("your_data.csv", name="my_data")

# 从Excel加载
dataset = data_manager.load_excel("your_data.xlsx", sheet_name="Sheet1")

# 从JSON加载
dataset = data_manager.load_json("your_data.json")

# 从SQLite加载
dataset = data_manager.load_database("your_database.db", "your_table")
```

#### 数据处理

```python
# 数据清洗
cleaned_dataset = data_manager.clean_data(
    dataset,
    remove_na=True,
    remove_outliers=True,
    outlier_threshold=3.0
)

# 数据标准化
normalized_dataset = data_manager.normalize_data(
    dataset,
    method="minmax"  # 或 "zscore"
)

# 计算基准值
benchmarks = data_manager.calculate_benchmarks(
    dataset,
    metric="market_size",
    method="percentile"  # "percentile" 或 "mean_std"
)

# 保存数据集
data_manager.save_dataset(dataset, format="csv")  # 或 "excel", "json", "database"
```

---

### 3. 机器学习系统 (`backend.ml`)

#### 可用模型列表

| 模型名 | 描述 | 特点 |
|--------|------|------|
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

#### 使用单个模型

```python
from backend import get_model

# 获取模型
model = get_model("random_forest")

# 使用默认参数训练
df = create_sample_data()
X = df[['land_price', 'labor_cost', 'energy_cost']]
y = df['market_size']

model.fit(X, y)

# 预测
predictions = model.predict(X)

# 评估
metrics = model.evaluate(X_test, y_test)
print(f"MAE: {metrics.mae}")
print(f"RMSE: {metrics.rmse}")
print(f"MAPE: {metrics.mape}")
print(f"R²: {metrics.r2}")

# 获取特征重要性
feature_importance = model.get_feature_importance()
print(feature_importance)

# 保存/加载模型
model.save("my_model.pkl")
loaded_model = get_model("random_forest").load("my_model.pkl")
```

#### 使用AutoML（自动模型选择）

```python
from backend import AutoML

# 创建AutoML
automl = AutoML(
    target_column='market_size',
    feature_columns=['land_price', 'labor_cost', 'energy_cost'],
    model_names=['random_forest', 'gbdt', 'linear_regression'],
    test_size=0.2,
    random_state=42,
    hyperparameter_tuning=True  # 开启自动超参数调优
)

# 训练
result = automl.fit(df)

# 获取最佳模型
best_model = result.best_model
print(f"最佳模型: {best_model.model_name}")
print(f"R²: {best_model.metrics.r2}")

# 获取所有模型对比
for model_result in result.all_results:
    print(f"{model_result.model_name}: R²={model_result.metrics.r2}")

# 使用最佳模型预测
predictions = automl.predict(new_data)

# 获取特征重要性
feature_importance = automl.get_feature_importance()
```

#### 超参数调优

```python
from backend import AutoML

# 开启自动调优
automl = AutoML(
    target_column='market_size',
    feature_columns=features,
    model_names=['random_forest', 'gbdt'],
    hyperparameter_tuning=True,
    tuning_method='grid',  # 'grid' 或 'random'
    tuning_iterations=50,  # 随机搜索迭代次数
    cross_validation_folds=5
)

result = automl.fit(df)

# 每个模型的最佳超参数
best_model = result.best_model
if best_model.hyperparameters:
    print("最佳超参数:", best_model.hyperparameters)
```

---

### 4. 通用分析器 (`backend.core.analyzer`)

#### 完整分析流程

```python
from backend import UniversalAnalyzer, create_sample_data

# 1. 初始化
analyzer = UniversalAnalyzer(config_name='default')

# 2. 加载数据
df = create_sample_data()
analyzer.load_data_from_dataframe(df, name='my_data')

# 3. 数据预处理
analyzer.preprocess_data(
    clean=True,
    normalize=False
)

# 4. 计算基准
benchmarks = analyzer.calculate_benchmarks()

# 5. 运行机器学习
ml_result = analyzer.run_ml_analysis(
    target_column='market_size',
    feature_columns=['land_price', 'labor_cost', 'energy_cost'],
    model_names=['random_forest', 'gbdt', 'linear_regression'],
    test_size=0.2
)

# 6. 生成洞察
insights = analyzer.generate_insights()

# 7. 运行完整分析（一键完成）
result = analyzer.analyze(run_ml=True)

# 8. 保存结果
analyzer.save_result(output_dir='./output')
```

---

## 🎨 行业定制示例

### 示例1: 零售行业分析

创建配置文件 `configs/retail.yaml`:

```yaml
project_name: retail_analysis
regions:
  - 北京
  - 上海
  - 广州

industry:
  industry_id: retail
  industry_name: 零售行业
  industry_type: retail
  description: 零售门店选址分析
  dimensions:
    - name: foot_traffic
      display_name: 客流维度
      weight: 0.4
      metrics: [population_density, avg_foot_traffic]
      metric_weights: {population_density: 0.5, avg_foot_traffic: 0.5}
      higher_is_better: {population_density: true, avg_foot_traffic: true}
    
    - name: cost
      display_name: 成本维度
      weight: 0.3
      metrics: [rent, labor_cost]
      metric_weights: {rent: 0.6, labor_cost: 0.4}
      higher_is_better: {rent: false, labor_cost: false}

ml:
  target_metric: revenue
  feature_columns: [population_density, rent, labor_cost, competitor_count]
  models: [random_forest, gbdt, linear_regression]
```

使用自定义配置:

```python
analyzer = UniversalAnalyzer(config_name='retail')
result = analyzer.analyze(run_ml=True)
```

### 示例2: 科技企业选址

```python
# configs/tech.yaml
industry:
  industry_name: 科技行业
  dimensions:
    - name: talent
      display_name: 人才维度
      weight: 0.5
      metrics: [graduates_per_year, tech_workers_count]
      metric_weights: {graduates_per_year: 0.6, tech_workers_count: 0.4}
      higher_is_better: true
```

---

## 📊 分析结果解读

### 模型评估指标

| 指标 | 全称 | 说明 | 目标 |
|------|------|------|------|
| MAE | Mean Absolute Error | 平均绝对误差 | 越小越好 |
| RMSE | Root Mean Squared Error | 均方根误差 | 越小越好 |
| MAPE | Mean Absolute Percentage Error | 平均绝对百分比误差 | 越小越好 |
| R² | R-Squared | 决定系数，解释方差百分比 | 越大越好(0-1) |

### 选择最佳模型

一般建议:
- **R² > 0.8**: 模型非常优秀
- **0.6 < R² < 0.8**: 模型效果良好
- **R² < 0.6**: 需要优化特征或模型

---

## 🛠️ 高级功能

### 集成学习预测

```python
# 用多个模型的集成预测
automl = AutoML(...)
result = automl.fit(df)

# 平均法集成
predictions_mean = automl.trainer.get_ensemble_prediction(X, method='mean')

# 中位数法集成
predictions_median = automl.trainer.get_ensemble_prediction(X, method='median')

# 加权平均（基于R²）
predictions_weighted = automl.trainer.get_ensemble_prediction(X, method='weighted')
```

### 时间序列专用分析

```python
from backend import TimeSeriesModelTrainer, TrainingConfig

config = TrainingConfig(
    model_names=['prophet', 'linear_regression'],
    target_column='market_size',
    feature_columns=['year', 'trend'],
    time_column='year',
    is_time_series=True
)

trainer = TimeSeriesModelTrainer(config)
```

---

## 📁 项目结构

```
/workspace/
├── backend/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # 配置系统
│   │   ├── data_manager.py    # 数据管理
│   │   └── analyzer.py        # 通用分析器
│   └── ml/
│       ├── __init__.py
│       ├── models.py          # 机器学习模型
│       └── trainer.py         # 训练器和AutoML
├── configs/                   # YAML配置文件
├── data/                      # 数据目录
│   └── processed/
├── models/                    # 保存的模型
├── output/                    # 输出结果
├── requirements.txt           # 依赖列表
├── test_universal_system.py   # 测试脚本
└── UNIVERSAL_FRAMEWORK.md     # 本文件
```

---

## 📦 依赖安装

```bash
# 核心依赖
pip install pandas numpy scikit-learn joblib pyyaml

# 高级模型（可选）
pip install prophet xgboost lightgbm

# 完整安装（推荐）
pip install -r requirements.txt
```

---

## 🎓 最佳实践建议

### 1. 数据准备
- 确保数据质量：处理缺失值、异常值
- 进行特征工程：创建有意义的特征
- 标准化/归一化：根据需要处理特征

### 2. 模型选择
- 从小模型开始：先用线性回归、简单模型
- 逐步尝试复杂模型：RandomForest → GBDT
- 最后使用集成方法

### 3. 性能评估
- 不要只看R²，也要看实际业务指标
- 进行交叉验证，确保稳定性
- 检查残差，理解模型错误

### 4. 可解释性
- 使用简单模型或可解释模型
- 分析特征重要性
- 确保业务方理解

---

## ❓ 常见问题

### Q: 如何添加新的机器学习模型？

A: 在 `backend/ml/models.py` 中继承 `BaseModel` 并实现：

```python
class MyNewModel(BaseModel):
    def __init__(self):
        super().__init__('my_new_model')
    
    def build_model(self, **kwargs):
        return MyMLAlgorithm(**kwargs)
    
    def get_default_params(self):
        return {'param1': 10, 'param2': 0.1}
    
    def get_param_grid(self):
        return {'param1': [5, 10, 20], 'param2': [0.01, 0.1, 1.0]}

# 注册
MODEL_REGISTRY['my_new_model'] = MyNewModel()
```

### Q: 如何处理大规模数据？

A: 
- 使用合适的格式（parquet、feather）
- 分批处理
- 使用更高效的算法（如LightGBM）
- 考虑分布式框架

### Q: 模型保存和加载？

A:
```python
# 保存
model.save("my_model.pkl")

# 加载
from backend import load_model
model = load_model("my_model.pkl")
```

---

## 📞 下一步

1. **运行演示**：`python test_universal_system.py`
2. **查看配置**：`configs/default.yaml`
3. **定制行业**：根据需求创建新配置
4. **加载数据**：导入你的真实数据
5. **运行分析**：开始你的数据科学之旅！

---

## 📜 许可证

MIT License - 自由使用、修改、分发

---

祝数据顺利！🎉
