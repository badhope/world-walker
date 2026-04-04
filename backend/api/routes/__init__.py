from backend.api.routes.data import router as data_router
from backend.api.routes.inference import router as inference_router
from backend.api.routes.scrape import router as scrape_router

__all__ = ["data_router", "inference_router", "scrape_router"]
