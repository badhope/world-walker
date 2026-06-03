"""
灵活的分析场景配置系统
支持多场景配置、自定义配置和快速切换
"""

import json
import logging
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """场景类型"""

    REGIONAL_ANALYSIS = "regional_analysis"  # 区域分析
    INDUSTRY_ANALYSIS = "industry_analysis"  # 产业分析
    ENTERPRISE_ANALYSIS = "enterprise_analysis"  # 企业分析
    GOVERNMENT_ANALYSIS = "government_analysis"  # 政府分析
    CUSTOM = "custom"  # 自定义


@dataclass
class ScenarioConfig:
    """场景配置"""

    id: str  # 场景ID
    name: str  # 场景名称
    description: str  # 场景描述
    scenario_type: ScenarioType  # 场景类型

    # 地区配置
    region: dict[str, Any] | None = None
    industry: dict[str, Any] | None = None

    # 分析配置
    analysis_years: list[int] = field(default_factory=lambda: [2025])
    enabled_dimensions: list[str] = field(default_factory=list)
    custom_indicators: list[str] = field(default_factory=list)

    # 数据源配置
    data_sources: list[str] = field(default_factory=list)

    # 输出配置
    output_format: str = "json"
    output_path: str | None = None

    # 阈值和权重
    thresholds: dict[str, float] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)

    # 额外配置
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scenario_type": self.scenario_type.value,
            "region": self.region,
            "industry": self.industry,
            "analysis_years": self.analysis_years,
            "enabled_dimensions": self.enabled_dimensions,
            "custom_indicators": self.custom_indicators,
            "data_sources": self.data_sources,
            "output_format": self.output_format,
            "output_path": self.output_path,
            "thresholds": self.thresholds,
            "weights": self.weights,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioConfig":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            scenario_type=ScenarioType(data.get("scenario_type", "custom")),
            region=data.get("region"),
            industry=data.get("industry"),
            analysis_years=data.get("analysis_years", [2025]),
            enabled_dimensions=data.get("enabled_dimensions", []),
            custom_indicators=data.get("custom_indicators", []),
            data_sources=data.get("data_sources", []),
            output_format=data.get("output_format", "json"),
            output_path=data.get("output_path"),
            thresholds=data.get("thresholds", {}),
            weights=data.get("weights", {}),
            metadata=data.get("metadata", {}),
        )


