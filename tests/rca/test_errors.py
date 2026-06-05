"""Tests for rca.errors — SDK 错误层次必须形成 R 树,统一 catch 顶层 RCAError。"""
import pytest

from rca.errors import (
    LLMUnavailableError,
    RCAError,
    ToolArgumentError,
    ToolNotFoundError,
)


def test_rca_error_is_base_for_all_subclasses():
    """所有 SDK 异常都应继承自 RCAError,以便用户用 except RCAError 统一捕获。"""
    for cls in (ToolNotFoundError, ToolArgumentError, LLMUnavailableError):
        assert issubclass(cls, RCAError)


def test_tool_not_found_error_preserves_tool_name():
    """ToolNotFoundError 含 tool 名,用户能定位错。"""
    err = ToolNotFoundError("get_foo")
    assert "get_foo" in str(err)
    assert isinstance(err, RCAError)


def test_tool_argument_error_preserves_detail():
    """ToolArgumentError 包装 tool_executor 的 {"error": "..."} message。"""
    err = ToolArgumentError("Missing required fields: ['name']")
    assert "Missing required fields" in str(err)
    assert "name" in str(err)
