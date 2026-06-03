"""
多城市数据支持模块 - 支持多个城市的经济数据分析
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CityConfig:
    """城市配置"""

    code: str  # 城市代码，如 'sz' (深圳)
    name: str  # 城市名称
    province: str  # 所属省份
    latitude: float  # 纬度
    longitude: float  # 经度
    population: int  # 常住人口（万）
    gdp_rank: int  # GDP 排名
    timezone: str = "Asia/Shanghai"  # 时区
    description: str = ""  # 城市描述
    tags: list[str] = field(default_factory=list)  # 标签
    metadata: dict[str, Any] = field(default_factory=dict)  # 其他元数据


@dataclass
class CityData:
    """城市数据"""

    city_code: str
    city_name: str
    year: int
    quarter: int | None = None
    indicators: dict[str, Any] = field(default_factory=dict)  # 指标数据
    last_updated: datetime = field(default_factory=datetime.now)
    source: str = "nbs"  # 数据来源
    quality_score: float = 1.0  # 数据质量评分


class CityDataManager:
    """城市数据管理器"""

    # 预设城市配置
    PRESET_CITIES = {
        "sz": CityConfig(
            code="sz",
            name="深圳",
            province="广东",
            latitude=22.5431,
            longitude=114.0579,
            population=1756,
            gdp_rank=3,
            description="中国特色社会主义先行示范区",
            tags=["一线城市", "经济特区", "科技创新中心"],
        ),
        "sh": CityConfig(
            code="sh",
            name="上海",
            province="上海",
            latitude=31.2304,
            longitude=121.4737,
            population=2487,
            gdp_rank=1,
            description="国际经济、金融、贸易、航运、科技创新中心",
            tags=["一线城市", "直辖市", "国际金融中心"],
        ),
        "bj": CityConfig(
            code="bj",
            name="北京",
            province="北京",
            latitude=39.9042,
            longitude=116.4074,
            population=2189,
            gdp_rank=2,
            description="国家首都，政治文化中心",
            tags=["一线城市", "直辖市", "政治文化中心"],
        ),
        "gz": CityConfig(
            code="gz",
            name="广州",
            province="广东",
            latitude=23.1291,
            longitude=113.2644,
            population=1868,
            gdp_rank=4,
            description="国家中心城市，粤港澳大湾区核心城市",
            tags=["一线城市", "国家中心城市", "商贸中心"],
        ),
        "wh": CityConfig(
            code="wh",
            name="武汉",
            province="湖北",
            latitude=30.5928,
            longitude=114.3055,
            population=1365,
            gdp_rank=9,
            description="中部地区中心城市，长江经济带核心城市",
            tags=["新一线城市", "国家中心城市", "科教基地"],
        ),
        "cd": CityConfig(
            code="cd",
            name="成都",
            province="四川",
            latitude=30.5728,
            longitude=104.0668,
            population=2140,
            gdp_rank=7,
            description="西部地区重要的中心城市",
            tags=["新一线城市", "国家中心城市", "天府之国"],
        ),
        "hz": CityConfig(
            code="hz",
            name="杭州",
            province="浙江",
            latitude=30.2741,
            longitude=120.1551,
            population=1390,
            gdp_rank=5,
            description="数字经济第一城，电子商务中心",
            tags=["新一线城市", "互联网经济", "数字经济"],
        ),
        "nj": CityConfig(
            code="nj",
            name="南京",
            province="江苏",
            latitude=32.0603,
            longitude=118.7969,
            population=953,
            gdp_rank=10,
            description="东部地区重要的中心城市",
            tags=["新一线城市", "国家中心城市", "科教名城"],
        ),
    }

    def __init__(self):
        """初始化管理器"""
        self.cities: dict[str, CityConfig] = {}
        self.city_data: dict[str, dict[int, CityData]] = {}  # {city_code: {year: CityData}}
        self.custom_city_loader: Callable | None = None

        # 加载预设城市
        for code, config in self.PRESET_CITIES.items():
            self.register_city(config)

    def register_city(self, config: CityConfig) -> bool:
        """
        注册城市

        Args:
            config: 城市配置

        Returns:
            是否成功
        """
        if config.code in self.cities:
            logger.warning(f"城市已存在: {config.code}")
            return False

        self.cities[config.code] = config
        self.city_data[config.code] = {}

        logger.info(f"城市注册成功: {config.name} ({config.code})")
        return True

    def unregister_city(self, city_code: str) -> bool:
        """
        注销城市

        Args:
            city_code: 城市代码

        Returns:
            是否成功
        """
        if city_code not in self.cities:
            logger.warning(f"城市不存在: {city_code}")
            return False

        del self.cities[city_code]
        del self.city_data[city_code]

        logger.info(f"城市注销成功: {city_code}")
        return True

    def get_city(self, city_code: str) -> CityConfig | None:
        """
        获取城市配置

        Args:
            city_code: 城市代码

        Returns:
            城市配置
        """
        return self.cities.get(city_code)

    def list_cities(self, filters: dict[str, Any] | None = None) -> list[CityConfig]:
        """
        列出城市

        Args:
            filters: 过滤条件（如 province, tags, gdp_rank 等）

        Returns:
            城市配置列表
        """
        cities = list(self.cities.values())

        if not filters:
            return cities

        # 应用过滤条件
        if "province" in filters:
            cities = [c for c in cities if c.province == filters["province"]]

        if "tags" in filters:
            filter_tags = filters["tags"]
            if isinstance(filter_tags, str):
                filter_tags = [filter_tags]
            cities = [c for c in cities if any(tag in c.tags for tag in filter_tags)]

        if "gdp_rank_le" in filters:
            cities = [c for c in cities if c.gdp_rank <= filters["gdp_rank_le"]]

        return cities

    def add_city_data(self, data: CityData) -> bool:
        """
        添加城市数据

        Args:
            data: 城市数据

        Returns:
            是否成功
        """
        if data.city_code not in self.cities:
            logger.error(f"城市不存在: {data.city_code}")
            return False

        # 使用年份作为主键
        year = data.year

        if year not in self.city_data[data.city_code]:
            self.city_data[data.city_code][year] = []

        self.city_data[data.city_code][year].append(data)
        logger.debug(f"城市数据添加成功: {data.city_name} {year}")
        return True

    def get_city_data(self, city_code: str, year: int | None = None) -> list[CityData]:
        """
        获取城市数据

        Args:
            city_code: 城市代码
            year: 年份（可选，返回该年份数据）

        Returns:
            城市数据列表
        """
        if city_code not in self.city_data:
            return []

        if year is None:
            # 返回所有年份的数据
            all_data = []
            for year_data in self.city_data[city_code].values():
                all_data.extend(year_data)
            return all_data
        else:
            return self.city_data[city_code].get(year, [])

    def compare_cities(self, city_codes: list[str], year: int, indicators: list[str]) -> dict[str, dict[str, Any]]:
        """
        城市对比分析

        Args:
            city_codes: 城市代码列表
            year: 年份
            indicators: 指标列表

        Returns:
            对比结果
        """
        results = {}

        for city_code in city_codes:
            city_data = self.get_city_data(city_code, year)
            city_config = self.get_city(city_code)

            if not city_config or not city_data:
                continue

            result = {"city_name": city_config.name, "year": year, "indicators": {}}

            for data in city_data:
                for indicator in indicators:
                    if indicator in data.indicators:
                        result["indicators"][indicator] = data.indicators[indicator]

            results[city_code] = result

        return results

    def export_city_summary(self, output_path: Path) -> bool:
        """
        导出城市摘要

        Args:
            output_path: 输出路径

        Returns:
            是否成功
        """
        try:
            import json

            summary = {"export_time": datetime.now().isoformat(), "total_cities": len(self.cities), "cities": []}

            for city_code, config in self.cities.items():
                city_info = {
                    "code": config.code,
                    "name": config.name,
                    "province": config.province,
                    "population": config.population,
                    "gdp_rank": config.gdp_rank,
                    "tags": config.tags,
                    "data_years": list(self.city_data[city_code].keys()),
                }
                summary["cities"].append(city_info)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            logger.info(f"城市摘要导出成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"城市摘要导出失败: {e}")
            return False

    def load_custom_cities(self, config_path: Path) -> int:
        """
        加载自定义城市配置

        Args:
            config_path: 配置文件路径

        Returns:
            加载的城市数量
        """
        try:
            import yaml

            with open(config_path, encoding="utf-8") as f:
                configs = yaml.safe_load(f)

            count = 0
            for city_data in configs.get("cities", []):
                config = CityConfig(
                    code=city_data["code"],
                    name=city_data["name"],
                    province=city_data["province"],
                    latitude=city_data["latitude"],
                    longitude=city_data["longitude"],
                    population=city_data["population"],
                    gdp_rank=city_data["gdp_rank"],
                    description=city_data.get("description", ""),
                    tags=city_data.get("tags", []),
                    metadata=city_data.get("metadata", {}),
                )

                if self.register_city(config):
                    count += 1

            logger.info(f"自定义城市加载完成: {count} 个")
            return count

        except Exception as e:
            logger.error(f"自定义城市加载失败: {e}")
            return 0


# 全局实例
city_manager = CityDataManager()
