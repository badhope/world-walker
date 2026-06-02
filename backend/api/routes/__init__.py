"""
路由模块
"""
from backend.api.routes.data import router as data_router
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.inference import router as inference_router
from backend.api.routes.interactive import router as interactive_router
from backend.api.routes.websocket import router as websocket_router
from backend.api.routes.cities import router as cities_router
from backend.api.routes.cities_v2 import router as cities_v2_router
from backend.api.routes.forecast import router as forecast_router
from backend.api.routes.analysis_v3 import router as analysis_v3_router
from backend.api.routes.real_data import router as real_data_router
from backend.api.routes.database import router as database_router
from backend.api.routes.static import router as static_router
from backend.api.routes.ml import router as ml_router

__all__ = [
    "data_router", "analysis_router", "inference_router",
    "interactive_router", "websocket_router",
    "cities_router", "cities_v2_router",
    "forecast_router", "analysis_v3_router",
    "real_data_router", "database_router", "static_router",
    "ml_router",
]
