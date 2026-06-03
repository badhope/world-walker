"""
真实数据分析 API 路由
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.analysis.real_data_analysis import real_data_analyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/real-data", tags=["真实数据分析"])


@router.get("/fetch", summary="获取宏观经济数据")
async def fetch_macro_data():
    """获取真实宏观经济数据"""
    try:
        df = real_data_analyzer.fetch_macro_data()

        # 转换为字典列表
        data_list = df.to_dict("records")

        return {"status": "success", "data": data_list, "count": len(data_list)}
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/eda", summary="执行探索性数据分析")
async def perform_eda():
    """执行探索性数据分析并返回结果"""
    try:
        df = real_data_analyzer.fetch_macro_data()
        eda_results = real_data_analyzer.perform_eda(df)

        return {"status": "success", "data": eda_results}
    except Exception as e:
        logger.error(f"EDA分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights", summary="生成数据洞察")
async def generate_insights():
    """Build data-driven insights from macro series and EDA."""
    try:
        df = real_data_analyzer.fetch_macro_data()
        eda_results = real_data_analyzer.perform_eda(df)
        insights = real_data_analyzer.generate_insights(eda_results)

        return {"status": "success", "data": insights}
    except Exception as e:
        logger.error(f"生成洞察失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualization", summary="获取可视化数据")
async def get_visualization_data():
    """获取图表可视化所需数据"""
    try:
        df = real_data_analyzer.fetch_macro_data()
        viz_data = real_data_analyzer.get_visualization_data(df)

        return {"status": "success", "data": viz_data}
    except Exception as e:
        logger.error(f"获取可视化数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/complete", summary="获取完整分析报告")
async def get_complete_analysis():
    """获取完整的分析报告，包含数据、EDA、洞察和可视化数据"""
    try:
        df = real_data_analyzer.fetch_macro_data()
        eda_results = real_data_analyzer.perform_eda(df)
        insights = real_data_analyzer.generate_insights(eda_results)
        viz_data = real_data_analyzer.get_visualization_data(df)

        return {
            "status": "success",
            "data": {
                "raw_data": df.to_dict("records"),
                "eda": eda_results,
                "insights": insights,
                "visualization": viz_data,
            },
        }
    except Exception as e:
        logger.error(f"获取完整分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
