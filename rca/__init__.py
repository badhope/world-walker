"""rca — Python SDK for the Regional Economic Analysis agent.

Public API: 9 tool functions + chat() + chat_stream() + RCAClient.
"""
from rca.errors import (
    LLMUnavailableError,
    RCAError,
    ToolArgumentError,
    ToolNotFoundError,
)

__all__ = [
    "RCAClient",
    "RCAError",
    "ToolNotFoundError",
    "ToolArgumentError",
    "LLMUnavailableError",
    "chat",
    "chat_stream",
    "data_provenance",
    "diagnostics",
    "forecast",
    "list_cities",
    "macro_data",
    "monte_carlo",
    "risk",
    "scenarios",
    "backtest",
]
