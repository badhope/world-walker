"""
城市数据聚合分析模块 - 多城市数据聚合和统计分析
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AggregationConfig:
    """聚合配置"""

    group_by: list[str]  # 分组字段
    metrics: list[str]  # 聚合指标
    filters: dict[str, Any] = field(default_factory=dict)  # 过滤条件
    sort_by: str | None = None  # 排序字段
    sort_order: str = "desc"  # 排序顺序
    limit: int | None = None  # 限制数量


@dataclass
class AggregationResult:
    """聚合结果"""

    groups: list[dict[str, Any]]  # 分组结果
    summary: dict[str, Any]  # 汇总统计
    metadata: dict[str, Any]  # 元数据


@dataclass
class ComparisonResult:
    """对比结果"""

    cities: list[dict[str, Any]]  # 城市数据
    indicators: dict[str, Any]  # 指标对比
    rankings: dict[str, list[dict[str, Any]]]  # 排名
    insights: list[str]  # 洞察


class CityDataAggregator:
    """城市数据聚合器"""

    def __init__(self):
        """初始化聚合器"""
        self.data_cache: dict[str, list[dict[str, Any]]] = {}

    def aggregate(self, data: list[dict[str, Any]], config: AggregationConfig) -> AggregationResult:
        """
        数据聚合

        Args:
            data: 原始数据列表
            config: 聚合配置

        Returns:
            聚合结果
        """
        # 过滤数据
        filtered_data = self._apply_filters(data, config.filters)

        # 分组
        groups_data = self._group_data(filtered_data, config.group_by)

        # 计算聚合指标
        groups = []
        for group_key, group_items in groups_data.items():
            group_result = {key: value for key, value in zip(config.group_by, self._parse_group_key(group_key))}

            # 计算每个指标
            for metric in config.metrics:
                if metric == "count":
                    group_result["count"] = len(group_items)
                elif metric == "sum":
                    group_result["sum"] = sum(float(item.get("value", 0)) for item in group_items)
                elif metric == "avg":
                    values = [float(item.get("value", 0)) for item in group_items]
                    group_result["avg"] = statistics.mean(values) if values else 0
                elif metric == "min":
                    values = [float(item.get("value", 0)) for item in group_items]
                    group_result["min"] = min(values) if values else 0
                elif metric == "max":
                    values = [float(item.get("value", 0)) for item in group_items]
                    group_result["max"] = max(values) if values else 0
                elif metric == "median":
                    values = [float(item.get("value", 0)) for item in group_items]
                    group_result["median"] = statistics.median(values) if values else 0
                elif metric == "std":
                    values = [float(item.get("value", 0)) for item in group_items]
                    group_result["std"] = statistics.stdev(values) if len(values) > 1 else 0

            groups.append(group_result)

        # 排序
        if config.sort_by:
            reverse = config.sort_order == "desc"
            groups = sorted(groups, key=lambda x: x.get(config.sort_by, 0), reverse=reverse)

        # 限制数量
        if config.limit:
            groups = groups[: config.limit]

        # 计算汇总统计
        summary = self._calculate_summary(groups, config.metrics)

        return AggregationResult(
            groups=groups,
            summary=summary,
            metadata={
                "total_records": len(data),
                "filtered_records": len(filtered_data),
                "group_count": len(groups),
                "timestamp": datetime.now().isoformat(),
            },
        )

    def compare_cities(
        self,
        data: list[dict[str, Any]],
        city_field: str = "city",
        indicator_field: str = "indicator",
        value_field: str = "value",
    ) -> ComparisonResult:
        """
        城市对比分析

        Args:
            data: 数据列表
            city_field: 城市字段名
            indicator_field: 指标字段名
            value_field: 数值字段名

        Returns:
            对比结果
        """
        # 按城市分组
        cities_data = defaultdict(lambda: defaultdict(list))

        for item in data:
            city = item.get(city_field, "Unknown")
            indicator = item.get(indicator_field, "Unknown")
            value = float(item.get(value_field, 0))

            cities_data[city][indicator].append(value)

        # 计算每个城市的统计数据
        cities = []
        for city, indicators in cities_data.items():
            city_stats = {"city": city, "indicators": {}}

            for indicator, values in indicators.items():
                city_stats["indicators"][indicator] = {
                    "sum": sum(values),
                    "avg": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "median": statistics.median(values),
                    "count": len(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                }

            cities.append(city_stats)

        # 计算指标排名
        rankings = defaultdict(list)
        for city in cities:
            for indicator, stats in city["indicators"].items():
                rankings[indicator].append({"city": city["city"], "value": stats["avg"]})

        # 对每个指标进行排名
        for indicator in rankings:
            rankings[indicator] = sorted(rankings[indicator], key=lambda x: x["value"], reverse=True)

        # 生成洞察
        insights = self._generate_insights(cities, rankings)

        return ComparisonResult(cities=cities, indicators={}, rankings=dict(rankings), insights=insights)

    def time_series_analysis(
        self,
        data: list[dict[str, Any]],
        time_field: str = "year",
        value_field: str = "value",
        group_by: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        时间序列分析

        Args:
            data: 数据列表
            time_field: 时间字段名
            value_field: 数值字段名
            group_by: 分组字段

        Returns:
            时间序列分析结果
        """
        if not group_by:
            # 简单时间序列
            time_series = defaultdict(list)

            for item in data:
                time_point = item.get(time_field)
                value = float(item.get(value_field, 0))
                time_series[time_point].append(value)

            result = {"time_points": [], "values": [], "trend": []}

            for time_point in sorted(time_series.keys()):
                result["time_points"].append(time_point)
                values = time_series[time_point]
                result["values"].append(statistics.mean(values))

            # 计算趋势
            result["trend"] = self._calculate_trend(result["values"])

            return result
        else:
            # 分组时间序列
            grouped_series = defaultdict(lambda: defaultdict(list))

            for item in data:
                key = tuple(item.get(field) for field in group_by)
                time_point = item.get(time_field)
                value = float(item.get(value_field, 0))

                grouped_series[key][time_point].append(value)

            result = {}
            for key, time_series in grouped_series.items():
                key_str = "_".join(str(k) for k in key)
                series_data = {"groups": list(key), "time_points": [], "values": [], "trend": []}

                for time_point in sorted(time_series.keys()):
                    series_data["time_points"].append(time_point)
                    values = time_series[time_point]
                    series_data["values"].append(statistics.mean(values))

                series_data["trend"] = self._calculate_trend(series_data["values"])
                result[key_str] = series_data

            return result

    def regional_analysis(
        self,
        data: list[dict[str, Any]],
        city_field: str = "city",
        region_field: str = "province",
        value_field: str = "value",
    ) -> dict[str, Any]:
        """
        区域分析

        Args:
            data: 数据列表
            city_field: 城市字段名
            region_field: 区域字段名
            value_field: 数值字段名

        Returns:
            区域分析结果
        """
        # 按区域分组
        region_data = defaultdict(lambda: {"cities": set(), "values": []})
        city_region_map = {}

        for item in data:
            city = item.get(city_field, "Unknown")
            region = item.get(region_field, "Unknown")
            value = float(item.get(value_field, 0))

            region_data[region]["cities"].add(city)
            region_data[region]["values"].append(value)
            city_region_map[city] = region

        # 计算区域统计
        regions = []
        for region, stats in region_data.items():
            values = stats["values"]
            region_info = {
                "region": region,
                "city_count": len(stats["cities"]),
                "cities": list(stats["cities"]),
                "total": sum(values),
                "avg": statistics.mean(values),
                "min": min(values),
                "max": max(values),
                "median": statistics.median(values),
            }
            regions.append(region_info)

        # 排序
        regions = sorted(regions, key=lambda x: x["avg"], reverse=True)

        return {
            "regions": regions,
            "total_regions": len(regions),
            "city_region_map": city_region_map,
            "timestamp": datetime.now().isoformat(),
        }

    def correlation_analysis(
        self, data: list[dict[str, Any]], indicators: list[str], city_field: str = "city", year_field: str = "year"
    ) -> dict[str, Any]:
        """
        指标相关性分析

        Args:
            data: 数据列表
            indicators: 指标列表
            city_field: 城市字段名
            year_field: 年份字段名

        Returns:
            相关性分析结果
        """
        # 构建城市-年份-指标矩阵
        matrix = defaultdict(lambda: defaultdict(dict))

        for item in data:
            city = item.get(city_field)
            year = item.get(year_field)
            indicator = item.get("indicator")
            value = float(item.get("value", 0))

            if indicator in indicators:
                matrix[(city, year)][indicator] = value

        # 计算相关系数矩阵
        correlation_matrix = {}

        for i, ind1 in enumerate(indicators):
            correlation_matrix[ind1] = {}

            for j, ind2 in enumerate(indicators):
                if i == j:
                    correlation_matrix[ind1][ind2] = 1.0
                    continue

                # 收集两个指标的所有配对值
                values1 = []
                values2 = []

                for key, indicators_dict in matrix.items():
                    if ind1 in indicators_dict and ind2 in indicators_dict:
                        values1.append(indicators_dict[ind1])
                        values2.append(indicators_dict[ind2])

                # 计算皮尔逊相关系数
                if len(values1) > 1:
                    corr = self._pearson_correlation(values1, values2)
                    correlation_matrix[ind1][ind2] = corr
                else:
                    correlation_matrix[ind1][ind2] = 0.0

        return {
            "correlation_matrix": correlation_matrix,
            "indicators": indicators,
            "timestamp": datetime.now().isoformat(),
        }

    def _apply_filters(self, data: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
        """应用过滤条件"""
        if not filters:
            return data

        filtered = data
        for field_name, condition in filters.items():
            if isinstance(condition, dict):
                # 范围过滤
                if "min" in condition:
                    filtered = [item for item in filtered if float(item.get(field_name, 0)) >= condition["min"]]
                if "max" in condition:
                    filtered = [item for item in filtered if float(item.get(field_name, 0)) <= condition["max"]]
            else:
                # 精确匹配
                filtered = [item for item in filtered if item.get(field_name) == condition]

        return filtered

    def _group_data(self, data: list[dict[str, Any]], group_by: list[str]) -> dict[str, list[dict[str, Any]]]:
        """分组数据"""
        groups = defaultdict(list)

        for item in data:
            key = tuple(item.get(field) for field in group_by)
            groups[key].append(item)

        return groups

    def _parse_group_key(self, group_key: tuple) -> list[Any]:
        """解析分组键"""
        return list(group_key)

    def _calculate_summary(self, groups: list[dict[str, Any]], metrics: list[str]) -> dict[str, Any]:
        """计算汇总统计"""
        summary = {"group_count": len(groups)}

        for metric in metrics:
            if metric == "count":
                summary["total_count"] = sum(g.get("count", 0) for g in groups)
            elif metric in ["sum", "avg", "min", "max"]:
                values = [g.get(metric, 0) for g in groups if g.get(metric) is not None]
                if values:
                    summary[f"{metric}_total"] = sum(values)
                    summary[f"{metric}_avg"] = statistics.mean(values)

        return summary

    def _generate_insights(self, cities: list[dict[str, Any]], rankings: dict[str, list[dict[str, Any]]]) -> list[str]:
        """生成洞察"""
        insights = []

        # 找出各指标第一名
        for indicator, ranking in rankings.items():
            if ranking:
                top_city = ranking[0]["city"]
                top_value = ranking[0]["value"]
                insights.append(f"{indicator}最高城市: {top_city} ({top_value:.2f})")

        return insights

    def _calculate_trend(self, values: list[float]) -> str:
        """计算趋势"""
        if len(values) < 2:
            return "insufficient_data"

        # 简单线性回归
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)

        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if abs(slope) < 0.01:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"

    def _pearson_correlation(self, x: list[float], y: list[float]) -> float:
        """计算皮尔逊相关系数"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        denominator_x = sum((xi - x_mean) ** 2 for xi in x)
        denominator_y = sum((yi - y_mean) ** 2 for yi in y)

        denominator = (denominator_x * denominator_y) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator


# 全局实例
city_aggregator = CityDataAggregator()
