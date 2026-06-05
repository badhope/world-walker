"""多模型 fallback 链:首选失败时降级到下一项。"""

import pytest
from unittest.mock import patch, MagicMock
from backend.ai.fallback import (
    ModelEntry,
    DEFAULT_FALLBACK_CHAIN,
    FatalLLMError,
    FallbackError,
    run_with_fallback,
    classify_error,
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
            run_with_fallback(messages=[{"role": "user", "content": "hi"}], tools=None)


def test_run_with_fallback_chain_exhausted_raises():
    """链全失败 → 抛 FallbackError(链所有错误聚合)。"""
    with patch(
        "backend.ai.llm_client.litellm.completion",
        side_effect=Exception("connection timeout"),
    ):
        with pytest.raises(FallbackError) as exc_info:
            run_with_fallback(messages=[{"role": "user", "content": "hi"}], tools=None)
        # 异常信息含每项模型的错误
        msg = str(exc_info.value)
        assert "qwen-max" in msg
        assert "qwen-long" in msg


def test_run_with_fallback_custom_chain():
    """自定义 chain 跳过默认。"""
    custom = [ModelEntry("openai", "deepseek-v3", 0, "deepseek")]
    with patch("backend.ai.llm_client.litellm.completion", side_effect=Exception("timeout")):
        with pytest.raises(FallbackError) as exc_info:
            run_with_fallback(messages=[{"role": "user", "content": "hi"}], tools=None, chain=custom)
        assert "deepseek-v3" in str(exc_info.value)
