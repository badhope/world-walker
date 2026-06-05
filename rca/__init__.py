"""rca — Python SDK for the Regional Economic Analysis agent.

Public API:
- 9 tool functions: forecast / diagnostics / backtest / risk / scenarios /
  monte_carlo / data_provenance / macro_data / list_cities
- chat() / chat_stream() — LLM agent
- RCAClient — 顶层类,聚合以上所有
- 错误: RCAError / ToolArgumentError / ToolNotFoundError / LLMUnavailableError

Usage:
    import rca
    rca.forecast(scope="city", name="shenzhen", indicator="gdp", years=3)
    rca.chat("session-1", "深圳 GDP 2026 多少?")

    client = rca.RCAClient()
    client.list_cities()
"""
from rca.chat import chat, chat_stream
from rca.client import RCAClient
from rca.errors import (
    LLMUnavailableError,
    RCAError,
    ToolArgumentError,
    ToolNotFoundError,
)
from rca.tools import (
    backtest,
    data_provenance,
    diagnostics,
    forecast,
    list_cities,
    macro_data,
    monte_carlo,
    risk,
    scenarios,
)

__all__ = [
    # Client
    "RCAClient",
    # Errors
    "RCAError",
    "ToolNotFoundError",
    "ToolArgumentError",
    "LLMUnavailableError",
    # Chat
    "chat",
    "chat_stream",
    # Tools (9)
    "forecast",
    "diagnostics",
    "backtest",
    "risk",
    "scenarios",
    "monte_carlo",
    "data_provenance",
    "macro_data",
    "list_cities",
]

__version__ = "9.1.0"
