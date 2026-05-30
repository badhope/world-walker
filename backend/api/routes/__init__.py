"""
路由模块
"""
from backend.api.routes.data import router as data_router
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.inference import router as inference_router
from backend.api.routes.interactive import router as interactive_router
from backend.api.routes.websocket import router as websocket_router
from backend.api.routes.cities import router as cities_router
from backend.api.routes.real_data import router as real_data_router

__all__ = ["data_router", "analysis_router", "inference_router", "interactive_router", "websocket_router", "cities_router", "real_data_router"]
