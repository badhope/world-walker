"""多模型 fallback 链:首选失败时降级到下一项。"""

from unittest.mock import MagicMock, patch

import pytest

from backend.ai.config import AIConfig
from backend.ai.fallback import (
    DEFAULT_FALLBACK_CHAIN,
    FallbackError,
    FatalLLMError,
    ModelEntry,
    classify_error,
    run_with_fallback,
)


def _base_cfg() -> AIConfig:
    return AIConfig(
        default_backend="openai",
        active_backend="openai",
        model="qwen-max",
        temperature=0.3,
        max_tokens=100,
        timeout_sec=30,
        max_tool_rounds=3,
        available_backends=["openai"],
    )


def test_default_fallback_chain_has_five_models():
    assert len(DEFAULT_FALLBACK_CHAIN) == 5
    assert DEFAULT_FALLBACK_CHAIN[0].model == "qwen-max"
    assert all(e.backend == "openai" for e in DEFAULT_FALLBACK_CHAIN)


def test_classify_error_retryable():
    # Timeout / 429 / 5xx → retryable(降级)
    assert classify_error(Exception("connection timeout")) == "retryable"
    assert classify_error(Exception("429 rate limit exceeded")) == "retryable"
    assert classify_error(Exception("free tier exhausted")) == "retryable"


def test_classify_error_fatal():
    # 401 / 403 / 404 → fatal(立即抛)
    assert classify_error(Exception("401 unauthorized")) == "fatal"
    assert classify_error(Exception("403 forbidden")) == "fatal"
    assert classify_error(Exception("404 not found")) == "fatal"


def test_run_with_fallback_first_model_succeeds():
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    with patch("backend.ai.llm_client.litellm.completion", return_value=mock_resp) as m:
        resp, used = run_with_fallback(
            base_cfg=_base_cfg(),
            messages=[{"role": "user", "content": "hi"}],
            tools=None,
        )
        assert m.call_count == 1
        assert used.model == "qwen-max"
        assert used.priority == 0


def test_run_with_fallback_degrades_on_retryable_error():
    """首选超时 → 降级到第二项;第二项成功。"""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]

    call_count = {"n": 0}

    def fake_completion(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise Exception("connection timeout")
        return mock_resp

    with patch("backend.ai.llm_client.litellm.completion", side_effect=fake_completion) as m:
        resp, used = run_with_fallback(
            base_cfg=_base_cfg(),
            messages=[{"role": "user", "content": "hi"}],
            tools=None,
        )
        assert m.call_count == 2
        assert used.model == "qwen-long"  # 第二项
        assert used.priority == 1


def test_run_with_fallback_fatal_error_raises_immediately():
    """首选 401 → 立即抛 FatalLLMError,不降级。"""
    with patch("backend.ai.llm_client.litellm.completion", side_effect=Exception("401 unauthorized")):
        with pytest.raises(FatalLLMError):
            run_with_fallback(base_cfg=_base_cfg(), messages=[{"role": "user", "content": "hi"}], tools=None)


def test_run_with_fallback_chain_exhausted_raises():
    """链全失败 → 抛 FallbackError(链所有错误聚合)。"""
    with patch(
        "backend.ai.llm_client.litellm.completion",
        side_effect=Exception("connection timeout"),
    ):
        with pytest.raises(FallbackError) as exc_info:
            run_with_fallback(base_cfg=_base_cfg(), messages=[{"role": "user", "content": "hi"}], tools=None)
        # 异常信息含每项模型的错误
        msg = str(exc_info.value)
        assert "qwen-max" in msg
        assert "qwen-long" in msg


def test_run_with_fallback_custom_chain():
    """自定义 chain 跳过默认。"""
    custom = [ModelEntry("openai", "deepseek-v3", 0, "deepseek")]
    with patch("backend.ai.llm_client.litellm.completion", side_effect=Exception("timeout")):
        with pytest.raises(FallbackError) as exc_info:
            run_with_fallback(
                base_cfg=_base_cfg(),
                messages=[{"role": "user", "content": "hi"}],
                tools=None,
                chain=custom,
            )
        assert "deepseek-v3" in str(exc_info.value)


def test_run_with_fallback_works_without_env_vars(monkeypatch):
    """关键设计:run_with_fallback 不再依赖 env vars — 完全靠 base_cfg 跑。

    这保证 eval / 测试 / 多租户配置可在隔离环境跑(不需要 export LLM_OPENAI_API_KEY)。
    """
    # 清空所有 LLM env vars
    for k in ("LLM_OPENAI_API_KEY", "LLM_ANTHROPIC_API_KEY", "LLM_OLLAMA_BASE_URL"):
        monkeypatch.delenv(k, raising=False)

    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    with patch("backend.ai.llm_client.litellm.completion", return_value=mock_resp) as m:
        resp, used = run_with_fallback(
            base_cfg=_base_cfg(),
            messages=[{"role": "user", "content": "hi"}],
        )
        assert used.model == "qwen-max"
        assert m.call_count == 1
