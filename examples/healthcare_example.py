"""
医疗健康行业分析配置示例
展示如何将通用框架应用于医疗健康行业
"""

industry_config = {
    "industry_id": "healthcare",
    "industry_name": "医疗健康行业",
    "industry_type": "healthcare",
    "description": "医疗机构选址与服务能力评估模板",
    "dimensions": [
        {
            "name": "demand",
            "display_name": "需求维度",
            "description": "评估医疗需求市场规模",
            "weight": 0.40,
            "metrics": ["population", "elderly_ratio", "disease_prevalence", "insurance_coverage"],
            "metric_weights": {
                "population": 0.35,
                "elderly_ratio": 0.30,
                "disease_prevalence": 0.20,
                "insurance_coverage": 0.15,
            },
            "higher_is_better": {
                "population": True,
                "elderly_ratio": True,
                "disease_prevalence": True,
                "insurance_coverage": True,
            },
        },
        {
            "name": "competition",
            "display_name": "竞争维度",
            "description": "评估市场竞争态势",
            "weight": 0.30,
            "metrics": ["hospital_density", "bed_utilization", "specialist_availability", "wait_time"],
            "metric_weights": {
                "hospital_density": 0.30,
                "bed_utilization": 0.25,
                "specialist_availability": 0.25,
                "wait_time": 0.20,
            },
            "higher_is_better": {
                "hospital_density": False,
                "bed_utilization": True,
                "specialist_availability": True,
                "wait_time": False,
            },
        },
        {
            "name": "resource",
            "display_name": "资源维度",
            "description": "评估医疗资源配置",
            "weight": 0.30,
            "metrics": ["medical_staff_ratio", "equipment_level", "cost_efficiency", "revenue_per_patient"],
            "metric_weights": {
                "medical_staff_ratio": 0.30,
                "equipment_level": 0.25,
                "cost_efficiency": 0.25,
                "revenue_per_patient": 0.20,
            },
            "higher_is_better": {
                "medical_staff_ratio": True,
                "equipment_level": True,
                "cost_efficiency": True,
                "revenue_per_patient": True,
            },
        },
    ],
    "metrics": {
        "population": {
            "name": "population",
            "display_name": "服务人口",
            "unit": "万人",
            "description": "服务半径内常住人口",
            "data_source": "统计局",
            "benchmark_method": "percentile",
        },
        "elderly_ratio": {
            "name": "elderly_ratio",
            "display_name": "老龄化比例",
            "unit": "%",
            "description": "65岁以上人口占比",
            "data_source": "统计局",
            "benchmark_method": "percentile",
        },
        "disease_prevalence": {
            "name": "disease_prevalence",
            "display_name": "疾病发病率",
            "unit": "%",
            "description": "慢性病发病率",
            "data_source": "卫健委",
            "benchmark_method": "percentile",
        },
        "insurance_coverage": {
            "name": "insurance_coverage",
            "display_name": "医保覆盖率",
            "unit": "%",
            "description": "基本医保参保率",
            "data_source": "医保局",
            "benchmark_method": "percentile",
        },
        "hospital_density": {
            "name": "hospital_density",
            "display_name": "医院密度",
            "unit": "家/10万人",
            "description": "每10万人拥有医院数量",
            "data_source": "卫健委",
            "benchmark_method": "percentile",
        },
        "bed_utilization": {
            "name": "bed_utilization",
            "display_name": "床位使用率",
            "unit": "%",
            "description": "病床实际使用率",
            "data_source": "医院数据",
            "benchmark_method": "percentile",
        },
        "specialist_availability": {
            "name": "specialist_availability",
            "display_name": "专科医生可及性",
            "unit": "人/万人",
            "description": "每万人拥有的专科医生数",
            "data_source": "卫健委",
            "benchmark_method": "percentile",
        },
        "wait_time": {
            "name": "wait_time",
            "display_name": "平均等待时间",
            "unit": "分钟",
            "description": "门诊平均等待时间",
            "data_source": "医院数据",
            "benchmark_method": "percentile",
        },
        "medical_staff_ratio": {
            "name": "medical_staff_ratio",
            "display_name": "医护比",
            "unit": "%",
            "description": "执业医师/护士比例",
            "data_source": "医院数据",
            "benchmark_method": "percentile",
        },
        "equipment_level": {
            "name": "equipment_level",
            "display_name": "设备水平",
            "unit": "分",
            "description": "医疗设备配置评分",
            "data_source": "综合评估",
            "benchmark_method": "percentile",
        },
        "cost_efficiency": {
            "name": "cost_efficiency",
            "display_name": "成本效率",
            "unit": "%",
            "description": "医疗成本控制率",
            "data_source": "医院数据",
            "benchmark_method": "percentile",
        },
        "revenue_per_patient": {
            "name": "revenue_per_patient",
            "display_name": "人均收入",
            "unit": "元/人次",
            "description": "每患者平均收入",
            "data_source": "医院数据",
            "benchmark_method": "percentile",
        },
    },
    "success_metrics": ["population", "bed_utilization", "revenue_per_patient"],
    "data_requirements": [
        "population",
        "elderly_ratio",
        "disease_prevalence",
        "insurance_coverage",
        "hospital_density",
        "bed_utilization",
        "specialist_availability",
        "wait_time",
        "medical_staff_ratio",
        "equipment_level",
        "cost_efficiency",
        "revenue_per_patient",
    ],
}

