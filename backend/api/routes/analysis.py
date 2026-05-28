"""
分析 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config.analysis_config import AnalysisConfig

router = APIRouter(prefix="/analysis", tags=["产业分析"])


class AnalysisRequest(BaseModel):
    """分析请求"""
    region: str = AnalysisConfig.DEFAULT_REGION
    industry: str = AnalysisConfig.DEFAULT_INDUSTRY
    year: int = AnalysisConfig.DEFAULT_YEAR
    data: Optional[Dict[str, Any]] = None


@router.post("/enterprise", summary="企业端分析")
def enterprise_analysis(request: AnalysisRequest):
    """企业端产业分析：营商成本、供应链配套、政策红利"""
    try:
        # 导入我们的示例分析器
        from examples.shenzhen_semiconductor_2025.enterprise_analysis import EnterpriseAnalysisRunner
        
        runner = EnterpriseAnalysisRunner()
        report = runner.generate_report()
        return report
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/government", summary="政府端分析")
def government_analysis(request: AnalysisRequest):
    """政府端产业分析：财政杠杆、产业带动、产业链分析"""
    try:
        # 导入我们的示例分析器
        from examples.shenzhen_semiconductor_2025.government_analysis import GovernmentAnalysisRunner
        
        runner = GovernmentAnalysisRunner()
        report = runner.generate_report()
        return report
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/config", summary="获取分析配置")
def get_analysis_config():
    """获取分析平台的默认配置"""
    return AnalysisConfig.get_config()


@router.get("/sample-data", summary="获取示例数据")
def get_sample_data(
    region: str = Query(AnalysisConfig.DEFAULT_REGION),
    industry: str = Query(AnalysisConfig.DEFAULT_INDUSTRY),
    year: int = Query(AnalysisConfig.DEFAULT_YEAR)
):
    """获取指定地区、产业、年份的示例数据（模拟）"""
    sample_data = {
        "region": region,
        "industry": industry,
        "year": year,
        # 营商成本
        "land_price": 800.0,
        "salary_level": 15000.0,
        "energy_cost": 1.2,
        "financing_cost": 4.5,
        # 供应链
        "local_support_rate": 75.0,
        "avg_delivery_time": 3.0,
        "location_quotient": 2.5,
        # 政策
        "tax_reduction": 500.0,
        "tax_coverage": 85.0,
        "rd_subsidy": 200.0,
        "avg_approval_time": 5.0,
        # 财政
        "gdp": 35000.0,
        "revenue": 4500.0,
        "expenditure": 5000.0,
        "special_funds": 300.0,
        # 产业带动
        "employment_driven": 85.0,
        "tax_contribution": 600.0,
        "related_industry_output": 2500.0,
        "influence_coefficient": 1.5,
        "sensitivity_coefficient": 1.2,
        # 产业链
        "upstream_coverage": 0.8,
        "midstream_coverage": 0.9,
        "downstream_coverage": 0.7,
        "bottlenecks": ["高端光刻机", "先进制程工艺"],
        "digitalization_level": 0.85
    }
    return sample_data
