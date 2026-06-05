"""多模型 fallback 链 — LLM 失败自动降级到下一项。

设计:
- DEFAULT_FALLBACK_CHAIN: 5 个模型(qwen-max → qwen-long → qwen-coder-turbo → deepseek-v3 → kimi-k2.5)
- 错误分类:fatal(401/403/404,立即抛) vs retryable(timeout/429/5xx,降级)
- run_with_fallback(): 循环 chain,成功立刻返;链全失败抛 FallbackError
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from backend.ai import llm_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelEntry:
    """fallback 链中的一项。"""
    backend: str      # "openai" / "anthropic" / "ollama"
    model: str        # LLM 模型名
    priority: int     # 0=首选,1=次选...
    label: str = ""   # 人读名(可选,默认 backend:model)

    def __str__(self) -> str:
        return self.label or f"{self.backend}:{self.model}"


# 来自 docs/AI_MODEL_REGISTRY.md 实测 25 个全功能模型,挑 5 个有代表性的
DEFAULT_FALLBACK_CHAIN: list[ModelEntry] = [
    ModelEntry("openai", "qwen-max",         0, "qwen-max (默认)"),
    ModelEntry("openai", "qwen-long",        1, "qwen-long (长文本)"),
    ModelEntry("openai", "qwen-coder-turbo", 2, "qwen-coder-turbo (代码)"),
    ModelEntry("openai", "deepseek-v3",      3, "deepseek-v3 (第三方)"),
    ModelEntry("openai", "kimi-k2.5",        4, "kimi-k2.5 (兜底)"),
]


# 错误分类
class LLMError(Exception):
    """LLM 通用错误。"""


class FatalLLMError(LLMError):
    """不可重试错误(401/403/404)— 立即抛,不降级。"""


class FallbackError(LLMError):
    """fallback 链全失败,聚合每项错误。"""


# 可重试的错误信号(子串匹配,小写)
_RETRYABLE_SIGNALS = ("timeout", "rate limit", "free tier", "exhausted",
                      "429", "500", "502", "503", "504", "connection")
_FATAL_SIGNALS = ("401", "unauthorized", "403", "forbidden", "404", "not found",
                  "invalid api key", "permission denied")


def classify_error(err: Exception) -> str:
    """根据错误信息分类:fatal / retryable。

    简单字符串匹配,生产可换成 litellm 异常类型判断。
    """
    msg = str(err).lower()
    for sig in _FATAL_SIGNALS:
        if sig in msg:
            return "fatal"
    return "retryable"  # 默认可重试,降级更安全


def _build_cfg_for_entry(base, entry: ModelEntry):
    """根据 ModelEntry 构造一个临时 AIConfig(继承 base 的连接/限制参数,只换 backend/model)。"""
    from backend.ai.config import AIConfig
    return AIConfig(
        default_backend=base.default_backend,
        active_backend=entry.backend,
        model=entry.model,
        temperature=base.temperature,
        max_tokens=base.max_tokens,
        timeout_sec=base.timeout_sec,
        max_tool_rounds=base.max_tool_rounds,
        available_backends=base.available_backends,
        tool_timeout_sec=base.tool_timeout_sec,
        parallel_max_workers=base.parallel_max_workers,
    )


def run_with_fallback(
    base_cfg: Any,                   # AIConfig — 必填,提供连接/限制参数(不再 reload env)
    messages: list[dict],
    tools: list[dict] | None = None,
    chain: list[ModelEntry] | None = None,
) -> tuple[Any, ModelEntry]:
    """循环 fallback 链,成功立刻返 (LLMResponse, ModelEntry);失败抛 FallbackError/FatalLLMError。

    base_cfg 提供:default_backend, available_backends, temperature, max_tokens,
                   timeout_sec, max_tool_rounds, tool_timeout_sec, parallel_max_workers。
    不读 env(由调用方负责初始化 base_cfg)。

    可重试错误(timeout/429/...)→ 降级下一项
    致命错误(401/403/404)→ 立即抛 FatalLLMError
    链全失败 → 抛 FallbackError(聚合所有错误)
    """
    chain = chain or DEFAULT_FALLBACK_CHAIN
    errors: list[str] = []

    for entry in chain:
        try:
            cfg = _build_cfg_for_entry(base_cfg, entry)
            resp = llm_client.chat(cfg, messages=messages, tools=tools)
            if entry != chain[0]:
                logger.info("fallback succeeded: %s", entry)
            return resp, entry
        except llm_client.LLMError as e:
            category = classify_error(e)
            err_str = f"{entry.model}: {type(e).__name__}: {e}"
            errors.append(err_str)
            logger.warning("fallback chain entry %s failed [%s]: %s", entry, category, e)
            if category == "fatal":
                raise FatalLLMError(f"致命错误,不降级: {err_str}") from e
            # retryable: 继续下一项
            continue
        except Exception as e:
            err_str = f"{entry.model}: {type(e).__name__}: {e}"
            errors.append(err_str)
            logger.warning("fallback chain entry %s unexpected error: %s", entry, e)
            continue

    raise FallbackError(f"fallback 链 {len(chain)} 项全失败:\n  " + "\n  ".join(errors))
