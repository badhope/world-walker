"""
Urban Pulse — city economic data & analysis routes.
"""

from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.analysis_v3 import router as analysis_v3_router
from backend.api.routes.cities import router as cities_router
from backend.api.routes.cities_v2 import router as cities_v2_router
from backend.api.routes.data import router as data_router
from backend.api.routes.forecast import router as forecast_router
from backend.api.routes.static import router as static_router

__all__ = [
    "data_router",
    "analysis_router",
    "analysis_v3_router",
    "cities_router",
    "cities_v2_router",
    "forecast_router",
    "static_router",
]
