"""
路由模块
"""
from backend.api.routes.data import router as data_router
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.inference import router as inference_router

__all__ = ["data_router", "analysis_router", "inference_router"]
