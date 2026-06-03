"""
零售行业分析配置示例
展示如何将通用框架应用于零售行业
"""

industry_config = {
    "industry_id": "retail",
    "industry_name": "零售行业",
    "industry_type": "retail",
    "description": "零售行业选址与经营分析模板",
    "dimensions": [
        {
            "name": "location",
            "display_name": "选址维度",
            "description": "评估店铺位置优势",
            "weight": 0.35,
            "metrics": ["foot_traffic", "rental_cost", "competition_density", "accessibility"],
            "metric_weights": {
                "foot_traffic": 0.35,
                "rental_cost": 0.25,
                "competition_density": 0.20,
                "accessibility": 0.20,
            },
            "higher_is_better": {
                "foot_traffic": True,
                "rental_cost": False,
                "competition_density": False,
                "accessibility": True,
            },
        },
        {
            "name": "market",
            "display_name": "市场维度",
            "description": "评估市场潜力",
            "weight": 0.35,
            "metrics": ["population", "income_level", "age_distribution", "spending_habit"],
            "metric_weights": {
                "population": 0.30,
                "income_level": 0.35,
                "age_distribution": 0.15,
                "spending_habit": 0.20,
            },
            "higher_is_better": {
                "population": True,
                "income_level": True,
                "age_distribution": True,
                "spending_habit": True,
            },
        },
        {
            "name": "operation",
            "display_name": "运营维度",
            "description": "评估运营成本与效率",
            "weight": 0.30,
            "metrics": ["labor_cost", "utilities_cost", "logistics_cost", "inventory_turnover"],
            "metric_weights": {
                "labor_cost": 0.25,
                "utilities_cost": 0.20,
                "logistics_cost": 0.25,
                "inventory_turnover": 0.30,
            },
            "higher_is_better": {
                "labor_cost": False,
                "utilities_cost": False,
                "logistics_cost": False,
                "inventory_turnover": True,
            },
        },
    ],
    "metrics": {
        "foot_traffic": {
            "name": "foot_traffic",
            "display_name": "客流量",
            "unit": "人次/天",
            "description": "日均客流量",
            "data_source": "实地调查",
            "benchmark_method": "percentile",
        },
        "rental_cost": {
            "name": "rental_cost",
            "display_name": "租金成本",
            "unit": "元/㎡/天",
            "description": "店铺日均租金",
            "data_source": "地产中介",
            "benchmark_method": "percentile",
        },
        "competition_density": {
            "name": "competition_density",
            "display_name": "竞争密度",
            "unit": "家/公里²",
            "description": "周边竞争对手数量",
            "data_source": "市场调研",
            "benchmark_method": "percentile",
        },
        "accessibility": {
            "name": "accessibility",
            "display_name": "交通便利度",
            "unit": "分",
            "description": "交通可达性评分",
            "data_source": "综合评估",
            "benchmark_method": "percentile",
        },
        "population": {
            "name": "population",
            "display_name": "人口规模",
            "unit": "万人",
            "description": "服务半径内人口",
            "data_source": "统计局",
            "benchmark_method": "percentile",
        },
        "income_level": {
            "name": "income_level",
            "display_name": "收入水平",
            "unit": "元/月",
            "description": "人均可支配收入",
            "data_source": "统计局",
            "benchmark_method": "percentile",
        },
        "age_distribution": {
            "name": "age_distribution",
            "display_name": "年龄分布",
            "unit": "%",
            "description": "目标年龄段占比",
            "data_source": "统计局",
            "benchmark_method": "percentile",
        },
        "spending_habit": {
            "name": "spending_habit",
            "display_name": "消费习惯",
            "unit": "分",
            "description": "零售消费偏好评分",
            "data_source": "消费调研",
            "benchmark_method": "percentile",
        },
        "labor_cost": {
            "name": "labor_cost",
            "display_name": "人力成本",
            "unit": "元/月/人",
            "description": "员工平均月工资",
            "data_source": "HR数据",
            "benchmark_method": "percentile",
        },
        "utilities_cost": {
            "name": "utilities_cost",
            "display_name": "水电成本",
            "unit": "元/月",
            "description": "月均水电费",
            "data_source": "账单数据",
            "benchmark_method": "percentile",
        },
        "logistics_cost": {
            "name": "logistics_cost",
            "display_name": "物流成本",
            "unit": "元/单",
            "description": "单均物流配送成本",
            "data_source": "物流系统",
            "benchmark_method": "percentile",
        },
        "inventory_turnover": {
            "name": "inventory_turnover",
            "display_name": "库存周转率",
            "unit": "次/年",
            "description": "年库存周转次数",
            "data_source": "ERP系统",
            "benchmark_method": "percentile",
        },
    },
    "success_metrics": ["foot_traffic", "income_level", "inventory_turnover"],
    "data_requirements": [
        "foot_traffic",
        "rental_cost",
        "competition_density",
        "accessibility",
        "population",
        "income_level",
        "age_distribution",
        "spending_habit",
        "labor_cost",
        "utilities_cost",
        "logistics_cost",
        "inventory_turnover",
    ],
}

