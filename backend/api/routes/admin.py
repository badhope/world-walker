"""Admin API routes — 8 endpoint + 9 tool dispatch + SSE chat。

设计:
- 全部 8 个 endpoint 挂 /api/v1/admin/*
- tool dispatch 用 rca.<func> 直接调(单一调用路径)
- 历史 ring buffer 1000 条
- AIConfig 热更新(用 ConfigStore)
- Chat stream 走 SSE(text/event-stream)
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, confloat, conint

from backend.api.admin_store import (
    QueryRecord,
    get_config_store,
    get_history,
    new_query_id,
)
from rca import tools as _rca_tools
from rca.chat import chat as _rca_chat
from rca.chat import chat_stream as _rca_chat_stream
from rca.errors import (
    LLMUnavailableError,
    RCAError,
    ToolArgumentError,
    ToolNotFoundError,
)

router = APIRouter(prefix="/admin", tags=["admin"])

# --------------------------------------------------------------------------- #
# 9 tool dispatch table — tool name → rca.<func> 字符串(每次查 module 拿
# 最新引用,让 monkeypatch.setattr 能生效)
# --------------------------------------------------------------------------- #

_TOOL_FUNC_NAMES = {
    "get_forecast": "forecast",
    "get_diagnostics": "diagnostics",
    "get_backtest": "backtest",
    "get_risk": "risk",
    "get_scenarios": "scenarios",
    "get_monte_carlo": "monte_carlo",
    "get_data_provenance": "data_provenance",
    "get_macro_data": "macro_data",
    "get_list_cities": "list_cities",
}


def _resolve_tool_func(tool_name: str):
    """tool 名 → rca.tools.<func> 当前引用(每次重查,支持 mock 替换)。"""
    fname = _TOOL_FUNC_NAMES.get(tool_name)
    if fname is None:
        return None
    return getattr(_rca_tools, fname, None)

# --------------------------------------------------------------------------- #
# 9 tool metadata(给前端 tools 页用)— name / label / description / params
# --------------------------------------------------------------------------- #

_TOOL_META = [
    {
        "name": "get_forecast",
        "label": "Forecast",
        "label_zh": "预测",
        "description": "多年 ensemble 预测(95% CI + diagnostics 摘要)",
        "params": {
            "scope": {"type": "select", "options": ["city", "province"], "default": "city"},
            "name": {"type": "text", "required": True, "placeholder": "shenzhen / guangdong"},
            "indicator": {"type": "text", "required": True, "placeholder": "gdp / population"},
            "years": {"type": "number", "default": 5, "min": 1, "max": 20},
        },
    },
    {
        "name": "get_diagnostics",
        "label": "Diagnostics",
        "label_zh": "诊断",
        "description": "5 项残差诊断(ADF/KPSS/Ljung-Box/Jarque-Bera/Breusch-Pagan) + verdict",
        "params": {
            "scope": {"type": "select", "options": ["city", "province"], "default": "city"},
            "name": {"type": "text", "required": True},
            "indicator": {"type": "text", "required": True},
        },
    },
    {
        "name": "get_backtest",
        "label": "Backtest",
        "label_zh": "回测",
        "description": "Walk-forward CV 5 指标(MAPE/RMSE/MASE/sMAPE/Coverage)",
        "params": {
            "scope": {"type": "select", "options": ["city", "province"], "default": "city"},
            "name": {"type": "text", "required": True},
            "indicator": {"type": "text", "required": True},
        },
    },
    {
        "name": "get_risk",
        "label": "Risk",
        "label_zh": "风险",
        "description": "VaR/CVaR 95/99 + GARCH(1,1) 条件波动率",
        "params": {
            "scope": {"type": "select", "options": ["city", "province"], "default": "city"},
            "name": {"type": "text", "required": True},
            "indicator": {"type": "text", "required": True},
        },
    },
    {
        "name": "get_scenarios",
        "label": "Scenarios",
        "label_zh": "情景",
        "description": "4 档情景:baseline/+10%/-10%/-25%",
        "params": {
            "scope": {"type": "select", "options": ["city", "province"], "default": "city"},
            "name": {"type": "text", "required": True},
            "indicator": {"type": "text", "required": True},
            "years": {"type": "number", "default": 5, "min": 1, "max": 20},
        },
    },
    {
        "name": "get_monte_carlo",
        "label": "Monte Carlo",
        "label_zh": "蒙特卡洛",
        "description": "1000 次模拟分位数(P5/P50/P95)",
        "params": {
            "scope": {"type": "select", "options": ["city", "province"], "default": "city"},
            "name": {"type": "text", "required": True},
            "indicator": {"type": "text", "required": True},
            "years": {"type": "number", "default": 5, "min": 1, "max": 20},
        },
    },
    {
        "name": "get_data_provenance",
        "label": "Data Provenance",
        "label_zh": "数据来源",
        "description": "数据血缘(URL/置信度/估算标记)",
        "params": {
            "name": {"type": "text", "required": True, "placeholder": "shenzhen"},
        },
    },
    {
        "name": "get_macro_data",
        "label": "Macro Data",
        "label_zh": "宏观数据",
        "description": "4 宏观协变量当前值 + 同比",
        "params": {},
    },
    {
        "name": "get_list_cities",
        "label": "List Cities",
        "label_zh": "城市列表",
        "description": "系统支持的所有城市和省份",
        "params": {},
    },
]

# --------------------------------------------------------------------------- #
# Request / response models
# --------------------------------------------------------------------------- #


class ConfigUpdateRequest(BaseModel):
    model: str | None = Field(default=None, description="LLM model name")
    base_url: str | None = Field(default=None, description="LLM gateway base URL")
    temperature: confloat(ge=0.0, le=2.0) | None = Field(default=None)
    max_tokens: conint(ge=64, le=32000) | None = Field(default=None)
    max_tool_rounds: conint(ge=1, le=20) | None = Field(default=None)
    timeout_sec: conint(ge=5, le=600) | None = Field(default=None)


class ChatRequest(BaseModel):
    session_id: str = Field(default="default", min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=8000)


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #


@router.get("/tools")
def list_tools() -> dict[str, Any]:
    """列出 9 tool 的 metadata(name / params / description)— 给前端表单生成用。"""
    return {"tools": _TOOL_META, "count": len(_TOOL_META)}


@router.post("/tools/{tool_name}/run")
def run_tool(
    tool_name: str = Path(..., description="tool 名, e.g. get_forecast"),
    payload: dict[str, Any] = ...,
) -> dict[str, Any]:
    """调一个 tool,返 data + duration + id(history 用)。"""
    func = _resolve_tool_func(tool_name)
    if func is None:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

    record_id = new_query_id()
    start = time.time()
    try:
        result = func(**payload)
        duration_ms = int((time.time() - start) * 1000)
        # 写 history
        get_history().add(QueryRecord(
            id=record_id,
            ts=time.time(),
            tool=tool_name,
            params=payload,
            result_summary=_summarize(tool_name, result),
            duration_ms=duration_ms,
            status="ok",
            error=None,
        ))
        return {
            "id": record_id,
            "tool": tool_name,
            "data": result.get("data", result) if isinstance(result, dict) else result,
            "duration_ms": duration_ms,
        }
    except ToolArgumentError as e:
        duration_ms = int((time.time() - start) * 1000)
        get_history().add(QueryRecord(
            id=record_id, ts=time.time(), tool=tool_name, params=payload,
            result_summary={}, duration_ms=duration_ms, status="error", error=str(e),
        ))
        raise HTTPException(status_code=400, detail=str(e))
    except ToolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RCAError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def list_history(
    tool: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=1000),
) -> dict[str, Any]:
    items = get_history().list(tool=tool, limit=limit)
    return {"items": items, "count": len(items)}


@router.get("/history/{record_id}")
def get_history_record(record_id: str) -> dict[str, Any]:
    rec = get_history().get(record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="record not found")
    return rec


@router.delete("/history")
def clear_history() -> dict[str, str]:
    get_history().clear()
    return {"status": "cleared"}


@router.get("/config")
def get_config() -> dict[str, Any]:
    cfg = get_config_store().get()
    return {
        "model": cfg.model,
        "default_backend": cfg.default_backend,
        "active_backend": cfg.active_backend,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "max_tool_rounds": cfg.max_tool_rounds,
        "timeout_sec": cfg.timeout_sec,
        "available_backends": list(cfg.available_backends),
        "fallback_chain": list(cfg.fallback_chain),
    }


@router.put("/config")
def update_config(body: ConfigUpdateRequest) -> dict[str, Any]:
    new_cfg = get_config_store().update(
        model=body.model,
        base_url=body.base_url,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        max_tool_rounds=body.max_tool_rounds,
        timeout_sec=body.timeout_sec,
    )
    return {
        "model": new_cfg.model,
        "default_backend": new_cfg.default_backend,
        "temperature": new_cfg.temperature,
        "max_tokens": new_cfg.max_tokens,
        "max_tool_rounds": new_cfg.max_tool_rounds,
        "status": "updated",
    }


@router.post("/chat")
def chat(body: ChatRequest) -> dict[str, Any]:
    """non-stream chat — 调一次 rca.chat,返 final answer。"""
    cfg = get_config_store().get()
    record_id = new_query_id()
    start = time.time()
    try:
        result = _rca_chat(
            session_id=body.session_id,
            user_message=body.message,
            config=cfg,
        )
        duration_ms = int((time.time() - start) * 1000)
        get_history().add(QueryRecord(
            id=record_id, ts=time.time(), tool="chat",
            params={"session_id": body.session_id, "message": body.message},
            result_summary={"content_preview": result.get("content", "")[:200]},
            duration_ms=duration_ms, status="ok", error=None,
        ))
        return {"id": record_id, **result}
    except LLMUnavailableError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except RCAError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/stream")
def chat_stream(
    session_id: str = Query("default", min_length=1, max_length=128),
    message: str = Query(..., min_length=1, max_length=8000),
) -> StreamingResponse:
    """SSE 流式 chat — 调 rca.chat_stream,yield 每个 event。"""

    async def event_gen():
        cfg = get_config_store().get()
        gen = _rca_chat_stream(session_id=session_id, user_message=message, config=cfg)
        for ev in gen:
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            # 给客户端一点时间 flush(提升打字机体感)
            await asyncio.sleep(0)
        # 终态 marker
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 关 nginx buffer
        },
    )


# --------------------------------------------------------------------------- #
# 工具函数
# --------------------------------------------------------------------------- #


def _summarize(tool_name: str, result: Any) -> dict[str, Any]:
    """只存 result 摘要,防 history 膨胀(forecast 不存整个 ensemble 数组)。"""
    if not isinstance(result, dict):
        return {"_type": type(result).__name__}
    data = result.get("data", result)
    if not isinstance(data, dict):
        return {"_type": type(data).__name__}
    summary: dict[str, Any] = {}
    if tool_name == "get_forecast" and "ensemble" in data:
        ens = data["ensemble"]
        preds = ens.get("predictions", [])
        summary["pred_first"] = preds[0] if preds else None
        summary["pred_last"] = preds[-1] if preds else None
        summary["n_years"] = len(preds)
        summary["verdict"] = data.get("diagnostics_verdict")
    elif tool_name == "get_diagnostics" and "verdict" in data:
        summary["verdict"] = data["verdict"]
    elif tool_name == "get_backtest" and "metrics" in data:
        m = data["metrics"]
        summary["mape"] = m.get("mape")
    elif tool_name == "get_risk" and "var_95" in data:
        summary["var_95_pct"] = data["var_95"].get("var_pct")
    elif tool_name == "get_list_cities" and "n_cities" in data:
        summary["n_cities"] = data["n_cities"]
    elif tool_name == "get_macro_data":
        summary["keys"] = list(data.keys())[:4]
    else:
        summary["keys"] = list(data.keys())[:5]
    return summary
