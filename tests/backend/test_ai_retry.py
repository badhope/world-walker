"""反射重试:tool 失败时,构造 hint 消息让 LLM 改参数重试。"""

import pytest

from backend.ai.retry import (
    RETRYABLE_TOOL_ERRORS,
    build_retry_hint,
    should_retry,
)


def test_retryable_set_contains_expected_errors():
    """白名单至少含 city_not_found / data_unavailable / missing_required_fields。"""
    assert "city_not_found" in RETRYABLE_TOOL_ERRORS
    assert "data_unavailable" in RETRYABLE_TOOL_ERRORS
    assert "missing_required_fields" in RETRYABLE_TOOL_ERRORS


def test_should_retry_true_for_retryable_error():
    result = {"error": "city_not_found", "navigate_to": None}
    assert should_retry(result) is True


def test_should_retry_false_for_non_retryable_error():
    result = {"error": "internal_server_error", "navigate_to": None}
    assert should_retry(result) is False


def test_should_retry_false_for_success_result():
    result = {"data": {"ok": True}, "navigate_to": "/x"}
    assert should_retry(result) is False


def test_build_retry_hint_contains_tool_name_and_args():
    hint = build_retry_hint("get_forecast", {"name": "shenzhenx"}, "city_not_found")
    assert "get_forecast" in hint
    assert "shenzhenx" in hint
    assert "city_not_found" in hint


def test_build_retry_hint_contains_suggestion():
    """hint 应含改参数的建议(让 LLM 知道做什么)。"""
    hint = build_retry_hint("get_forecast", {"name": "shenzhenx"}, "city_not_found")
    # 含 '请' 或 '建议' 或 '用' 之类引导词
    assert any(kw in hint for kw in ["请", "建议", "用", "改", "Try", "use", "check"])
