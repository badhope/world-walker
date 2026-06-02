"""
前后端交互 API 路由 - 支持前端交互操作
"""
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import ast
import operator as op
import math

from backend.core.data_import_export import data_manager, DataImportExportManager
from backend.core.multi_city import city_manager, CityConfig, CityData
from backend.core.cache import cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interactive", tags=["交互操作"])

_SAFE_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg,
}

_SAFE_FUNCS = {
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'sqrt': math.sqrt, 'log': math.log, 'exp': math.exp,
    'abs': abs, 'round': round, 'max': max, 'min': min,
    'sum': sum,
}


def _safe_eval(expr: str, variables: dict) -> float:
    try:
        import numexpr
        return float(numexpr.evaluate(expr, local_dict=variables))
    except ImportError:
        pass
    tree = ast.parse(expr, mode='eval')
    return _eval_node(tree.body, variables)


def _eval_node(node, variables):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        raise ValueError(f"Unknown variable: {node.id}")
    elif isinstance(node, ast.BinOp):
        return _SAFE_OPS[type(node.op)](_eval_node(node.left, variables), _eval_node(node.right, variables))
    elif isinstance(node, ast.UnaryOp):
        return _SAFE_OPS[type(node.op)](_eval_node(node.operand, variables))
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _SAFE_FUNCS:
            args = [_eval_node(a, variables) for a in node.args]
            return _SAFE_FUNCS[node.func.id](*args)
    raise ValueError(f"Unsafe expression: {type(node)}")


# ==================== 请求和响应模型 ====================

class DataImportRequest(BaseModel):
    """数据导入请求"""
    file_name: str = Field(..., description="文件名")
    file_content: str = Field(..., description="文件内容（Base64编码）")
    format_type: str = Field(..., description="格式类型: json, csv, xlsx")
    do_validate: bool = Field(True, description="是否验证数据", alias="validate")


class DataExportRequest(BaseModel):
    """数据导出请求"""
    data: List[Dict[str, Any]] = Field(..., description="要导出的数据")
    format_type: str = Field(..., description="格式类型: json, csv, xlsx")
    file_name: Optional[str] = Field(None, description="文件名")


class CityQueryRequest(BaseModel):
    """城市查询请求"""
    city_codes: List[str] = Field(..., description="城市代码列表")
    year: int = Field(..., description="年份")
    indicators: List[str] = Field(..., description="要查询的指标列表")


class IndicatorAnalysisRequest(BaseModel):
    """指标分析请求"""
    indicator_code: str = Field(..., description="指标代码")
    city_codes: List[str] = Field(..., description="城市代码列表")
    start_year: int = Field(..., description="开始年份")
    end_year: int = Field(..., description="结束年份")
    dimensions: Optional[List[str]] = Field(None, description="分析维度")


class CustomCalculationRequest(BaseModel):
    """自定义计算请求"""
    formula: str = Field(..., description="计算公式")
    variables: Dict[str, Any] = Field(..., description="变量值")
    description: Optional[str] = Field(None, description="计算描述")


class ScenarioCreateRequest(BaseModel):
    """场景创建请求"""
    name: str = Field(..., description="场景名称")
    description: Optional[str] = Field(None, description="场景描述")
    config: Dict[str, Any] = Field(..., description="场景配置")
    tags: Optional[List[str]] = Field(None, description="标签")


# ==================== 数据导入导出接口 ====================

