"""
城市数据 API 路由 - 多城市数据聚合和对比分析
"""
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from backend.core.city_aggregation import city_aggregator, AggregationConfig, AggregationResult, ComparisonResult
from backend.core.multi_city import city_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cities", tags=["城市数据"])


# ==================== 请求和响应模型 ====================

class AggregationRequest(BaseModel):
    """聚合分析请求"""
    group_by: List[str] = Field(..., description="分组字段")
    metrics: List[str] = Field(..., description="聚合指标")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: str = Field('desc', description="排序顺序")
    limit: Optional[int] = Field(None, description="限制数量")


class ComparisonRequest(BaseModel):
    """城市对比请求"""
    city_codes: List[str] = Field(..., description="城市代码列表")
    indicators: List[str] = Field(..., description="要对比的指标列表")
    year_start: int = Field(..., description="开始年份")
    year_end: int = Field(..., description="结束年份")


class TimeSeriesRequest(BaseModel):
    """时间序列分析请求"""
    city_codes: List[str] = Field(..., description="城市代码列表")
    indicator: str = Field(..., description="指标代码")
    year_start: int = Field(..., description="开始年份")
    year_end: int = Field(..., description="结束年份")
    group_by: Optional[List[str]] = Field(None, description="分组字段")


class RegionalRequest(BaseModel):
    """区域分析请求"""
    region_field: str = Field('province', description="区域字段名")
    indicators: Optional[List[str]] = Field(None, description="指标列表")


class CorrelationRequest(BaseModel):
    """相关性分析请求"""
    city_codes: List[str] = Field(..., description="城市代码列表")
    indicators: List[str] = Field(..., description="指标列表")
    year_start: int = Field(..., description="开始年份")
    year_end: int = Field(..., description="结束年份")


# ==================== 聚合分析接口 ====================

@router.post("/aggregate", summary="数据聚合分析")
async def aggregate_data(request: AggregationRequest):
    """
    数据聚合分析
    
    支持多种聚合方式：
    - 按城市分组
    - 按年份分组
    - 按指标分组
    - 按区域分组
    
    支持的聚合指标：
    - count: 计数
    - sum: 求和
    - avg: 平均值
    - min: 最小值
    - max: 最大值
    - median: 中位数
    - std: 标准差
    """
    try:
        # 构建聚合配置
        config = AggregationConfig(
            group_by=request.group_by,
            metrics=request.metrics,
            filters=request.filters or {},
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            limit=request.limit
        )
        
        # 获取数据（使用模拟数据）
        data = _generate_mock_city_data()
        
        # 执行聚合
        result = city_aggregator.aggregate(data, config)
        
        return {
            'success': True,
            'result': {
                'groups': result.groups,
                'summary': result.summary,
                'metadata': result.metadata
            }
        }
        
    except Exception as e:
        logger.error(f"聚合分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/compare", summary="城市对比分析")
