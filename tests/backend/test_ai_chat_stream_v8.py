"""v8.0 chat_stream_with_trace 端到端 SSE 事件链测试。

mock LLM + tool,验证:
- fallback 降级事件
- parallel tool_call 事件
- retry hint 事件
- trace 出现在 done 事件中
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.ai import chat_service
from backend.ai.config import AIConfig
from backend.ai.llm_client import LLMResponse, ToolCall
from backend.ai.fallback import ModelEntry


def _cfg():
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


def _tool_resp(tc_id: str, name: str, args: dict) -> LLMResponse:
    tc = ToolCall(id=tc_id, name=name, arguments=args)
    return LLMResponse(content="", tool_calls=[tc], prompt_tokens=10, completion_tokens=5, finish_reason="tool_calls")


def _final_resp(content: str) -> LLMResponse:
    return LLMResponse(content=content, tool_calls=[], prompt_tokens=10, completion_tokens=5, finish_reason="stop")


def test_stream_emits_thinking_tool_call_token_done():
    """正常流程:thinking → tool_call → token → done,trace 在 done 事件中。"""
    with patch.object(chat_service.llm_client, "chat", side_effect=[
        _tool_resp("1", "get_forecast", {"scope": "city", "name": "shenzhen"}),
        _final_resp("深圳 2026 GDP 预测 4.42 万亿。"),
    ]) as m:
        events = list(chat_service.chat_stream_with_trace(_cfg(), "s1", "深圳 GDP 2026?"))

    types = [e["type"] for e in events]
    assert types[0] == "thinking"
    assert "tool_call" in types
    assert "token" in types
    assert types[-1] == "done"
    # trace 在 done 中
    done_evt = events[-1]
    assert "trace" in done_evt
    assert len(done_evt["trace"]) >= 2  # 至少 llm_call + tool_call


def test_stream_parallel_tool_calls():
    """LLM 一次返 2 个 tool_call,都被执行。"""
    with patch.object(chat_service.llm_client, "chat", side_effect=[
        # 一次 LLM 返 2 个 tool
        LLMResponse(
            content="",
            tool_calls=[
                ToolCall(id="1", name="get_macro_data", arguments={"indicator": "gdp"}),
                ToolCall(id="2", name="list_cities", arguments={}),
            ],
            prompt_tokens=10, completion_tokens=5, finish_reason="tool_calls"
        ),
        _final_resp("GDP 数据见上。"),
    ]):
        events = list(chat_service.chat_stream_with_trace(_cfg(), "s2", "GDP + 城市列表"))

    tool_events = [e for e in events if e["type"] == "tool_call"]
    assert len(tool_events) == 2
    names = {e["name"] for e in tool_events}
    assert "get_macro_data" in names
    assert "list_cities" in names


def test_stream_fallback_emits_error_when_all_models_fail():
    """fallback 链全失败时,emit error 事件含 trace。"""
    with patch(
        "backend.ai.fallback.llm_client.chat",
        side_effect=Exception("connection timeout"),
    ):
        events = list(chat_service.chat_stream_with_trace(_cfg(), "s3", "失败场景"))

    # 第一个事件是 thinking,最后一个是 error
    assert events[0]["type"] == "thinking"
    error_evt = [e for e in events if e["type"] == "error"]
    assert len(error_evt) == 1
    assert "trace" in error_evt[0]


def test_stream_retry_hint_on_retryable_error():
    """tool 返 city_not_found 时,下一轮 messages 含 retry hint(从 _build_messages 间接验证)。"""
    # 用 get_data_provenance 模拟可重试失败
    with patch.object(chat_service.llm_client, "chat", side_effect=[
        _tool_resp("1", "get_data_provenance", {"name": "invalid_city"}),
        _final_resp("已用正确城市重试。"),
    ]) as m:
        events = list(chat_service.chat_stream_with_trace(_cfg(), "s4", "深圳数据来源"))

    # 验证第二次 LLM call 收到了含 hint 的 messages
    assert m.call_count == 2
    second_call_messages = m.call_args_list[1].kwargs["messages"]
    # 验证 hint 在 messages 里
    hint_found = any(
        msg.get("role") == "user" and "系统提示" in str(msg.get("content", ""))
        for msg in second_call_messages
    )
    assert hint_found
