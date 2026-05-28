"""
半导体产业配置
"""
from config.industries.template import IndustryConfig


class SemiconductorConfig(IndustryConfig):
    """半导体产业配置"""
    
    name = "半导体"
    code = "C39"
    category = "制造业"
    
    chain_links = [
        "上游：设计（EDA、IP核）",
        "上游：材料（硅片、光刻胶、靶材）",
        "上游：设备（光刻机、刻蚀机、薄膜沉积设备）",
        "中游：制造（晶圆代工）",
        "中游：封装测试",
        "下游：芯片设计公司",
        "下游：终端应用（消费电子、汽车电子、工业电子）"
    ]
    
    key_indicators = {
        "output_value": {"name": "产值", "unit": "亿元"},
        "employment": {"name": "就业人数", "unit": "万人"},
        "rd_intensity": {"name": "研发强度", "unit": "%"},
        "localization_rate": {"name": "本土化率", "unit": "%"}
    }
    
    characteristics = [
        "技术密集型",
        "资本密集型",
        "长周期研发",
        "产业链长",
        "全球竞争激烈"
    ]
