"""
指标推演 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
from functools import lru_cache

from backend.models.schemas import (
    InferenceRequest, InferenceResponse,
    BatchInferenceRequest
)
from backend.analysis.economic_models import inference_engine, economic_models

router = APIRouter(prefix="/inference", tags=["指标推演"])


@router.post("/calculate", response_model=InferenceResponse, summary="单指标推演")
def calculate_indicator(request: InferenceRequest):
    """
    推演单个经济指标
    
    基于经济学公式或统计模型，从已知指标推算目标指标。
    
    支持的推演方法:
    - linear: 线性推演（公式计算）
    - monte_carlo: 蒙特卡洛模拟
    """
    try:
        result = inference_engine.calculate(
            target=request.target_indicator,
            inputs=request.input_indicators,
            method=request.method.value,
            confidence_level=request.confidence_level
        )
        
        return InferenceResponse(
            predicted_value=result.value,
            predicted_unit=result.unit,
            confidence_interval=result.confidence_interval,
            method_used=result.method,
            r_squared=result.r_squared,
            input_indicators=request.input_indicators,
            target_indicator=request.target_indicator
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/available", summary="获取可推演指标列表")
@lru_cache(maxsize=1)
def list_available_indicators():
    """获取所有可推演的指标及其要求"""
    return inference_engine.list_available_indicators()


@router.post("/infer_all", summary="推演所有可计算指标")
def infer_all_indicators(request: Dict[str, float]):
    """
    根据输入的指标，自动推演所有可计算的指标
    
    输入任意已知指标，系统将自动识别并计算所有可推演的目标指标。
    """
    return inference_engine.infer_all(request)


@router.post("/batch", summary="批量推演")
def batch_calculate(request: BatchInferenceRequest):
    """批量推演多个指标"""
    results = []
    
    for item in request.items:
        try:
            result = inference_engine.calculate(
                target=item.target_indicator,
                inputs=item.input_indicators,
                method=item.method.value
            )
            results.append({
                "target": item.target_indicator,
                "status": "success",
                "value": result.value,
                "unit": result.unit,
                "confidence_interval": result.confidence_interval
            })
        except Exception as e:
            results.append({
                "target": item.target_indicator,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total": len(request.items),
        "success": sum(1 for r in results if r["status"] == "success"),
        "results": results
    }


# ==================== 经济学模型 ====================

@router.get("/models/phillips", summary="菲利普斯曲线")
def phillips_curve(
    unemployment: float,
    natural_unemployment: float = 5.0,
    expected_inflation: float = 2.0,
    beta: float = 0.5
):
    """
    菲利普斯曲线模型
    
    公式: π = πₑ - β(u - u*)
    
    描述失业率与通胀率之间的短期替代关系。
    """
    return economic_models.phillips_curve(unemployment, natural_unemployment, expected_inflation, beta)


@router.get("/models/okun", summary="奥肯定律")
def okun_law(
    gdp_growth: float,
    potential_growth: float = 6.0,
    okun_coefficient: float = 2.0
):
    """
    奥肯定律模型
    
    公式: (Y - Y*)/Y* = -β(u - u*)
    
    描述GDP增速与失业率变化的关系。
    """
    return economic_models.okun_law(gdp_growth, potential_growth, okun_coefficient)


@router.get("/models/cobb_douglas", summary="柯布-道格拉斯生产函数")
def cobb_douglas(
    capital: float,
    labor: float,
    alpha: float = 0.3,
    technology: float = 1.0
):
    """
    柯布-道格拉斯生产函数
    
    公式: Y = A × K^α × L^(1-α)
    
    描述产出与资本、劳动投入的关系。
    """
    return economic_models.cobb_douglas(capital, labor, alpha, technology)


@router.get("/models/solow", summary="索洛增长模型")
def solow_growth(
    savings_rate: float,
    population_growth: float,
    depreciation: float,
    alpha: float = 0.3,
    technology: float = 1.0
):
    """
    索洛增长模型
    
    计算稳态人均资本和人均产出。
    """
    return economic_models.solow_growth(savings_rate, population_growth, depreciation, alpha, technology)