ml_config = {
    "models": ["xgboost", "random_forest", "gbdt", "prophet", "linear_regression"],
    "target_metric": "revenue_per_patient",
    "feature_columns": [
        "population",
        "elderly_ratio",
        "disease_prevalence",
        "insurance_coverage",
        "hospital_density",
        "specialist_availability",
        "medical_staff_ratio",
        "equipment_level",
        "cost_efficiency",
    ],
    "time_column": "year",
    "id_column": "hospital_id",
    "train_size": 0.8,
    "validation_size": 0.2,
    "hyperparameter_tuning": True,
    "cross_validation_folds": 5,
}


def create_healthcare_sample_data(n_hospitals=15, n_years=5, seed=42):
    """创建医疗健康行业示例数据"""
    import numpy as np
    import pandas as pd

    np.random.seed(seed)

    hospitals = [f"Hospital_{i:03d}" for i in range(n_hospitals)]
    years = list(range(2020, 2020 + n_years))

    data = []
    for hospital in hospitals:
        base_quality = np.random.uniform(0.5, 1.0)

        for year in years:
            base = hospitals.index(hospital) * 3

            record = {
                "hospital_id": hospital,
                "hospital_name": f"{hospital} - Grade {hospitals.index(hospital) % 3 + 1}",
                "year": year,
                "source": "sample",
                "population": 100 + base * 5 + np.random.normal(0, 10),
                "elderly_ratio": 12 + base * 0.3 + np.random.normal(0, 1),
                "disease_prevalence": 25 + base * 0.5 + np.random.normal(0, 2),
                "insurance_coverage": 85 + base * 0.2 + np.random.normal(0, 3),
                "hospital_density": 3 - base * 0.05 + np.random.normal(0, 0.3),
                "bed_utilization": 70 + base * 1.5 + base_quality * 10 + np.random.normal(0, 5),
                "specialist_availability": 15 + base * 0.8 + base_quality * 5 + np.random.normal(0, 2),
                "wait_time": 45 - base * 0.5 + np.random.normal(0, 5),
                "medical_staff_ratio": 60 + base * 0.8 + base_quality * 10 + np.random.normal(0, 3),
                "equipment_level": 70 + base * 1.2 + base_quality * 15 + np.random.normal(0, 5),
                "cost_efficiency": 75 + base * 0.5 + np.random.normal(0, 5),
                "revenue_per_patient": 200
                + base * 5
                + base_quality * 50
                + (year - 2020) * 10
                + np.random.normal(0, 15),
            }

            record["hospital_density"] = max(0.5, record["hospital_density"])
            record["wait_time"] = max(5, record["wait_time"])
            record["bed_utilization"] = min(100, max(30, record["bed_utilization"]))
            record["medical_staff_ratio"] = min(100, max(20, record["medical_staff_ratio"]))

            data.append(record)

    return pd.DataFrame(data)


if __name__ == "__main__":
    from pathlib import Path

    import yaml

    workspace_root = Path(__file__).parent.parent
    config_dir = workspace_root / "configs"
    config_dir.mkdir(exist_ok=True, parents=True)

    config = {
        "project_name": "healthcare_facility_analysis",
        "regions": ["Shanghai", "Beijing", "Guangzhou", "Shenzhen", "Chengdu"],
        "industry": industry_config,
        "ml": ml_config,
        "data": {},
    }

    with open(config_dir / "healthcare.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    print(f"✓ 医疗健康行业配置已保存到 {config_dir / 'healthcare.yaml'}")

    sample_df = create_healthcare_sample_data()
    data_dir = workspace_root / "data"
    data_dir.mkdir(exist_ok=True, parents=True)
    sample_df.to_csv(data_dir / "healthcare_sample.csv", index=False)
    print(f"✓ 医疗健康行业示例数据已保存到 {data_dir / 'healthcare_sample.csv'}")
    print("\n数据预览:")
    print(sample_df.head())