async def compare_cities(request: ComparisonRequest):
    """
    城市对比分析
    
    对比多个城市在指定指标上的表现
    """
    try:
        # 获取城市数据
        data = []
        for city_code in request.city_codes:
            city_config = city_manager.get_city(city_code)
            if not city_config:
                continue
            
            # 获取该城市的数据
            city_data = city_manager.get_city_data(city_code)
            
            for item in city_data:
                if request.year_start <= item.year <= request.year_end:
                    if item.indicators.get(request.indicators):
                        data.append({
                            'city': city_config.name,
                            'city_code': city_code,
                            'indicator': request.indicators[0],
                            'value': item.indicators.get(request.indicators[0]),
                            'year': item.year
                        })
        
        # 如果没有真实数据，使用模拟数据
        if not data:
            data = _generate_mock_city_data()
            data = [
                item for item in data 
                if item.get('city') in [
                    city_manager.get_city(c).name 
                    for c in request.city_codes
                ] and item.get('indicator') in request.indicators
            ]
        
        # 执行对比分析
        result = city_aggregator.compare_cities(
            data, 
            city_field='city',
            indicator_field='indicator',
            value_field='value'
        )
        
        return {
            'success': True,
            'comparison': {
                'cities': result.cities,
                'rankings': result.rankings,
                'insights': result.insights
            }
        }
        
    except Exception as e:
        logger.error(f"城市对比分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"城市对比分析失败: {str(e)}")


@router.post("/time-series", summary="时间序列分析")
async def time_series_analysis(request: TimeSeriesRequest):
    """
    时间序列分析
    
    分析城市指标随时间的变化趋势
    """
    try:
        # 获取城市数据
        data = []
        for city_code in request.city_codes:
            city_config = city_manager.get_city(city_code)
            if not city_config:
                continue
            
            city_data = city_manager.get_city_data(city_code)
            
            for item in city_data:
                if request.year_start <= item.year <= request.year_end:
                    if request.indicator in item.indicators:
                        data.append({
                            'city': city_config.name,
                            'city_code': city_code,
                            'indicator': request.indicator,
                            'value': item.indicators.get(request.indicator),
                            'year': item.year
                        })
        
        # 如果没有真实数据，使用模拟数据
        if not data:
            data = _generate_mock_city_data()
            data = [
                item for item in data 
                if item.get('city_code') in request.city_codes
                and item.get('indicator') == request.indicator
                and request.year_start <= item.get('year', 0) <= request.year_end
            ]
        
        # 执行时间序列分析
        result = city_aggregator.time_series_analysis(
            data,
            time_field='year',
            value_field='value',
            group_by=request.group_by or ['city_code']
        )
        
        return {
            'success': True,
            'time_series': result
        }
        
    except Exception as e:
        logger.error(f"时间序列分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/regional", summary="区域分析")
async def regional_analysis(request: RegionalRequest):
    """
    区域分析
    
    分析不同区域（省/城市群）的经济表现
    """
    try:
        # 生成模拟数据
        data = _generate_mock_city_data()
        
        # 执行区域分析
        result = city_aggregator.regional_analysis(
            data,
            city_field='city',
            region_field='region',
            value_field='value'
        )
        
        return {
            'success': True,
            'regional_analysis': result
        }
        
    except Exception as e:
        logger.error(f"区域分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/correlation", summary="相关性分析")
async def correlation_analysis(request: CorrelationRequest):
    """
    指标相关性分析
    
    分析不同指标之间的相关性
    """
    try:
        # 生成模拟数据
        data = _generate_mock_city_data()
        
        # 过滤到指定的指标
        data = [item for item in data if item.get('indicator') in request.indicators]
        
        # 执行相关性分析
        result = city_aggregator.correlation_analysis(
            data,
            indicators=request.indicators,
            city_field='city',
            year_field='year'
        )
        
        return {
            'success': True,
            'correlation': result
        }
        
    except Exception as e:
        logger.error(f"相关性分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/rankings", summary="城市排名")
async def get_city_rankings(
    indicator: str = Query('gdp', description="指标代码"),
    year: Optional[int] = Query(None, description="年份"),
    limit: int = Query(10, description="返回数量")
):
    """
    获取城市排名
    
    按指定指标返回城市排名
    """
    try:
        # 生成模拟数据
        data = _generate_mock_city_data()
        
        # 过滤数据
        if year:
            data = [item for item in data if item.get('year') == year]
        
        if indicator:
            data = [item for item in data if item.get('indicator') == indicator]
        
        # 聚合
        config = AggregationConfig(
            group_by=['city'],
            metrics=['sum'],
            sort_by='sum',
            sort_order='desc',
            limit=limit
        )
        
        result = city_aggregator.aggregate(data, config)
        
        return {
            'success': True,
            'indicator': indicator,
            'year': year,
            'rankings': [
                {
                    'rank': idx + 1,
                    'city': group['city'],
                    'value': group['sum']
                }
                for idx, group in enumerate(result.groups)
            ]
        }
        
    except Exception as e:
        logger.error(f"获取城市排名失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/dashboard", summary="城市仪表盘")
async def get_city_dashboard(city_code: str = Query(..., description="城市代码")):
    """
    获取城市仪表盘数据
    
    返回城市的多维度统计信息
    """
    try:
        city_config = city_manager.get_city(city_code)
        
        if not city_config:
            raise HTTPException(status_code=404, detail=f"城市不存在: {city_code}")
        
        # 获取该城市的数据
        city_data = city_manager.get_city_data(city_code)
        
        # 生成模拟仪表盘数据
        dashboard = {
            'city_info': {
                'code': city_config.code,
                'name': city_config.name,
                'province': city_config.province,
                'population': city_config.population,
                'gdp_rank': city_config.gdp_rank,
                'tags': city_config.tags
            },
            'overview': {
                'total_indicators': 15,
                'data_years': list(range(2020, 2026)),
                'data_sources': 3,
                'last_update': datetime.now().isoformat()
            },
            'trends': [
                {
                    'indicator': 'GDP',
                    'trend': 'increasing',
                    'change_rate': 6.5
                },
                {
                    'indicator': 'CPI',
                    'trend': 'stable',
                    'change_rate': 2.1
                },
                {
                    'indicator': 'PMI',
                    'trend': 'increasing',
                    'change_rate': 3.2
                }
            ],
            'rankings': {
                'gdp_national': city_config.gdp_rank,
                'innovation': 2,
                'business_env': 1
            }
        }
        
        return {
            'success': True,
            'dashboard': dashboard
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取城市仪表盘失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

def _generate_mock_city_data() -> List[Dict[str, Any]]:
    """生成模拟城市数据"""
    cities = [
        {'code': 'sz', 'name': '深圳', 'region': '广东'},
        {'code': 'sh', 'name': '上海', 'region': '上海'},
        {'code': 'bj', 'name': '北京', 'region': '北京'},
        {'code': 'gz', 'name': '广州', 'region': '广东'},
        {'code': 'hz', 'name': '杭州', 'region': '浙江'},
        {'code': 'wh', 'name': '武汉', 'region': '湖北'},
        {'code': 'cd', 'name': '成都', 'region': '四川'},
        {'code': 'nj', 'name': '南京', 'region': '江苏'},
    ]
    
    indicators = [
        {'code': 'gdp', 'name': 'GDP', 'base': 30000, 'variance': 5000},
        {'code': 'cpi', 'name': 'CPI', 'base': 102, 'variance': 2},
        {'code': 'pmi', 'name': 'PMI', 'base': 50, 'variance': 5},
        {'code': 'fiscal_revenue', 'name': '财政收入', 'base': 4000, 'variance': 500},
        {'code': 'industrial_output', 'name': '工业产值', 'base': 25000, 'variance': 3000},
    ]
    
    years = [2020, 2021, 2022, 2023, 2024, 2025]
    
    data = []
    
    rng = random.Random(42)

    for city in cities:
        for indicator in indicators:
            for year in years:
                base_value = indicator['base']

                if city['code'] == 'sz':
                    multiplier = 1.2
                elif city['code'] == 'sh':
                    multiplier = 1.5
                elif city['code'] == 'bj':
                    multiplier = 1.4
                else:
                    multiplier = 1.0

                year_multiplier = 1 + (year - 2020) * 0.05

                value = (base_value * multiplier * year_multiplier +
                        rng.uniform(-indicator['variance'], indicator['variance']))
                
                data.append({
                    'city': city['name'],
                    'city_code': city['code'],
                    'region': city['region'],
                    'indicator': indicator['code'],
                    'indicator_name': indicator['name'],
                    'value': round(value, 2),
                    'year': year
                })
    
    return data
