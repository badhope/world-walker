"""
灵活的指标注册和管理系统
允许动态注册、查询和管理各种分析指标
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IndicatorCategory(Enum):
    """指标分类"""

    MACRO = "macro"  # 宏观经济
    INDUSTRY = "industry"  # 产业分析
    BUSINESS = "business"  # 营商环境
    FISCAL = "fiscal"  # 财政金融
    EMPLOYMENT = "employment"  # 就业人才
    TRADE = "trade"  # 国际贸易
    INNOVATION = "innovation"  # 科技创新
    SOCIAL = "social"  # 社会民生
    ENVIRONMENT = "environment"  # 生态环境
    CUSTOM = "custom"  # 自定义指标


@dataclass
class IndicatorDefinition:
    """指标定义"""

    code: str  # 指标代码
    name: str  # 指标名称
    category: IndicatorCategory  # 指标分类
    unit: str  # 单位
    description: str  # 描述
    formula: str | None = None  # 计算公式（如有）
    required_data: list[str] = field(default_factory=list)  # 所需数据字段
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他指标
    calculation_func: Callable | None = None  # 自定义计算函数
    threshold_high: float | None = None  # 高阈值
    threshold_low: float | None = None  # 低阈值
    tags: list[str] = field(default_factory=list)  # 标签
    metadata: dict[str, Any] = field(default_factory=dict)  # 额外元数据

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "category": self.category.value,
            "unit": self.unit,
            "description": self.description,
            "formula": self.formula,
            "required_data": self.required_data,
            "dependencies": self.dependencies,
            "threshold_high": self.threshold_high,
            "threshold_low": self.threshold_low,
            "tags": self.tags,
        }


class IndicatorRegistry:
    """指标注册中心"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._indicators: dict[str, IndicatorDefinition] = {}
        self._categories: dict[IndicatorCategory, list[str]] = {cat: [] for cat in IndicatorCategory}
        self._tags_index: dict[str, list[str]] = {}  # tag -> list of indicator codes

        self._initialize_default_indicators()
        self._initialized = True
        logger.info(f"IndicatorRegistry 初始化完成，共注册 {len(self._indicators)} 个指标")

    def _initialize_default_indicators(self):
        """初始化默认指标"""
        # 宏观经济类指标
        default_indicators = [
            # 宏观经济
            IndicatorDefinition(
                code="gdp",
                name="地区生产总值",
                category=IndicatorCategory.MACRO,
                unit="亿元",
                description="地区生产总值，反映经济总量",
            ),
            IndicatorDefinition(
                code="gdp_growth",
                name="GDP增速",
                category=IndicatorCategory.MACRO,
                unit="%",
                description="GDP同比增长率",
                threshold_high=15.0,
                threshold_low=0.0,
            ),
            IndicatorDefinition(
                code="gdp_per_capita",
                name="人均GDP",
                category=IndicatorCategory.MACRO,
                unit="元/人",
                description="人均地区生产总值",
            ),
            IndicatorDefinition(
                code="cpi",
                name="居民消费价格指数",
                category=IndicatorCategory.MACRO,
                unit="上年=100",
                description="CPI反映通货膨胀水平",
            ),
            IndicatorDefinition(
                code="ppi",
                name="工业生产者出厂价格指数",
                category=IndicatorCategory.MACRO,
                unit="上年=100",
                description="PPI反映工业品价格变动",
            ),
            IndicatorDefinition(
                code="pmi",
                name="采购经理指数",
                category=IndicatorCategory.MACRO,
                unit="",
                description="PMI反映经济景气程度，50为荣枯线",
                threshold_high=60.0,
                threshold_low=45.0,
            ),
            # 产业分析类
            IndicatorDefinition(
                code="industrial_output",
                name="工业总产值",
                category=IndicatorCategory.INDUSTRY,
                unit="亿元",
                description="规模以上工业总产值",
            ),
            IndicatorDefinition(
                code="industry_concentration",
                name="产业集中度",
                category=IndicatorCategory.INDUSTRY,
                unit="%",
                description="前几大企业占行业总产值比重",
                threshold_high=80.0,
            ),
            IndicatorDefinition(
                code="capacity_utilization",
                name="产能利用率",
                category=IndicatorCategory.INDUSTRY,
                unit="%",
                description="实际产量/设计产能",
                threshold_high=100.0,
                threshold_low=60.0,
            ),
            IndicatorDefinition(
                code="output_value",
                name="产业产值",
                category=IndicatorCategory.INDUSTRY,
                unit="亿元",
                description="特定产业总产值",
            ),
            IndicatorDefinition(
                code="market_share",
                name="市场份额",
                category=IndicatorCategory.INDUSTRY,
                unit="%",
                description="在目标市场的占比",
            ),
            IndicatorDefinition(
                code="export_ratio",
                name="出口依存度",
                category=IndicatorCategory.TRADE,
                unit="%",
                description="出口额/GDP，反映经济对外依赖程度",
                threshold_high=50.0,
            ),
            # 营商环境类
            IndicatorDefinition(
                code="land_price",
                name="工业用地价格",
                category=IndicatorCategory.BUSINESS,
                unit="元/㎡·年",
                description="工业用地年租金",
            ),
            IndicatorDefinition(
                code="labor_cost",
                name="人力成本",
                category=IndicatorCategory.BUSINESS,
                unit="元/月·人",
                description="平均人力成本",
            ),
            IndicatorDefinition(
                code="electricity_price",
                name="工业用电价格",
                category=IndicatorCategory.BUSINESS,
                unit="元/kWh",
                description="大工业用电价格",
            ),
            IndicatorDefinition(
                code="comprehensive_cost_index",
                name="综合营商成本指数",
                category=IndicatorCategory.BUSINESS,
                unit="",
                description="综合土地、人力、能源等成本的指数",
                threshold_high=120.0,
                threshold_low=50.0,
            ),
            # 财政金融类
            IndicatorDefinition(
                code="fiscal_revenue",
                name="财政收入",
                category=IndicatorCategory.FISCAL,
                unit="亿元",
                description="一般公共预算收入",
            ),
            IndicatorDefinition(
                code="fiscal_expenditure",
                name="财政支出",
                category=IndicatorCategory.FISCAL,
                unit="亿元",
                description="一般公共预算支出",
            ),
            IndicatorDefinition(
                code="deficit_rate",
                name="赤字率",
                category=IndicatorCategory.FISCAL,
                unit="%",
                description="财政赤字/GDP",
                threshold_high=15.0,
                threshold_low=0.0,
            ),
            IndicatorDefinition(
                code="fiscal_self_sufficiency",
                name="财政自给率",
                category=IndicatorCategory.FISCAL,
                unit="%",
                description="财政收入/财政支出",
                threshold_high=100.0,
                threshold_low=50.0,
            ),
            IndicatorDefinition(
                code="leverage_ratio",
                name="杠杆倍数",
                category=IndicatorCategory.FISCAL,
                unit="倍",
                description="财政投入撬动社会资本的倍数",
                threshold_low=1.0,
            ),
            IndicatorDefinition(
                code="loan_rate",
                name="贷款利率",
                category=IndicatorCategory.FISCAL,
                unit="%",
                description="企业实际贷款利率",
                threshold_high=8.0,
                threshold_low=2.0,
            ),
            # 就业人才类
            IndicatorDefinition(
                code="employment_rate",
                name="就业率",
                category=IndicatorCategory.EMPLOYMENT,
                unit="%",
                description="城镇就业人员/劳动年龄人口",
                threshold_low=90.0,
            ),
            IndicatorDefinition(
                code="unemployment_rate",
                name="失业率",
                category=IndicatorCategory.EMPLOYMENT,
                unit="%",
                description="城镇登记失业率",
                threshold_high=5.0,
            ),
            IndicatorDefinition(
                code="avg_salary",
                name="平均工资",
                category=IndicatorCategory.EMPLOYMENT,
                unit="元/月",
                description="城镇单位就业人员平均工资",
            ),
            IndicatorDefinition(
                code="turnover_rate",
                name="员工离职率",
                category=IndicatorCategory.EMPLOYMENT,
                unit="%",
                description="年度离职员工/平均员工数",
                threshold_high=20.0,
            ),
            IndicatorDefinition(
                code="rd_personnel",
                name="研发人员数量",
                category=IndicatorCategory.EMPLOYMENT,
                unit="人",
                description="R&D研究人员数量",
            ),
            # 科技创新类
            IndicatorDefinition(
                code="rd_intensity",
                name="研发投入强度",
                category=IndicatorCategory.INNOVATION,
                unit="%",
                description="研发支出/GDP",
                threshold_low=2.5,
            ),
            IndicatorDefinition(
                code="patent_count",
                name="专利授权量",
                category=IndicatorCategory.INNOVATION,
                unit="件",
                description="年度发明专利授权量",
            ),
            IndicatorDefinition(
                code="tech_breakthrough_count",
                name="关键技术突破数",
                category=IndicatorCategory.INNOVATION,
                unit="项",
                description="解决卡脖子问题的技术突破数",
            ),
            IndicatorDefinition(
                code="localization_rate",
                name="国产化率",
                category=IndicatorCategory.INNOVATION,
                unit="%",
                description="关键零部件/原材料国产化程度",
                threshold_low=50.0,
            ),
            # 供应链类
            IndicatorDefinition(
                code="supply_chain_coverage",
                name="供应链覆盖度",
                category=IndicatorCategory.INDUSTRY,
                unit="%",
                description="产业链各环节本地配套率",
                threshold_low=60.0,
            ),
            IndicatorDefinition(
                code="location_quotient",
                name="区位熵",
                category=IndicatorCategory.INDUSTRY,
                unit="",
                description="产业集聚程度指标，大于1表示集聚",
                threshold_low=1.0,
            ),
            IndicatorDefinition(
                code="delivery_cycle",
                name="平均交付周期",
                category=IndicatorCategory.BUSINESS,
                unit="天",
                description="从订单到交付的平均天数",
                threshold_high=45.0,
            ),
            IndicatorDefinition(
                code="on_time_delivery_rate",
                name="准时交货率",
                category=IndicatorCategory.BUSINESS,
                unit="%",
                description="按时交货订单/总订单",
                threshold_low=90.0,
            ),
            # 政策效果类
            IndicatorDefinition(
                code="tax_incentive",
                name="税收优惠总额",
                category=IndicatorCategory.FISCAL,
                unit="亿元",
                description="企业享受的各类税收优惠",
            ),
            IndicatorDefinition(
                code="subsidy_amount",
                name="补贴金额",
                category=IndicatorCategory.FISCAL,
                unit="亿元",
                description="政府发放的各类补贴",
            ),
            IndicatorDefinition(
                code="policy_coverage",
                name="政策覆盖率",
                category=IndicatorCategory.BUSINESS,
                unit="%",
                description="符合条件企业中实际受惠比例",
                threshold_low=70.0,
            ),
            IndicatorDefinition(
                code="satisfaction_rate",
                name="企业满意度",
                category=IndicatorCategory.BUSINESS,
                unit="%",
                description="企业对政策的主观评价",
                threshold_low=80.0,
            ),
        ]

        # 注册所有默认指标
        for indicator in default_indicators:
            self.register(indicator)

    def register(self, indicator: IndicatorDefinition) -> bool:
        """
        注册指标

        Args:
            indicator: 指标定义

        Returns:
            是否注册成功
        """
        if indicator.code in self._indicators:
            logger.warning(f"指标 {indicator.code} 已存在，将被覆盖")

        self._indicators[indicator.code] = indicator

        # 更新分类索引
        if indicator.category not in self._categories:
            self._categories[indicator.category] = []
        if indicator.code not in self._categories[indicator.category]:
            self._categories[indicator.category].append(indicator.code)

        # 更新标签索引
        for tag in indicator.tags:
            if tag not in self._tags_index:
                self._tags_index[tag] = []
            if indicator.code not in self._tags_index[tag]:
                self._tags_index[tag].append(indicator.code)

        logger.debug(f"注册指标: {indicator.code} - {indicator.name}")
        return True

    def unregister(self, code: str) -> bool:
        """注销指标"""
        if code not in self._indicators:
            logger.warning(f"指标 {code} 不存在")
            return False

        indicator = self._indicators.pop(code)

        # 从分类中移除
        if code in self._categories[indicator.category]:
            self._categories[indicator.category].remove(code)

        # 从标签索引中移除
        for tag in indicator.tags:
            if tag in self._tags_index and code in self._tags_index[tag]:
                self._tags_index[tag].remove(code)

        return True

    def get(self, code: str) -> IndicatorDefinition | None:
        """获取指标定义"""
        return self._indicators.get(code)

    def get_by_category(self, category: IndicatorCategory) -> list[IndicatorDefinition]:
        """获取某分类下的所有指标"""
        codes = self._categories.get(category, [])
        return [self._indicators[code] for code in codes if code in self._indicators]

    def get_by_tags(self, tags: list[str]) -> list[IndicatorDefinition]:
        """获取包含指定标签的指标"""
        result_codes = set()
        for tag in tags:
            if tag in self._tags_index:
                result_codes.update(self._tags_index[tag])

        return [self._indicators[code] for code in result_codes if code in self._indicators]

    def search(self, keyword: str) -> list[IndicatorDefinition]:
        """搜索指标（按名称或描述）"""
        keyword = keyword.lower()
        results = []

        for indicator in self._indicators.values():
            if (
                keyword in indicator.name.lower()
                or keyword in indicator.description.lower()
                or keyword in indicator.code.lower()
            ):
                results.append(indicator)

        return results

    def get_all(self) -> list[IndicatorDefinition]:
        """获取所有指标"""
        return list(self._indicators.values())

    def get_categories(self) -> list[IndicatorCategory]:
        """获取所有分类"""
        return list(IndicatorCategory)

    def get_all_codes(self) -> list[str]:
        """获取所有指标代码"""
        return list(self._indicators.keys())

    def export_to_dict(self) -> dict[str, Any]:
        """导出为字典"""
        return {
            "total_count": len(self._indicators),
            "categories": {cat.value: len(codes) for cat, codes in self._categories.items()},
            "indicators": {code: ind.to_dict() for code, ind in self._indicators.items()},
        }

    def save_to_file(self, filepath: str):
        """保存到文件"""
        data = self.export_to_dict()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"指标定义已保存到 {filepath}")

    def load_from_file(self, filepath: str):
        """从文件加载"""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        loaded_count = 0
        for code, ind_data in data.get("indicators", {}).items():
            category = IndicatorCategory(ind_data.get("category", "custom"))
            indicator = IndicatorDefinition(
                code=ind_data["code"],
                name=ind_data["name"],
                category=category,
                unit=ind_data.get("unit", ""),
                description=ind_data.get("description", ""),
                formula=ind_data.get("formula"),
                required_data=ind_data.get("required_data", []),
                dependencies=ind_data.get("dependencies", []),
                threshold_high=ind_data.get("threshold_high"),
                threshold_low=ind_data.get("threshold_low"),
                tags=ind_data.get("tags", []),
            )
            self.register(indicator)
            loaded_count += 1

        logger.info(f"从 {filepath} 加载了 {loaded_count} 个指标")


# 全局单例
indicator_registry = IndicatorRegistry()


# 便捷函数
def register_indicator(
    code: str, name: str, category: str, unit: str, description: str, **kwargs
) -> IndicatorDefinition:
    """
    便捷的指标注册函数

    Example:
        register_indicator(
            code="custom_ratio",
            name="自定义比率",
            category="macro",
            unit="%",
            description="用户自定义指标",
            threshold_high=80.0
        )
    """
    cat = IndicatorCategory(category) if isinstance(category, str) else category
    indicator = IndicatorDefinition(code=code, name=name, category=cat, unit=unit, description=description, **kwargs)
    return indicator_registry.register(indicator)


def get_indicator(code: str) -> IndicatorDefinition | None:
    """获取指标定义"""
    return indicator_registry.get(code)


def list_indicators_by_category(category: str) -> list[IndicatorDefinition]:
    """按分类列出指标"""
    cat = IndicatorCategory(category) if isinstance(category, str) else category
    return indicator_registry.get_by_category(cat)


def search_indicators(keyword: str) -> list[IndicatorDefinition]:
    """搜索指标"""
    return indicator_registry.search(keyword)
