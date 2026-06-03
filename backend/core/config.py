"""
通用配置系统 - 支持任意行业和地区
使用YAML配置文件，便于扩展和修改
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DimensionConfig:
    """评分维度配置"""

    name: str
    display_name: str
    description: str
    weight: float
    metrics: list[str]
    metric_weights: dict[str, float]
    higher_is_better: dict[str, bool]


@dataclass
class MetricConfig:
    """单个指标配置"""

    name: str
    display_name: str
    unit: str
    description: str
    data_source: str
    benchmark_method: str = "percentile"  # percentile, fixed, dynamic


@dataclass
class IndustryConfig:
    """行业配置"""

    industry_id: str
    industry_name: str
    industry_type: str  # manufacturing, services, tech, retail
    description: str
    dimensions: list[DimensionConfig]
    metrics: dict[str, MetricConfig]
    success_metrics: list[str]  # 衡量项目成功的指标
    data_requirements: list[str]  # 需要的数据字段


@dataclass
class MLConfig:
    """机器学习配置"""

    models: list[str]
    target_metric: str
    feature_columns: list[str]
    time_column: str
    id_column: str
    train_size: float = 0.8
    validation_size: float = 0.2
    hyperparameter_tuning: bool = True
    cross_validation_folds: int = 5


@dataclass
class ProjectConfig:
    """项目配置"""

    project_name: str
    industry: IndustryConfig
    regions: list[str]
    ml_config: MLConfig
    data_config: dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str | None = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent.parent / "configs"
        self.config_dir.mkdir(exist_ok=True, parents=True)
        self._cache: dict[str, ProjectConfig] = {}

    def load_config(self, config_name: str = "default") -> ProjectConfig:
        """加载配置文件"""
        config_path = self.config_dir / f"{config_name}.yaml"

        if not config_path.exists():
            logger.info(f"Config {config_name} not found, creating default...")
            self._create_default_config(config_name)

        with open(config_path, encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)

        return self._dict_to_config(config_dict)

    def save_config(self, config: ProjectConfig, config_name: str):
        """保存配置"""
        config_path = self.config_dir / f"{config_name}.yaml"
        config_dict = self._config_to_dict(config)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)

        self._cache[config_name] = config
        logger.info(f"Config saved to {config_path}")

    def _dict_to_config(self, config_dict: dict) -> ProjectConfig:
        """将字典转换为配置对象"""
        industry_dict = config_dict.get("industry", {})

        dimensions = [DimensionConfig(**dim) for dim in industry_dict.get("dimensions", [])]

        metrics = {name: MetricConfig(**metric) for name, metric in industry_dict.get("metrics", {}).items()}

        industry = IndustryConfig(
            industry_id=industry_dict.get("industry_id", "default"),
            industry_name=industry_dict.get("industry_name", "通用行业"),
            industry_type=industry_dict.get("industry_type", "services"),
            description=industry_dict.get("description", ""),
            dimensions=dimensions,
            metrics=metrics,
            success_metrics=industry_dict.get("success_metrics", []),
            data_requirements=industry_dict.get("data_requirements", []),
        )

        ml_dict = config_dict.get("ml", {})
        ml_config = MLConfig(
            models=ml_dict.get("models", ["xgboost", "random_forest", "linear_regression"]),
            target_metric=ml_dict.get("target_metric", "target"),
            feature_columns=ml_dict.get("feature_columns", []),
            time_column=ml_dict.get("time_column", "year"),
            id_column=ml_dict.get("id_column", "region"),
            train_size=ml_dict.get("train_size", 0.8),
            validation_size=ml_dict.get("validation_size", 0.2),
            hyperparameter_tuning=ml_dict.get("hyperparameter_tuning", True),
            cross_validation_folds=ml_dict.get("cross_validation_folds", 5),
        )

        return ProjectConfig(
            project_name=config_dict.get("project_name", "default_project"),
            industry=industry,
            regions=config_dict.get("regions", []),
            ml_config=ml_config,
            data_config=config_dict.get("data", {}),
        )

    def _config_to_dict(self, config: ProjectConfig) -> dict:
        """将配置对象转换为字典"""
        dimensions_list = []
        for dim in config.industry.dimensions:
            dimensions_list.append(
                {
                    "name": dim.name,
                    "display_name": dim.display_name,
                    "description": dim.description,
                    "weight": dim.weight,
                    "metrics": dim.metrics,
                    "metric_weights": dim.metric_weights,
                    "higher_is_better": dim.higher_is_better,
                }
            )

        metrics_dict = {}
        for name, metric in config.industry.metrics.items():
            metrics_dict[name] = {
                "name": metric.name,
                "display_name": metric.display_name,
                "unit": metric.unit,
                "description": metric.description,
                "data_source": metric.data_source,
                "benchmark_method": metric.benchmark_method,
            }

        return {
            "project_name": config.project_name,
            "regions": config.regions,
            "industry": {
                "industry_id": config.industry.industry_id,
                "industry_name": config.industry.industry_name,
                "industry_type": config.industry.industry_type,
                "description": config.industry.description,
                "dimensions": dimensions_list,
                "metrics": metrics_dict,
                "success_metrics": config.industry.success_metrics,
                "data_requirements": config.industry.data_requirements,
            },
            "ml": {
                "models": config.ml_config.models,
                "target_metric": config.ml_config.target_metric,
                "feature_columns": config.ml_config.feature_columns,
                "time_column": config.ml_config.time_column,
                "id_column": config.ml_config.id_column,
                "train_size": config.ml_config.train_size,
                "validation_size": config.ml_config.validation_size,
                "hyperparameter_tuning": config.ml_config.hyperparameter_tuning,
                "cross_validation_folds": config.ml_config.cross_validation_folds,
            },
            "data": config.data_config,
        }

    def _create_default_config(self, config_name: str):
        """创建默认配置"""
        dimensions = [
            DimensionConfig(
                name="cost",
                display_name="成本维度",
                description="评估运营成本",
                weight=0.40,
                metrics=["land_price", "labor_cost", "energy_cost"],
                metric_weights={"land_price": 0.35, "labor_cost": 0.45, "energy_cost": 0.20},
                higher_is_better={"land_price": False, "labor_cost": False, "energy_cost": False},
            ),
            DimensionConfig(
                name="environment",
                display_name="环境维度",
                description="评估商业环境",
                weight=0.35,
                metrics=["market_size", "talent_pool", "infrastructure"],
                metric_weights={"market_size": 0.40, "talent_pool": 0.35, "infrastructure": 0.25},
                higher_is_better={"market_size": True, "talent_pool": True, "infrastructure": True},
            ),
            DimensionConfig(
                name="policy",
                display_name="政策维度",
                description="评估政策支持",
                weight=0.25,
                metrics=["tax_incentive", "subsidy", "approval_efficiency"],
                metric_weights={"tax_incentive": 0.40, "subsidy": 0.35, "approval_efficiency": 0.25},
                higher_is_better={"tax_incentive": True, "subsidy": True, "approval_efficiency": False},
            ),
        ]

        metrics = {
            "land_price": MetricConfig(
                name="land_price",
                display_name="土地价格",
                unit="元/㎡",
                description="工业用地价格",
                data_source="统计年鉴",
            ),
            "labor_cost": MetricConfig(
                name="labor_cost",
                display_name="劳动力成本",
                unit="元/月",
                description="平均工资水平",
                data_source="统计年鉴",
            ),
            "energy_cost": MetricConfig(
                name="energy_cost",
                display_name="能源成本",
                unit="元/千瓦时",
                description="工业电价",
                data_source="公开数据",
            ),
            "market_size": MetricConfig(
                name="market_size",
                display_name="市场规模",
                unit="亿元",
                description="GDP规模",
                data_source="统计局",
            ),
            "talent_pool": MetricConfig(
                name="talent_pool",
                display_name="人才储备",
                unit="万人",
                description="高等院校在校生",
                data_source="教育局",
            ),
            "infrastructure": MetricConfig(
                name="infrastructure",
                display_name="基础设施",
                unit="分",
                description="基础设施评分",
                data_source="行业报告",
            ),
            "tax_incentive": MetricConfig(
                name="tax_incentive",
                display_name="税收优惠",
                unit="亿元",
                description="税收减免金额",
                data_source="税务局",
            ),
            "subsidy": MetricConfig(
                name="subsidy",
                display_name="补贴金额",
                unit="亿元",
                description="政府补贴金额",
                data_source="财政局",
            ),
            "approval_efficiency": MetricConfig(
                name="approval_efficiency",
                display_name="审批效率",
                unit="天",
                description="平均审批时间",
                data_source="政务服务中心",
            ),
        }

        industry = IndustryConfig(
            industry_id="default",
            industry_name="通用行业",
            industry_type="services",
            description="适用于各类企业的通用分析模板",
            dimensions=dimensions,
            metrics=metrics,
            success_metrics=["market_size", "talent_pool", "tax_incentive"],
            data_requirements=[
                "land_price",
                "labor_cost",
                "energy_cost",
                "market_size",
                "talent_pool",
                "infrastructure",
                "tax_incentive",
                "subsidy",
                "approval_efficiency",
            ],
        )

        ml_config = MLConfig(
            models=["xgboost", "random_forest", "prophet", "linear_regression", "gbdt"],
            target_metric="market_size",
            feature_columns=[
                "land_price",
                "labor_cost",
                "energy_cost",
                "talent_pool",
                "infrastructure",
                "tax_incentive",
                "subsidy",
            ],
            time_column="year",
            id_column="region",
        )

        config = ProjectConfig(
            project_name="default_project",
            industry=industry,
            regions=["北京", "上海", "广州", "深圳"],
            ml_config=ml_config,
        )

        self.save_config(config, config_name)


# 单例
_config_manager: ConfigManager | None = None


def get_config_manager(config_dir: str | None = None) -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir)
    return _config_manager
