"""SDK 内部 config loader — 从 env 读 + 填默认 fallback chain + 默认 tool/parallel 配置。

设计:
- 不读 env(由调用方负责初始化),此函数读 env
- 把 AIConfig 的 3 个 v8.0 字段(fallback_chain, tool_timeout_sec, parallel_max_workers)填好
- 找不到任何 backend key → ConfigError
"""
from __future__ import annotations

from backend.ai.config import AIConfig
from backend.ai.fallback import DEFAULT_FALLBACK_CHAIN
from rca.errors import ConfigError


def load_config() -> AIConfig:
    """从 env 构造 AIConfig。

    Returns:
        AIConfig with fallback_chain = DEFAULT_FALLBACK_CHAIN,
        tool_timeout_sec = 30, parallel_max_workers = 5,
        其他字段从 env 读(load_config() from backend.ai.config)。

    Raises:
        ConfigError: 找不到任何 LLM backend 的 env var。
    """
    try:
        from backend.ai.config import load_config as _backend_load
        cfg = _backend_load()
    except Exception as e:
        raise ConfigError(str(e)) from e

    # 补 v8.0 字段(backend load_config() 已经填了默认值,但确保不空)
    if not cfg.fallback_chain:
        cfg = AIConfig(
            default_backend=cfg.default_backend,
            active_backend=cfg.active_backend,
            model=cfg.model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            timeout_sec=cfg.timeout_sec,
            max_tool_rounds=cfg.max_tool_rounds,
            available_backends=cfg.available_backends,
            fallback_chain=tuple(DEFAULT_FALLBACK_CHAIN),
            tool_timeout_sec=cfg.tool_timeout_sec or 30,
            parallel_max_workers=cfg.parallel_max_workers or 5,
        )
    return cfg
