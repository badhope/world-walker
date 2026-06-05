"""SDK 错误层次。

设计:
- RCAError 是所有 SDK 异常的基类,用户 except RCAError: 一次捕完
- ToolNotFoundError — 调了不存在的 tool 名
- ToolArgumentError — tool 必填字段缺失 / 值非法
- LLMUnavailableError — fallback 链全失败
- ConfigError — SDK 配置错(无 API key 等)
"""
from __future__ import annotations


class RCAError(Exception):
    """SDK 顶层错误。所有 SDK 抛出的异常都继承自本类。"""


class ToolNotFoundError(RCAError):
    """Tool 名错 — 调了不在 _DISPATCH 里的 tool。

    Example:
        RCAClient().invoke("get_foo", {})
        # → ToolNotFoundError: Tool not found: get_foo
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool not found: {tool_name}")


class ToolArgumentError(RCAError):
    """Tool 参数错 — 必填字段缺失 / tool 内部返回 {"error": "..."}。

    Example:
        RCAClient().invoke("get_forecast", {})  # 缺 name / scope / indicator
        # → ToolArgumentError: Missing required fields: ['scope', 'name', 'indicator']
    """


class LLMUnavailableError(RCAError):
    """所有 LLM 都不可用 — fallback 链全失败。

    Example:
        RCAClient().chat(...)  # 网络挂 / 全 401
        # → LLMUnavailableError: fallback 链 5 项全失败: qwen-max: ..., deepseek-v3: ...
    """


class ConfigError(RCAError):
    """SDK config 错(无 API key / 后端不存在等)。"""
