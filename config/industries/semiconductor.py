"""
半导体产业配置
"""

from config.industries.template import IndustryConfig


class SemiconductorConfig(IndustryConfig):
    """半导体产业配置"""

    name = "半导体"
    code = "C39"
    category = "制造业"
    industry_level = "secondary"

    chain_links = [
        "上游：设计（EDA、IP核）",
        "上游：材料（硅片、光刻胶、靶材）",
        "上游：设备（光刻机、刻蚀机、薄膜沉积设备）",
        "中游：制造（晶圆代工）",
        "中游：封装测试",
        "下游：芯片设计公司",
        "下游：终端应用（消费电子、汽车电子、工业电子）",
    ]

    key_indicators = {
        "output_value": {"name": "产值", "unit": "亿元"},
        "employment": {"name": "就业人数", "unit": "万人"},
        "rd_intensity": {"name": "研发强度", "unit": "%"},
        "localization_rate": {"name": "本土化率", "unit": "%"},
        "wafer_capacity": {"name": "晶圆产能", "unit": "万片/月"},
        "export_value": {"name": "出口额", "unit": "亿美元"},
    }

    characteristics = ["技术密集型", "资本密集型", "长周期研发", "产业链长", "全球竞争激烈", "高附加值"]

    chain_analysis = {
        "upstream_weight": 0.4,
        "midstream_weight": 0.35,
        "downstream_weight": 0.25,
        "key_bottlenecks": ["高端光刻机", "先进制程工艺", "高端芯片设计EDA工具", "关键材料（光刻胶、电子特气）"],
    }

    market_data = {
        "market_size": 12000.0,  # 亿元
        "growth_rate": 15.0,  # %
        "global_market_share": 8.5,  # %
        "export_ratio": 45.0,  # %
    }

    technology_maturity = {
        "rd_intensity": 12.0,  # 研发强度
        "patent_count": 50000,
        "technology_level": "catching_up",  # leading, developing, catching_up
    }

    enterprise_structure = {
        "total_enterprises": 2000,
        "large_enterprises": 50,
        "sme_count": 1950,
        "leading_enterprises": ["华为海思", "中芯国际", "长江存储", "长鑫存储", "北方华创", "中微公司"],
    }
