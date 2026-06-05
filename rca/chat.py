"""SDK chat + chat_stream — 包装 backend.ai.chat_service,错误统一为 LLMUnavailableError。

设计:
- 模块级函数 chat() / chat_stream() — 不需要 RCAClient
- 内部懒加载 cfg(第一次调用时 load,后续复用)
- 任何 LLMError/FallbackError → LLMUnavailableError
- 返回值与 backend chat_service 100% 一致(不动结构)
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from backend.ai import chat_service as _chat_service
from backend.ai.fallback import FallbackError, FatalLLMError
from backend.ai.llm_client import LLMError
from rca._config import load_config
from rca.errors import LLMUnavailableError

_cached_cfg = None


def _get_cfg():
    """懒加载 cfg(第一次调时 load,后续复用同一对象)。"""
    global _cached_cfg
    if _cached_cfg is None:
        _cached_cfg = load_config()
    return _cached_cfg


def chat(session_id: str, user_message: str) -> dict[str, Any]:
    """单轮 LLM agent — 调一次 LLM,允许多 tool round,返 final 答案。

    Args:
        session_id: 客户端会话 ID(用于 conversation store)
        user_message: 用户自然语言问题

    Returns:
        {"content": "...", "tool_rounds": N, "tool_calls": [...], "prompt_tokens": N, ...}

    Raises:
        LLMUnavailableError: 所有 LLM 都不可用
        RCAError: 其他 LLM 错(配置错 / 模型不存在 等)
    """
    try:
        return _chat_service.chat(_get_cfg(), session_id, user_message)
    except (FallbackError, FatalLLMError, LLMError) as e:
        raise LLMUnavailableError(str(e)) from e


def chat_stream(session_id: str, user_message: str) -> Iterator[dict[str, Any]]:
    """流式 LLM agent — yield 事件 dict,事件类型:
    - {"type": "thinking"}                          启动
    - {"type": "tool_call", "name", "args", ...}    一次 tool dispatch
    - {"type": "token", "content": "..."}           文本片段
    - {"type": "done", "finish_reason", "trace":[]} 结束(含 trace)
    - {"type": "error", "message", "trace":[]}      失败

    Yields:
        事件 dict
    """
    try:
        gen = _chat_service.chat_stream_with_trace(_get_cfg(), session_id, user_message)
        yield from gen
    except (FallbackError, FatalLLMError, LLMError) as e:
        # 不能 raise(generator 半路抛会断流);改 yield error event
        yield {"type": "error", "message": str(e), "trace": []}
