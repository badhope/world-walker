"""
深圳地区配置
"""

from config.regions.template import RegionConfig


class ShenzhenConfig(RegionConfig):
    """深圳配置"""

    name = "深圳"
    code = "440300"
    province = "广东省"
    country = "中国"

    statistical_caliber = "city"

    administrative_divisions = {
        "districts": ["福田区", "罗湖区", "南山区", "宝安区", "龙岗区", "盐田区", "龙华区", "坪山区", "光明区"],
        "development_zones": ["前海深港现代服务业合作区", "深圳高新区", "坪山高新区"],
    }

    indicator_weights = {
        "gdp": 0.25,
        "fiscal_revenue": 0.2,
        "industrial_output": 0.2,
        "employment": 0.15,
        "innovation": 0.2,
    }

    economic_characteristics = ["科技创新中心", "先进制造业基地", "金融中心", "对外贸易枢纽", "民营经济活跃"]

    benchmark_data = {
        "gdp_per_capita": 183000.0,  # 元/人
        "average_wage": 15000.0,  # 元/月
        "industrial_efficiency": 0.85,
        "land_price": 800.0,  # 元/平方米·年
        "energy_cost": 1.2,  # 元/千瓦时
    }

    data_sources = ["nbs", "guangdong_statistics_bureau", "shenzhen_statistics_bureau", "industry_association"]
