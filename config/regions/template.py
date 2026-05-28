"""
地区配置模板
"""
from typing import Dict, Any


class RegionConfig:
    """地区配置基类"""
    
    # 地区基本信息
    name: str = ""
    code: str = ""
    province: str = ""
    
    # 统计口径
    statistical_caliber: str = "city"
    
    # 行政区划
    administrative_divisions: Dict[str, Any] = {}
    
    # 经济指标权重
    indicator_weights: Dict[str, float] = {}
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": cls.name,
            "code": cls.code,
            "province": cls.province,
            "statistical_caliber": cls.statistical_caliber,
            "administrative_divisions": cls.administrative_divisions,
            "indicator_weights": cls.indicator_weights
        }