ml_config = {
    "models": ["xgboost", "random_forest", "gbdt", "prophet", "linear_regression"],
    "target_metric": "inventory_turnover",
    "feature_columns": [
        "foot_traffic",
        "rental_cost",
        "competition_density",
        "accessibility",
        "population",
        "income_level",
        "age_distribution",
        "spending_habit",
        "labor_cost",
        "utilities_cost",
        "logistics_cost",
    ],
    "time_column": "year",
    "id_column": "store_id",
    "train_size": 0.8,
    "validation_size": 0.2,
    "hyperparameter_tuning": True,
    "cross_validation_folds": 5,
}


def create_retail_sample_data(n_stores=20, n_years=5, seed=42):
    """创建零售行业示例数据"""
    import numpy as np
    import pandas as pd

    np.random.seed(seed)

    stores = [f"Store_{i:03d}" for i in range(n_stores)]
    years = list(range(2020, 2020 + n_years))

    data = []
    for store in stores:
        base_quality = np.random.uniform(0.6, 1.0)

        for year in years:
            base = stores.index(store) * 5

            record = {
                "store_id": store,
                "store_name": f"{store} - Location {stores.index(store)}",
                "year": year,
                "source": "sample",
                "foot_traffic": int(500 + base * 10 + base_quality * 200 + np.random.normal(0, 50)),
                "rental_cost": 5 + base * 0.2 + np.random.normal(0, 0.5),
                "competition_density": 10 - base * 0.5 + np.random.normal(0, 2),
                "accessibility": 70 + base * 0.3 + np.random.normal(0, 5),
                "population": 50 + base * 2 + np.random.normal(0, 5),
                "income_level": 8000 + base * 100 + base_quality * 500 + np.random.normal(0, 200),
                "age_distribution": 30 + base * 0.5 + np.random.normal(0, 5),
                "spending_habit": 60 + base * 0.8 + np.random.normal(0, 5),
                "labor_cost": 4000 + base * 50 + np.random.normal(0, 200),
                "utilities_cost": 5000 + base * 20 + np.random.normal(0, 300),
                "logistics_cost": 15 + base * 0.3 + np.random.normal(0, 2),
                "inventory_turnover": 8 + base_quality * 4 + (year - 2020) * 0.5 + np.random.normal(0, 1),
            }

            record["foot_traffic"] = max(0, record["foot_traffic"])
            record["competition_density"] = max(0, record["competition_density"])
            record["inventory_turnover"] = max(0, record["inventory_turnover"])

            data.append(record)

    return pd.DataFrame(data)


if __name__ == "__main__":
    from pathlib import Path

    import yaml

    workspace_root = Path(__file__).parent.parent
    config_dir = workspace_root / "configs"
    config_dir.mkdir(exist_ok=True, parents=True)

    config = {
        "project_name": "retail_store_analysis",
        "regions": ["Shanghai", "Beijing", "Guangzhou", "Shenzhen"],
        "industry": industry_config,
        "ml": ml_config,
        "data": {},
    }

    with open(config_dir / "retail.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    print(f"✓ 零售行业配置已保存到 {config_dir / 'retail.yaml'}")

    sample_df = create_retail_sample_data()
    data_dir = workspace_root / "data"
    data_dir.mkdir(exist_ok=True, parents=True)
    sample_df.to_csv(data_dir / "retail_sample.csv", index=False)
    print(f"✓ 零售行业示例数据已保存到 {data_dir / 'retail_sample.csv'}")
    print("\n数据预览:")
    print(sample_df.head())
