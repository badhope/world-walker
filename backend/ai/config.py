"""
LLM 配置 — 读 env,选定 backend,fallback 链。

设计:
- 单一入口 load_config() 返回 dataclass
- 默认 openai,无 key 尝试 anthropic,仍无则 ollama
- 全无 → 抛 ConfigError(API 层返 503)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """无可用 LLM backend。"""


@dataclass(frozen=True)
class AIConfig:
    default_backend: str
    active_backend: str
    model: str
    temperature: float
    max_tokens: int
    max_tool_rounds: int
    timeout_sec: int
    available_backends: list[str]


_BACKEND_DEFAULTS: dict[str, tuple[str, str]] = {
    "openai": ("gpt-4o-mini", "LLM_OPENAI_API_KEY"),
    "anthropic": ("claude-3-5-sonnet-20241022", "LLM_ANTHROPIC_API_KEY"),
    "ollama": ("qwen2.5:7b", "LLM_OLLAMA_BASE_URL"),
}

_BACKEND_ORDER = ["openai", "anthropic", "ollama"]


def _is_backend_available(backend: str) -> bool:
    """检查该 backend 是否有最低配置(API key / base URL)。"""
    if backend == "openai":
        return bool(os.getenv("LLM_OPENAI_API_KEY"))
    if backend == "anthropic":
        return bool(os.getenv("LLM_ANTHROPIC_API_KEY"))
    if backend == "ollama":
        return bool(os.getenv("LLM_OLLAMA_BASE_URL"))
    return False

def _model_for(backend: str) -> str:
    default, _ = _BACKEND_DEFAULTS[backend]
    env = {
        "openai": "LLM_OPENAI_MODEL",
        "anthropic": "LLM_ANTHROPIC_MODEL",
        "ollama": "LLM_OLLAMA_MODEL",
    }[backend]
    return os.getenv(env, default)


def load_config() -> AIConfig:
    default = os.getenv("LLM_DEFAULT_BACKEND", "openai").lower()
    if default not in _BACKEND_DEFAULTS:
        raise ConfigError(f"Unknown LLM_DEFAULT_BACKEND: {default}")

    available = [b for b in _BACKEND_ORDER if _is_backend_available(b)]
    if not available:
        raise ConfigError(
            "No LLM backend available. Configure one of: "
            "LLM_OPENAI_API_KEY, LLM_ANTHROPIC_API_KEY, LLM_OLLAMA_BASE_URL"
        )

    # 优先级:default 在 available 里就用,否则降级到第一个 available
    if default in available:
        active = default
    else:
        active = available[0]
        logger.warning(
            "LLM_DEFAULT_BACKEND=%s unavailable, falling back to %s",
            default, active,
        )

    return AIConfig(
        default_backend=default,
        active_backend=active,
        model=_model_for(active),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
        max_tool_rounds=int(os.getenv("LLM_MAX_TOOL_ROUNDS", "5")),
        timeout_sec=int(os.getenv("LLM_TIMEOUT_SEC", "60")),
        available_backends=available,
    )
