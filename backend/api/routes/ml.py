"""
AutoML API route.

Exposes the previously un-wired `backend.ml.AutoML` module as a
real HTTP endpoint. This is what makes the ML module discoverable
and useful — without this router, `backend/ml/` would be a tested
but unused module.

Endpoints:
  GET  /api/v1/ml/models         — list all available algorithms
  POST /api/v1/ml/train          — train a single model on user data
  POST /api/v1/ml/automl         — auto-select and tune the best model
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.ml import (
    AutoML,
    ModelTrainer,
    TrainingConfig,
    get_available_models,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["ml"])


# ============================================
# Request / Response schemas
# ============================================
class TrainRequest(BaseModel):
    """Training data and config."""
    data: List[Dict[str, Any]] = Field(
        ..., description="Training rows as list of dicts (records)",
    )
    target_column: str = Field(..., description="Name of the target column")
    feature_columns: Optional[List[str]] = Field(
        default=None, description="Optional list of feature columns; defaults to all non-target",
    )
    model_name: str = Field(
        default="random_forest", description="One of get_available_models()",
    )
    test_size: float = Field(default=0.2, ge=0.05, le=0.5)


class AutoMLRequest(BaseModel):
    """AutoML request."""
    data: List[Dict[str, Any]] = Field(..., description="Training rows as records")
    target_column: str = Field(..., description="Name of the target column")
    feature_columns: Optional[List[str]] = Field(default=None)
    candidate_models: Optional[List[str]] = Field(
        default=None, description="Subset of models to consider; defaults to all",
    )
    metric: str = Field(default="r2", description="r2 | neg_mae | neg_rmse")


# ============================================
# Endpoints
# ============================================
@router.get("/models", summary="List available ML models")
async def list_models() -> Dict[str, Any]:
    """Return the catalogue of training algorithms."""
    return {
        "models": get_available_models(),
        "count": len(get_available_models()),
    }


@router.post("/train", summary="Train a single model")
async def train(req: TrainRequest) -> Dict[str, Any]:
    """Train the requested algorithm and return metrics."""
    if not req.data:
        raise HTTPException(status_code=400, detail="`data` must be non-empty")
    if req.target_column not in req.data[0]:
        raise HTTPException(
            status_code=400,
            detail=f"`target_column` {req.target_column!r} not present in data",
        )

    feature_columns = req.feature_columns or [
        k for k in req.data[0].keys() if k != req.target_column
    ]

    try:
        # Write to a temp dir so the canonical models/ directory is not polluted
        import tempfile
        with tempfile.TemporaryDirectory(prefix="ml_train_") as tmpdir:
            cfg = TrainingConfig(
                model_names=[req.model_name],
                target_column=req.target_column,
                feature_columns=feature_columns,
                test_size=req.test_size,
                save_models=False,
                model_output_dir=tmpdir,
            )
            import pandas as pd
            df = pd.DataFrame(req.data)
            trainer = ModelTrainer(cfg)
            trainer.prepare_data(df)
            all_results = trainer.train_all_models().all_results or []
        # Find the requested model's metrics
        chosen = next(
            (r for r in all_results if getattr(r, "model_name", None) == req.model_name),
            all_results[0] if all_results else None,
        )
        metrics_obj = getattr(chosen, "metrics", None) if chosen else None
        metrics_dict = {
            "r2": getattr(metrics_obj, "r2", None) if metrics_obj else None,
            "mae": getattr(metrics_obj, "mae", None) if metrics_obj else None,
            "rmse": getattr(metrics_obj, "rmse", None) if metrics_obj else None,
        }
    except Exception as exc:  # pragma: no cover — re-raised via HTTP
        logger.exception("Training failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Training failed: {exc}") from exc

    return {
        "model": req.model_name,
        "metrics": metrics_dict,
        "feature_columns": feature_columns,
        "rows": len(req.data),
    }


@router.post("/automl", summary="Auto-select and tune the best model")
async def automl(req: AutoMLRequest) -> Dict[str, Any]:
    """Run AutoML on the dataset and return the leaderboard."""
    if not req.data:
        raise HTTPException(status_code=400, detail="`data` must be non-empty")

    feature_columns = req.feature_columns or [
        k for k in req.data[0].keys() if k != req.target_column
    ]

    try:
        aml = AutoML(
            target_column=req.target_column,
            feature_columns=feature_columns,
            model_names=req.candidate_models,
            scoring=req.metric,
        )
        import pandas as pd
        df = pd.DataFrame(req.data)
        result = aml.fit(df)
        # Build a leaderboard from all_results
        leaderboard = []
        for r in (result.all_results or []):
            entry = {"model": getattr(r, "model_name", "?")}
            metrics = getattr(r, "metrics", None)
            if metrics is not None:
                entry["metrics"] = {
                    "r2": getattr(metrics, "r2", None),
                    "mae": getattr(metrics, "mae", None),
                    "rmse": getattr(metrics, "rmse", None),
                }
            leaderboard.append(entry)
    except Exception as exc:  # pragma: no cover
        logger.exception("AutoML failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AutoML failed: {exc}") from exc

    return {
        "metric": req.metric,
        "leaderboard": leaderboard,
        "rows": len(req.data),
    }


__all__ = ["router"]
