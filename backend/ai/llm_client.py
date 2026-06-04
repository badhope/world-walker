"""
LLM 客户端 — LiteLLM 包装,统一 OpenAI / Anthropic / Ollama 接口。

设计:
- chat(cfg, messages, tools) → LLMResponse(同步)
- stream_chat(cfg, messages, tools) → Iterator[dict](SSE 用,本期暂不实现完整)
- 任何 litellm 异常包装为 LLMError
- 关键:litellm.drop_params = True → 不支持的参数自动忽略
- 模型名前缀: anthropic/* ollama/* (OpenAI 不用前缀)
"""
from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import litellm

from backend.ai.config import AIConfig

logger = logging.getLogger(__name__)

# 不支持的参数 litellm 自动 drop(避免某些 provider 不支持导致 400)
litellm.drop_params = True


class LLMError(Exception):
    """LLM 调用失败的统一包装(给上层 chat_service / API 路由捕获)。"""


@dataclass
class ToolCall:
    """单次 tool call — LLM 决定要调什么 + 参数。"""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """LLM 单次响应 — content + 可能的 tool_calls + token 用量。"""

    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = "stop"


def _model_name(cfg: AIConfig) -> str:
    """litellm 要求 anthropic/ollama 加前缀,openai 不加。"""
    if cfg.active_backend == "anthropic":
        return f"anthropic/{cfg.model}"
    if cfg.active_backend == "ollama":
        return f"ollama/{cfg.model}"
    return cfg.model  # openai / 其他


def _parse_tool_calls(raw: Any) -> list[ToolCall]:
    """litellm 返回的 tool_calls.arguments 是 JSON 字符串,需要 parse。"""
    out: list[ToolCall] = []
    for tc in raw or []:
        try:
            args_str = tc.function.arguments
            if isinstance(args_str, str):
                args = json.loads(args_str) if args_str.strip() else {}
            elif isinstance(args_str, dict):
                args = args_str
            else:
                args = {}
        except (json.JSONDecodeError, AttributeError, TypeError):
            logger.warning("Failed to parse tool call arguments: %r", args_str)
            args = {}
        out.append(
            ToolCall(
                id=getattr(tc, "id", "") or "",
                name=getattr(getattr(tc, "function", None), "name", "") or "",
                arguments=args,
            )
        )
    return out


def _build_kwargs(cfg: AIConfig, messages: list[dict], tools: list[dict] | None) -> dict:
    kwargs: dict[str, Any] = {
        "model": _model_name(cfg),
        "messages": messages,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "timeout": cfg.timeout_sec,
    }
    if tools:
        kwargs["tools"] = tools
    # ollama 需要 api_base(本地)
    if cfg.active_backend == "ollama":
        kwargs["api_base"] = os.getenv("LLM_OLLAMA_BASE_URL", "http://localhost:11434")
    # openai 兼容模式(百炼 / 自建 gateway)— 显式加前缀让 litellm 走 OpenAI client
    if cfg.active_backend == "openai":
        openai_base = os.getenv("LLM_OPENAI_BASE_URL")
        if openai_base:
            kwargs["api_base"] = openai_base
            kwargs["model"] = f"openai/{cfg.model}"
    return kwargs


def chat(
    cfg: AIConfig,
    messages: list[dict],
    tools: list[dict] | None = None,
) -> LLMResponse:
    """同步 chat — 给 LLM 发请求,返回 content / tool_calls。

    任何底层异常(网络/超时/认证/参数)统一包装为 LLMError。
    """
    try:
        kwargs = _build_kwargs(cfg, messages, tools)
        resp = litellm.completion(**kwargs)
    except Exception as e:
        logger.warning("LLM chat failed (backend=%s, model=%s): %s", cfg.active_backend, cfg.model, e)
        raise LLMError(f"{type(e).__name__}: {e}") from e

    if not getattr(resp, "choices", None):
        raise LLMError("LLM returned no choices")

    choice = resp.choices[0]
    msg = getattr(choice, "message", None)
    if msg is None:
        raise LLMError("LLM choice has no message")

    usage = getattr(resp, "usage", None)
    return LLMResponse(
        content=(getattr(msg, "content", None) or ""),
        tool_calls=_parse_tool_calls(getattr(msg, "tool_calls", None)),
        prompt_tokens=(getattr(usage, "prompt_tokens", 0) or 0) if usage else 0,
        completion_tokens=(getattr(usage, "completion_tokens", 0) or 0) if usage else 0,
        finish_reason=getattr(choice, "finish_reason", None) or "stop",
    )


def stream_chat(
    cfg: AIConfig,
    messages: list[dict],
    tools: list[dict] | None = None,
) -> Iterator[dict[str, Any]]:
    """真流式 chat — 调 litellm.completion(stream=True),yield 增量 token / done / error 事件。

    每个 yield 是 dict:
    - {"type": "token", "content": "..."} — 增量文本片段
    - {"type": "done", "finish_reason": "..."} — 最后一个 chunk(stream 完结标记)
    - {"type": "error", "message": "..."} — 任何底层错误,绝不抛异常给上层 SSE 消费者

    tool_calls 暂不在 stream 中处理(流式 + tool calling 各 provider 支持差异大),
    流式场景下用户先看思考过程 + 增量回答,tool 调用的批处理走 /chat 端点。
    """
    try:
        kwargs = _build_kwargs(cfg, messages, tools)
        kwargs["stream"] = True
        for chunk in litellm.completion(**kwargs):
            try:
                choice = chunk.choices[0]
                delta = getattr(choice, "delta", None)
                content = getattr(delta, "content", None) if delta else None
                finish_reason = getattr(choice, "finish_reason", None)
            except (AttributeError, IndexError):
                continue
            if content:
                yield {"type": "token", "content": content}
            if finish_reason:
                yield {"type": "done", "finish_reason": finish_reason}
    except Exception as e:
        logger.warning("LLM stream failed (backend=%s, model=%s): %s", cfg.active_backend, cfg.model, e)
        yield {"type": "error", "message": f"{type(e).__name__}: {e}"}