@router.post("/import", summary="导入数据")
async def import_data(request: DataImportRequest):
    """
    导入数据
    
    支持 JSON、CSV、Excel 格式
    """
    try:
        import base64
        from pathlib import Path
        
        # 解码文件内容
        try:
            content = base64.b64decode(request.file_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Base64 decoding failed")
        
        # 保存临时文件
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / request.file_name
        
        with open(temp_file, 'wb') as f:
            f.write(content)
        
        # 导入数据
        data = data_manager.import_data(temp_file, request.format_type)
        
        # 清理临时文件
        temp_file.unlink(missing_ok=True)
        
        if not data:
            raise HTTPException(status_code=400, detail="数据导入失败或数据为空")
        
        # 验证数据
        if request.do_validate:
            validation_result = {
                'total_records': len(data),
                'required_fields': ['code', 'name', 'value', 'year'],
                'has_required_fields': all(
                    all(field in item for field in ['code', 'name', 'value', 'year'])
                    for item in data
                )
            }
            
            return {
                'success': True,
                'message': '数据导入成功',
                'data': data[:10],  # 返回前10条预览
                'total_count': len(data),
                'validation': validation_result
            }
        
        return {
            'success': True,
            'message': '数据导入成功',
            'data': data[:10],
            'total_count': len(data)
        }
        
    except Exception as e:
        logger.error(f"数据导入失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/export", summary="导出数据")
async def export_data(request: DataExportRequest):
    """
    导出数据
    
    支持 JSON、CSV、Excel 格式
    """
    try:
        import base64
        from pathlib import Path
        
        # 生成文件名
        if not request.file_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = request.format_type
            request.file_name = f"export_{timestamp}.{extension}"
        
        # 导出到临时目录
        temp_dir = Path("temp_exports")
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / request.file_name
        
        success = data_manager.export_data(request.data, temp_file, request.format_type)
        
        if not success:
            raise HTTPException(status_code=500, detail="数据导出失败")
        
        # 读取文件内容并转为 Base64
        with open(temp_file, 'rb') as f:
            file_content = base64.b64encode(f.read()).decode('utf-8')
        
        # 清理临时文件
        temp_file.unlink(missing_ok=True)
        
        return {
            'success': True,
            'message': '数据导出成功',
            'file_name': request.file_name,
            'file_content': file_content,
            'record_count': len(request.data)
        }
        
    except Exception as e:
        logger.error(f"数据导出失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/formats", summary="获取支持的格式")
async def get_supported_formats():
    """
    获取支持的数据格式
    """
    formats = data_manager.get_supported_formats()
    return {
        'success': True,
        'formats': formats
    }


# ==================== 城市数据接口 ====================

@router.get("/cities", summary="获取城市列表")
async def get_cities(
    province: Optional[str] = Query(None, description="省份过滤"),
    tags: Optional[str] = Query(None, description="标签过滤，逗号分隔"),
    gdp_rank_le: Optional[int] = Query(None, description="GDP排名上限")
):
    """
    获取城市列表
    
    支持按省份、标签、GDP排名过滤
    """
    try:
        filters = {}
        
        if province:
            filters['province'] = province
        
        if tags:
            filters['tags'] = tags.split(',')
        
        if gdp_rank_le:
            filters['gdp_rank_le'] = gdp_rank_le
        
        cities = city_manager.list_cities(filters)
        
        return {
            'success': True,
            'total': len(cities),
            'cities': [
                {
                    'code': c.code,
                    'name': c.name,
                    'province': c.province,
                    'population': c.population,
                    'gdp_rank': c.gdp_rank,
                    'tags': c.tags,
                    'description': c.description
                }
                for c in cities
            ]
        }
        
    except Exception as e:
        logger.error(f"获取城市列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取城市列表失败: {str(e)}")


@router.get("/cities/{city_code}", summary="获取城市详情")
async def get_city_detail(city_code: str):
    """
    获取城市详情
    """
    try:
        city = city_manager.get_city(city_code)
        
        if not city:
            raise HTTPException(status_code=404, detail=f"城市不存在: {city_code}")
        
        # 获取数据年份
        data_years = list(city_manager.city_data.get(city_code, {}).keys())
        
        return {
            'success': True,
            'city': {
                'code': city.code,
                'name': city.name,
                'province': city.province,
                'latitude': city.latitude,
                'longitude': city.longitude,
                'population': city.population,
                'gdp_rank': city.gdp_rank,
                'tags': city.tags,
                'description': city.description,
                'available_years': sorted(data_years)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取城市详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取城市详情失败: {str(e)}")


@router.post("/cities/compare", summary="城市对比分析")
async def compare_cities(request: CityQueryRequest):
    """
    多城市对比分析
    """
    try:
        results = city_manager.compare_cities(
            request.city_codes,
            request.year,
            request.indicators
        )
        
        return {
            'success': True,
            'year': request.year,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"城市对比分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== 指标分析接口 ====================

@router.post("/indicators/analyze", summary="指标分析")
async def analyze_indicators(request: IndicatorAnalysisRequest):
    """
    指标趋势分析
    """
    try:
        from backend.analysis.indicator_registry import indicator_registry
        
        results = {
            'indicator_code': request.indicator_code,
            'cities': {},
            'summary': {}
        }
        
        for city_code in request.city_codes:
            city_data = city_manager.get_city_data(city_code)
            city_config = city_manager.get_city(city_code)
            
            if not city_config:
                continue
            
            # 筛选年份范围内的数据
            filtered_data = [
                d for d in city_data
                if request.start_year <= d.year <= request.end_year
            ]
            
            # 提取指标值
            indicator_values = []
            for data in filtered_data:
                if request.indicator_code in data.indicators:
                    indicator_values.append({
                        'year': data.year,
                        'value': data.indicators[request.indicator_code]
                    })
            
            results['cities'][city_code] = {
                'name': city_config.name,
                'data': indicator_values
            }
        
        return {
            'success': True,
            'analysis': results
        }
        
    except Exception as e:
        logger.error(f"指标分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/indicators/calculate", summary="自定义指标计算")
async def calculate_custom_indicator(request: CustomCalculationRequest):
    """
    自定义指标计算
    
    支持简单的算术表达式
    """
    try:
        import re
        import math
        
        # 安全计算：只允许基本的数学运算
        allowed_names = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'log': math.log,
            'exp': math.exp,
            'abs': abs,
            'round': round,
            'max': max,
            'min': min,
            'sum': sum,
        }
        
        # 验证公式安全性
        if re.search(r'[a-zA-Z_]\w*', request.formula):
            # 提取所有变量名
            formula_vars = set(re.findall(r'[a-zA-Z_]\w*', request.formula))
            # 排除函数名
            formula_vars -= set(allowed_names.keys())
            
            # 检查是否所有变量都有值
            missing_vars = formula_vars - set(request.variables.keys())
            if missing_vars:
                raise HTTPException(
                    status_code=400,
                    detail=f"缺少变量值: {', '.join(missing_vars)}"
                )
        
        # 安全地执行计算
        local_vars = request.variables.copy()
        local_vars.update(allowed_names)
        
        result = _safe_eval(request.formula, local_vars)
        
        return {
            'success': True,
            'formula': request.formula,
            'variables': request.variables,
            'result': result,
            'description': request.description or '自定义计算'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"指标计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== 场景管理接口 ====================

@router.post("/scenarios", summary="创建场景")
async def create_scenario(request: ScenarioCreateRequest):
    """
    创建分析场景
    """
    try:
        from backend.config.scenario_manager import scenario_manager
        
        scenario_id = scenario_manager.create_scenario(
            name=request.name,
            description=request.description,
            config=request.config,
            tags=request.tags or []
        )
        
        return {
            'success': True,
            'message': '场景创建成功',
            'scenario_id': scenario_id
        }
        
    except Exception as e:
        logger.error(f"创建场景失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/scenarios", summary="获取场景列表")
async def get_scenarios():
    """
    获取场景列表
    """
    try:
        from backend.config.scenario_manager import scenario_manager
        
        scenarios = scenario_manager.list_scenarios()
        
        return {
            'success': True,
            'total': len(scenarios),
            'scenarios': scenarios
        }
        
    except Exception as e:
        logger.error(f"获取场景列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/scenarios/{scenario_id}", summary="获取场景详情")
async def get_scenario_detail(scenario_id: str):
    """
    获取场景详情
    """
    try:
        from backend.config.scenario_manager import scenario_manager
        
        scenario = scenario_manager.get_scenario(scenario_id)
        
        if not scenario:
            raise HTTPException(status_code=404, detail=f"场景不存在: {scenario_id}")
        
        return {
            'success': True,
            'scenario': scenario
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取场景详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== 缓存管理接口 ====================

@router.post("/cache/clear", summary="清除缓存")
async def clear_cache(pattern: str = Query("*", description="缓存键模式")):
    """
    清除指定模式的缓存
    """
    try:
        count = cache_manager.clear_pattern(pattern)
        
        return {
            'success': True,
            'message': f'清除缓存 {count} 条',
            'count': count
        }
        
    except Exception as e:
        logger.error(f"清除缓存失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@router.get("/cache/stats", summary="获取缓存统计")
async def get_cache_stats():
    """
    获取缓存统计信息
    """
    try:
        # 简单的统计信息
        stats = {
            'backend_cache_available': cache_manager.redis_client is not None,
            'memory_cache_size': len(cache_manager.memory_cache) if hasattr(cache_manager, 'memory_cache') else 0
        }
        
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")
