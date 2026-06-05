"""RCAClient — 顶层 SDK 入口,聚合 9 tools + chat + custom config。"""
from unittest.mock import MagicMock, patch

import pytest

from backend.ai.config import AIConfig
from rca.client import RCAClient


def _custom_cfg(model: str = "deepseek-v3") -> AIConfig:
    return AIConfig(
        default_backend="openai", active_backend="openai", model=model,
        temperature=0.5, max_tokens=1500, timeout_sec=45, max_tool_rounds=4,
        available_backends=["openai"],
    )


def test_rca_client_uses_custom_config():
    """RCAClient(config=cfg) → client._cfg is cfg。"""
    cfg = _custom_cfg()
    client = RCAClient(config=cfg)
    assert client._cfg is cfg


def test_rca_client_exposes_9_tools_as_methods():
    """client.forecast / diagnostics / ... / list_cities 全部存在。"""
    client = RCAClient(config=_custom_cfg())
    for name in ("forecast", "diagnostics", "backtest", "risk", "scenarios",
                 "monte_carlo", "data_provenance", "macro_data", "list_cities"):
        assert hasattr(client, name), f"missing method: {name}"
        assert callable(getattr(client, name))


def test_rca_client_methods_delegate_to_tools_module():
    """client.forecast(...) → rca.tools.forecast(...) — 委托不复制。"""
    client = RCAClient(config=_custom_cfg())
    with patch("rca.tools.forecast", return_value={"data": {"x": 1}, "navigate_to": None}) as m:
        result = client.forecast(scope="city", name="shenzhen", indicator="gdp", years=3)
    m.assert_called_once_with(scope="city", name="shenzhen", indicator="gdp", years=3)
    assert result == {"data": {"x": 1}, "navigate_to": None}


def test_rca_client_chat_delegates():
    """client.chat(...) → rca.chat.chat(...) — 委托不复制。"""
    client = RCAClient(config=_custom_cfg())
    with patch("rca.client._chat_fn", return_value={"content": "hi", "tool_rounds": 0}) as m:
        result = client.chat(session_id="s1", user_message="深圳 GDP")
    # 验证 session_id + user_message 传过去了(config/base_url 默认为 None)
    assert m.call_args.kwargs["session_id"] == "s1"
    assert m.call_args.kwargs["user_message"] == "深圳 GDP"
    assert result == {"content": "hi", "tool_rounds": 0}


def test_rca_public_api_reexports():
    """rca.* 直接 import 能用 — 9 tool + chat + chat_stream + RCAClient + errors。"""
    import rca
    from rca import (
        LLMUnavailableError,
        RCAClient,
        RCAError,
        ToolArgumentError,
        ToolNotFoundError,
        backtest,
        chat,
        chat_stream,
        data_provenance,
        diagnostics,
        forecast,
        list_cities,
        macro_data,
        monte_carlo,
        risk,
        scenarios,
    )
    assert rca.RCAClient is RCAClient
    assert rca.forecast is forecast
    assert rca.list_cities is list_cities
    assert rca.chat is chat
    assert rca.chat_stream is chat_stream
    # errors
    assert issubclass(ToolArgumentError, RCAError)
    assert issubclass(ToolNotFoundError, RCAError)
    assert issubclass(LLMUnavailableError, RCAError)


def test_rca_client_chat_uses_default_config():
    """client.chat(不传 config) → 用 self._cfg。"""
    cfg = _custom_cfg()
    client = RCAClient(config=cfg)
    with patch("rca.client._chat_fn", return_value={"content": "ok", "tool_rounds": 0}) as m:
        client.chat(session_id="s1", user_message="x")
    call = m.call_args
    assert call.kwargs["config"] is cfg  # default = self._cfg


def test_rca_client_chat_per_call_config_override():
    """client.chat(..., config=other_cfg) → 用 other_cfg 覆盖 self._cfg。"""
    client_cfg = _custom_cfg()
    other_cfg = _custom_cfg(model="different-model")
    client = RCAClient(config=client_cfg)
    with patch("rca.client._chat_fn", return_value={"content": "ok", "tool_rounds": 0}) as m:
        client.chat(session_id="s1", user_message="x", config=other_cfg)
    call = m.call_args
    assert call.kwargs["config"] is other_cfg
    assert call.kwargs["config"] is not client_cfg


def test_rca_client_chat_per_call_base_url_override():
    """client.chat(..., base_url='...') → 透传给 rca.chat()。"""
    client = RCAClient(config=_custom_cfg())
    with patch("rca.client._chat_fn", return_value={"content": "ok", "tool_rounds": 0}) as m:
        client.chat(session_id="s1", user_message="x", base_url="https://override.example.com/v1")
    call = m.call_args
    assert call.kwargs["base_url"] == "https://override.example.com/v1"
