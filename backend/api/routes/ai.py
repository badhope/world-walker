"""
AI 路由 — /api/v1/ai/chat, /chat/stream, /tools, /config。

设计:
- /chat 一次性返回(简单,test 友好)
- /chat/stream SSE 流式(浏览器友好)
- /tools + /config 静态
- 输入校验:session_id 长度,message 长度,频率限制(轻量)
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.ai import chat_service
from backend.ai.config import load_config
from backend.ai.tool_registry import TOOLS, list_tool_names

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., max_length=4000)


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=50)


# --------------------------------------------------------------------------- #
# 限频(简单滑动窗口,内存)
# --------------------------------------------------------------------------- #

_rate_store: dict[str, list[float]] = {}
_RATE_LIMIT = 10  # msg per minute per session
_RATE_WINDOW = 60  # sec


def _check_rate(session_id: str) -> None:
    now = time.time()
    if session_id not in _rate_store:
        _rate_store[session_id] = []
    recent = [t for t in _rate_store[session_id] if now - t < _RATE_WINDOW]
    if len(recent) >= _RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many messages, slow down")
    _rate_store[session_id] = recent + [now]


# --------------------------------------------------------------------------- #
# 路由
# --------------------------------------------------------------------------- #


@router.get("/config")
def get_config():
    try:
        cfg = load_config()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {
        "default_backend": cfg.default_backend,
        "active_backend": cfg.active_backend,
        "model": cfg.model,
        "available_backends": cfg.available_backends,
        "max_tool_rounds": cfg.max_tool_rounds,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
    }


@router.get("/tools")
def get_tools():
    return {
        "tools": TOOLS,
        "count": len(TOOLS),
        "names": list_tool_names(),
    }


@router.post("/chat")
def post_chat(req: ChatRequest):
    _check_rate(req.session_id)
    # 取最后一条 user message
    user_msgs = [m for m in req.messages if m.role == "user"]
    if not user_msgs:
        raise HTTPException(status_code=400, detail="No user message in request")
    user_message = user_msgs[-1].content
    try:
        cfg = load_config()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI config error: {e}")
    result = chat_service.chat(cfg, session_id=req.session_id, user_message=user_message)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@router.post("/chat/stream")
def post_chat_stream(req: ChatRequest):
    """SSE 流式 — 当前实现是非流式 chat 包装成 SSE event,简化版。

    真正的流式需要改造 chat_service 用 stream_chat + 增量工具调用,
    后续可加(本 task 先确保非流式工作)。
    """
    _check_rate(req.session_id)
    user_msgs = [m for m in req.messages if m.role == "user"]
    if not user_msgs:
        raise HTTPException(status_code=400, detail="No user message")
    user_message = user_msgs[-1].content

    def event_gen() -> Any:
        try:
            cfg = load_config()
            yield f"event: message\ndata: {json.dumps({'type': 'thinking'})}\n\n"
            result = chat_service.chat(cfg, session_id=req.session_id, user_message=user_message)
            # 拆 content 为 token(粗粒度,按字符流)
            content = result.get("content", "")
            for i in range(0, len(content), 4):
                yield f"event: message\ndata: {json.dumps({'type': 'token', 'content': content[i:i+4]})}\n\n"
            yield f"event: message\ndata: {json.dumps({'type': 'done', 'tool_rounds': result.get('tool_rounds', 0)})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")