class ScenarioManager:
    """场景管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._scenarios: dict[str, ScenarioConfig] = {}
        self._current_scenario: ScenarioConfig | None = None

        self._initialize_default_scenarios()
        self._initialized = True
        logger.info("ScenarioManager 初始化完成")

    def _initialize_default_scenarios(self):
        """初始化默认场景"""
        default_scenarios = [
            # 深圳半导体产业 - 企业视角
            ScenarioConfig(
                id="shenzhen_semiconductor_enterprise",
                name="深圳半导体产业（企业视角）",
                description="从企业角度分析深圳半导体产业的营商环境",
                scenario_type=ScenarioType.ENTERPRISE_ANALYSIS,
                region={"name": "深圳", "code": "440300", "level": "city"},
                industry={"name": "半导体", "code": "C39", "category": "新一代信息技术"},
                analysis_years=[2023, 2024, 2025],
                enabled_dimensions=["business_cost", "supply_chain", "policy_benefits", "market_analysis"],
                thresholds={"cost_high": 100, "policy_coverage_min": 70},
                weights={"land_cost": 0.25, "labor_cost": 0.35, "energy_cost": 0.15, "policy_benefit": 0.25},
            ),
            # 深圳半导体产业 - 政府视角
            ScenarioConfig(
                id="shenzhen_semiconductor_government",
                name="深圳半导体产业（政府视角）",
                description="从政府角度分析半导体产业政策效果",
                scenario_type=ScenarioType.GOVERNMENT_ANALYSIS,
                region={"name": "深圳", "code": "440300", "level": "city"},
                industry={"name": "半导体", "code": "C39", "category": "新一代信息技术"},
                analysis_years=[2023, 2024, 2025],
                enabled_dimensions=["fiscal_leverage", "industry_driving", "policy_effect", "chain_completeness"],
                thresholds={"leverage_ratio_min": 1.5, "deficit_rate_max": 15},
                weights={"fiscal_efficiency": 0.3, "employment_effect": 0.3, "policy_effect": 0.4},
            ),
            # 上海新能源汽车产业
            ScenarioConfig(
                id="shanghai_new_energy",
                name="上海新能源汽车产业分析",
                description="分析上海新能源汽车产业发展状况",
                scenario_type=ScenarioType.INDUSTRY_ANALYSIS,
                region={"name": "上海", "code": "310000", "level": "city"},
                industry={"name": "新能源汽车", "code": "C36", "category": "高端装备制造"},
                analysis_years=[2024, 2025],
                enabled_dimensions=["market_analysis", "technology_analysis", "supply_chain"],
            ),
            # 广东省产业转移分析
            ScenarioConfig(
                id="guangdong_industry_transfer",
                name="广东省产业转移分析",
                description="分析珠三角向粤东西北产业转移情况",
                scenario_type=ScenarioType.REGIONAL_ANALYSIS,
                region={"name": "广东省", "code": "440000", "level": "province"},
                analysis_years=[2022, 2023, 2024, 2025],
                enabled_dimensions=["regional_comparison", "industry_transfer", "investment_analysis"],
            ),
        ]

        for scenario in default_scenarios:
            self.register_scenario(scenario)

    def register_scenario(self, scenario: ScenarioConfig) -> bool:
        """注册场景"""
        self._scenarios[scenario.id] = scenario
        logger.info(f"注册场景: {scenario.id} - {scenario.name}")
        return True

    def unregister_scenario(self, scenario_id: str) -> bool:
        """注销场景"""
        if scenario_id in self._scenarios:
            del self._scenarios[scenario_id]
            if self._current_scenario and self._current_scenario.id == scenario_id:
                self._current_scenario = None
            return True
        return False

    def get_scenario(self, scenario_id: str) -> ScenarioConfig | None:
        """获取场景配置"""
        return self._scenarios.get(scenario_id)

    def list_scenarios(self, scenario_type: ScenarioType | None = None) -> list[ScenarioConfig]:
        """列出场景"""
        if scenario_type:
            return [s for s in self._scenarios.values() if s.scenario_type == scenario_type]
        return list(self._scenarios.values())

    def set_current_scenario(self, scenario_id: str) -> bool:
        """设置当前场景"""
        scenario = self._scenarios.get(scenario_id)
        if scenario:
            self._current_scenario = scenario
            logger.info(f"切换到场景: {scenario.name}")
            return True
        return False

    def get_current_scenario(self) -> ScenarioConfig | None:
        """获取当前场景"""
        return self._current_scenario

    def create_scenario(self, name: str, scenario_type: str = "custom", **kwargs) -> ScenarioConfig:
        """快速创建场景"""
        import uuid

        scenario_id = f"custom_{uuid.uuid4().hex[:8]}"

        scenario = ScenarioConfig(
            id=scenario_id,
            name=name,
            description=kwargs.get("description", ""),
            scenario_type=ScenarioType(scenario_type),
            region=kwargs.get("region"),
            industry=kwargs.get("industry"),
            analysis_years=kwargs.get("years", [2025]),
            enabled_dimensions=kwargs.get("dimensions", []),
            custom_indicators=kwargs.get("indicators", []),
            thresholds=kwargs.get("thresholds", {}),
            weights=kwargs.get("weights", {}),
        )

        self.register_scenario(scenario)
        return scenario

    def clone_scenario(self, source_id: str, new_name: str, **overrides) -> ScenarioConfig | None:
        """克隆场景"""
        source = self._scenarios.get(source_id)
        if not source:
            return None

        import uuid

        new_id = f"clone_{uuid.uuid4().hex[:8]}"

        cloned = deepcopy(source)
        cloned.id = new_id
        cloned.name = new_name
        cloned.metadata["cloned_from"] = source_id

        # 应用覆盖
        for key, value in overrides.items():
            if hasattr(cloned, key):
                setattr(cloned, key, value)

        self.register_scenario(cloned)
        return cloned

    def save_scenarios(self, filepath: str):
        """保存场景到文件"""
        data = {"scenarios": [s.to_dict() for s in self._scenarios.values()]}

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"场景配置已保存到 {filepath}")

    def load_scenarios(self, filepath: str):
        """从文件加载场景"""
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            loaded = 0
            for scenario_data in data.get("scenarios", []):
                scenario = ScenarioConfig.from_dict(scenario_data)
                self.register_scenario(scenario)
                loaded += 1

            logger.info(f"从 {filepath} 加载了 {loaded} 个场景")
        except Exception as e:
            logger.error(f"加载场景失败: {e}")

    def export_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        """导出单个场景"""
        scenario = self._scenarios.get(scenario_id)
        if scenario:
            return scenario.to_dict()
        return None

    def get_status(self) -> dict[str, Any]:
        """获取状态"""
        type_counts = {}
        for scenario in self._scenarios.values():
            t = scenario.scenario_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_scenarios": len(self._scenarios),
            "by_type": type_counts,
            "current_scenario": self._current_scenario.id if self._current_scenario else None,
        }


# 全局单例
scenario_manager = ScenarioManager()


# 便捷函数
def register_scenario(name: str, scenario_type: str = "custom", **kwargs) -> ScenarioConfig:
    """注册场景"""
    return scenario_manager.create_scenario(name, scenario_type, **kwargs)


def get_scenario(scenario_id: str) -> ScenarioConfig | None:
    """获取场景"""
    return scenario_manager.get_scenario(scenario_id)


def list_scenarios(scenario_type: str = None) -> list[ScenarioConfig]:
    """列出场景"""
    st = ScenarioType(scenario_type) if scenario_type else None
    return scenario_manager.list_scenarios(st)


def use_scenario(scenario_id: str) -> bool:
    """使用场景"""
    return scenario_manager.set_current_scenario(scenario_id)


def clone_scenario(source_id: str, new_name: str, **overrides) -> ScenarioConfig | None:
    """克隆场景"""
    return scenario_manager.clone_scenario(source_id, new_name, **overrides)
