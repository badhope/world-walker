"""
分析 API 路由 - v2 版本，使用真实数据分析
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from backend.analysis.enterprise_analyzer_v2 import enterprise_analyzer_v2
from backend.analysis.real_data_analysis import real_data_analyzer
from config.analysis_config import AnalysisConfig

router = APIRouter(prefix="/analysis", tags=["产业分析"])


class AnalysisRequest(BaseModel):
    """分析请求"""

    region: str = AnalysisConfig.DEFAULT_REGION
    industry: str = AnalysisConfig.DEFAULT_INDUSTRY
    year: int = AnalysisConfig.DEFAULT_YEAR
    data: dict[str, Any] | None = None


@router.post("/enterprise/v2", summary="企业端分析 (v2)")
def enterprise_analysis_v2(request: AnalysisRequest):
    """
    Enterprise-side industry analysis v2:
    - Computes scores from real data
    - Anchored to published economic baselines
    - Returns actionable recommendations
    """
    try:
        logger.info(f"企业端分析 v2 请求: {request.region} - {request.industry} - {request.year}")

        # 如果请求中没有数据，使用默认示例数据
        if not request.data:
            request.data = {
                "region": request.region,
                "industry": request.industry,
                "year": request.year,
                "land_price": 800.0,
                "salary_level": 15000.0,
                "energy_cost": 1.2,
                "financing_cost": 4.5,
                "local_support_rate": 75.0,
                "avg_delivery_time": 3.0,
                "location_quotient": 2.5,
                "tax_reduction": 500.0,
                "tax_coverage": 85.0,
                "rd_subsidy": 200.0,
                "avg_approval_time": 5.0,
            }
        else:
            # 确保 data 包含地区、产业、年份信息
            request.data["region"] = request.region
            request.data["industry"] = request.industry
            request.data["year"] = request.year

        # 调用 v2 版本的分析器
        report = enterprise_analyzer_v2.generate_comprehensive_report(request.data)

        return {"status": "success", "version": "v2", "data": report}

    except Exception as e:
        logger.exception(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/enterprise/sample", summary="获取企业端示例数据")
def get_enterprise_sample_data(
    region: str = Query(AnalysisConfig.DEFAULT_REGION),
    industry: str = Query(AnalysisConfig.DEFAULT_INDUSTRY),
    year: int = Query(AnalysisConfig.DEFAULT_YEAR),
):
    """获取企业端分析的示例数据"""
    sample_data = {
        "region": region,
        "industry": industry,
        "year": year,
        "land_price": 800.0,
        "salary_level": 15000.0,
        "energy_cost": 1.2,
        "financing_cost": 4.5,
        "local_support_rate": 75.0,
        "avg_delivery_time": 3.0,
        "location_quotient": 2.5,
        "tax_reduction": 500.0,
        "tax_coverage": 85.0,
        "rd_subsidy": 200.0,
        "avg_approval_time": 5.0,
    }

    # 获取真实宏观经济数据作为参考
    try:
        macro_df = real_data_analyzer.fetch_macro_data()
        sample_data["macro_reference"] = {
            "available_years": len(macro_df),
            "latest_gdp": float(macro_df.iloc[-1]["gdp"]) if len(macro_df) > 0 else None,
            "data_source": "akshare",
        }
    except Exception as e:
        logger.warning(f"获取宏观参考数据失败: {e}")

    return sample_data


@router.get("/config", summary="获取分析配置")
def get_analysis_config():
    """获取分析平台的默认配置"""
    return AnalysisConfig.get_config()


# 保留旧版本的接口，但添加弃用警告
@router.post("/enterprise", summary="企业端分析 (v1 已弃用)", deprecated=True)
def enterprise_analysis_v1(request: AnalysisRequest):
    """企业端产业分析 v1 版本（已弃用，请使用 /enterprise/v2）"""
    logger.warning("使用了已弃用的 /enterprise v1 接口，请改用 /enterprise/v2")

    # 调用 v2 版本保持兼容
    return enterprise_analysis_v2(request)


@router.post("/government", summary="政府端分析 (v1)", response_model=dict)
def government_analysis(request: AnalysisRequest):
    """
    政府端产业分析：财政杠杆、产业带动、产业链分析
    （暂使用模拟数据，待后续开发 v2 版本）
    """
    try:
        logger.info(f"政府端分析请求: {request.region} - {request.industry} - {request.year}")

        # 暂时返回模拟数据
        report = {
            "status": "success",
            "note": "政府端分析 v2 版本开发中",
            "data": {
                "region": request.region,
                "industry": request.industry,
                "year": request.year,
                "fiscal_leverage": {"score": 72.5, "revenue_efficiency": 78.0, "expenditure_efficiency": 67.0},
                "industry_drive": {"score": 68.0, "employment_contribution": 72.0, "tax_contribution": 64.0},
            },
        }

        return report

    except Exception as e:
        error_detail = f"{str(e)}"
        logger.error(f"政府端分析失败: {error_detail}", exc_info=True)
        raise HTTPException(status_code=500, detail="政府端分析失败，请稍后重试")
