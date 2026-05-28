"""
产业配置模板
"""
from typing import Dict, Any, List


class IndustryConfig:
    """产业配置基类"""
    
    # 产业基本信息
    name: str = ""
    code: str = ""
    category: str = ""
    
    # 产业链环节
    chain_links: List[str] = []
    
    # 关键指标定义
    key_indicators: Dict[str, Any] = {}
    
    # 产业特点
    characteristics: List[str] = []
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": cls.name,
            "code": cls.code,
            "category": cls.category,
            "chain_links": cls.chain_links,
            "key_indicators": cls.key_indicators,
            "characteristics": cls.characteristics
        }
