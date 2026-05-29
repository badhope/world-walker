"""
分析 API 路由 - 使用爬虫获取真实数据
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config.analysis_config import AnalysisConfig
from backend.data_collection.web_crawler import WebCrawler

router = APIRouter(prefix="/analysis", tags=["产业分析"])

# 初始化爬虫
crawler = WebCrawler()


class AnalysisRequest(BaseModel):
    """分析请求"""
    region: str = AnalysisConfig.DEFAULT_REGION
    industry: str = AnalysisConfig.DEFAULT_INDUSTRY
    year: int = AnalysisConfig.DEFAULT_YEAR
    data: Optional[Dict[str, Any]] = None


def get_real_data(year: int) -> Dict[str, Any]:
    """
    使用爬虫获取真实数据
    
    Args:
        year: 年份
        
    Returns:
        包含各类经济指标的字典
    """
    logger.info(f"正在获取 {year} 年的真实数据...")
    
    result = {}
    
    try:
        # 获取 GDP 数据
        gdp_data = crawler.fetch_data(indicator='gdp')
        if gdp_data:
            for item in gdp_data:
                if item['year'] == year:
                    result['gdp'] = item['value']
                    result['gdp_source'] = item['source']
                    break
        
        # 获取 CPI 数据
        cpi_data = crawler.fetch_data(indicator='cpi')
        if cpi_data:
            cpi_values = [item['value'] for item in cpi_data if item['year'] == year]
            if cpi_values:
                result['cpi'] = sum(cpi_values) / len(cpi_values)
                result['cpi_source'] = cpi_data[0]['source']
        
        # 获取财政数据
        fiscal_data = crawler.fetch_data(indicator='fiscal')
        if fiscal_data:
            for item in fiscal_data:
                if item['year'] == year:
                    result['fiscal_revenue'] = item['value']
                    result['fiscal_source'] = item['source']
                    break
        
        # 获取工业数据
        industry_data = crawler.fetch_data(indicator='industry')
        if industry_data:
            for item in industry_data:
                if item['year'] == year:
                    result['industrial_growth'] = item['value']
                    result['industrial_source'] = item['source']
                    break
        
        # 获取劳动力数据
        labor_data = crawler.fetch_data(indicator='labor')
        if labor_data:
            for item in labor_data:
                if item['year'] == year:
                    result['urban_employment'] = item['value']
                    result['labor_source'] = item['source']
                    break
        
        # 获取半导体数据（如果是半导体产业）
        semi_data = crawler.fetch_data(indicator='semiconductor')
        if semi_data:
            for item in semi_data:
                if item['year'] == year:
                    result['semiconductor_output'] = item['value']
                    result['semiconductor_source'] = item['source']
                    break
        
        logger.info(f"成功获取真实数据: {list(result.keys())}")
        
    except Exception as e:
        logger.error(f"获取真实数据失败: {e}")
        # 如果爬虫失败，使用模拟数据
        result = get_fallback_data(year)
    
    return result


def get_fallback_data(year: int) -> Dict[str, Any]:
    """
    获取模拟数据作为后备
    
    Args:
        year: 年份
        
    Returns:
        包含各类经济指标的字典
    """
    base_year = 2024
    year_diff = year - base_year
    
    fallback_data = {
        # GDP 数据（单位：亿元）
        "gdp": 1340000 + year_diff * 80000,
        "gdp_source": "simulated",
        
        # CPI 数据
        "cpi": 101.3 + year_diff * 0.2,
        "cpi_source": "simulated",
        
        # 财政数据（单位：亿元）
        "fiscal_revenue": 235000 + year_diff * 17000,
        "fiscal_source": "simulated",
        
        # 工业数据
        "industrial_growth": 5.2 + year_diff * 0.3,
        "industrial_source": "simulated",
        
        # 劳动力数据（单位：万人）
        "urban_employment": 1230 + year_diff * 10,
        "labor_source": "simulated",
        
        # 半导体数据（单位：亿元）
        "semiconductor_output": 16800 + year_diff * 2700,
        "semiconductor_source": "simulated",
    }
    
    return fallback_data


@router.post("/enterprise", summary="企业端分析")
def enterprise_analysis(request: AnalysisRequest):
    """企业端产业分析：营商成本、供应链配套、政策红利"""
    try:
        logger.info(f"企业端分析请求: {request.region} - {request.industry} - {request.year}")
        
        # 使用爬虫获取真实数据
        real_data = get_real_data(request.year)
        
        # 导入我们的示例分析器
        from examples.shenzhen_semiconductor_2025.enterprise_analysis import EnterpriseAnalysisRunner
        
        runner = EnterpriseAnalysisRunner()
        report = runner.generate_report()
        
        # 将真实数据注入到报告中
        if real_data:
            report['real_data'] = real_data
            report['data_source'] = "crawler" if 'nbs' in str(real_data.values()) else "simulated"
        
        return report
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"企业端分析失败: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/government", summary="政府端分析")
def government_analysis(request: AnalysisRequest):
    """政府端产业分析：财政杠杆、产业带动、产业链分析"""
    try:
        logger.info(f"政府端分析请求: {request.region} - {request.industry} - {request.year}")
        
        # 使用爬虫获取真实数据
        real_data = get_real_data(request.year)
        
        # 导入我们的示例分析器
        from examples.shenzhen_semiconductor_2025.government_analysis import GovernmentAnalysisRunner
        
        runner = GovernmentAnalysisRunner()
        report = runner.generate_report()
        
        # 将真实数据注入到报告中
        if real_data:
            report['real_data'] = real_data
            report['data_source'] = "crawler" if 'nbs' in str(real_data.values()) else "simulated"
        
        return report
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"政府端分析失败: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/config", summary="获取分析配置")
def get_analysis_config():
    """获取分析平台的默认配置"""
    return AnalysisConfig.get_config()


@router.get("/real-data", summary="获取真实数据")
def get_real_data_api(
    year: int = Query(AnalysisConfig.DEFAULT_YEAR),
    indicator: Optional[str] = Query(None)
):
    """
    使用爬虫获取真实经济数据
    
    Args:
        year: 年份
        indicator: 指标名称（可选）：gdp, cpi, fiscal, industry, labor, semiconductor
    
    Returns:
        真实经济数据
    """
    try:
        if indicator:
            # 获取指定指标的数据
            data = crawler.fetch_data(indicator=indicator)
            # 过滤指定年份的数据
            filtered_data = [item for item in data if item.get('year') == year]
            if not filtered_data:
                filtered_data = data  # 返回所有年份的数据
            return {
                "indicator": indicator,
                "year": year,
                "data": filtered_data,
                "count": len(filtered_data)
            }
        else:
            # 获取所有指标的数据
            result = get_real_data(year)
            return {
                "year": year,
                "data": result,
                "source": "crawler"
            }
            
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"获取真实数据失败: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/sample-data", summary="获取示例数据")
def get_sample_data(
    region: str = Query(AnalysisConfig.DEFAULT_REGION),
    industry: str = Query(AnalysisConfig.DEFAULT_INDUSTRY),
    year: int = Query(AnalysisConfig.DEFAULT_YEAR)
):
    """获取指定地区、产业、年份的示例数据"""
    # 获取真实数据作为基础
    real_data = get_real_data(year)
    
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
        # 财政（使用真实数据）
        "gdp": real_data.get('gdp', 35000.0),
        "revenue": real_data.get('fiscal_revenue', 4500.0) / 50,  # 按比例缩小到城市级别
        "expenditure": real_data.get('fiscal_revenue', 5000.0) / 47,
        "special_funds": 300.0,
        # 产业带动
        "employment_driven": real_data.get('urban_employment', 85.0),
        "tax_contribution": 600.0,
        "related_industry_output": 2500.0,
        "influence_coefficient": 1.5,
        "sensitivity_coefficient": 1.2,
        # 产业链
        "upstream_coverage": 0.8,
        "midstream_coverage": 0.9,
        "downstream_coverage": 0.7,
        "bottlenecks": ["高端光刻机", "先进制程工艺"],
        "digitalization_level": 0.85,
        # 真实数据来源
        "real_data_available": real_data,
        "data_source": real_data.get('gdp_source', 'simulated')
    }
    return sample_data
