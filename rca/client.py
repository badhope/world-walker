"""RCAClient — SDK 顶层类,聚合 9 tools + chat + custom config。

设计:
- 默认 config: rca._config.load_config()(从 env 读)
- 传 config=... 可覆盖(适合多租户 / 多模型配置)
- 9 tool 方法纯委托给 rca.tools 模块(不重写)
- chat() / chat_stream() 委托给 rca.chat 模块
"""
from __future__ import annotations

from typing import Any, Iterator, Optional

from backend.ai.config import AIConfig

from rca import chat as _chat
from rca import tools as _tools
from rca._config import load_config
from rca.chat import chat as _chat_fn
from rca.chat import chat_stream as _chat_stream_fn


class RCAClient:
    """SDK 顶层入口。

    用法:
        client = RCAClient()  # 读 env
        client = RCAClient(config=my_cfg)  # 自定义 cfg

        client.forecast(scope="city", name="shenzhen", indicator="gdp")
        client.chat("session-1", "深圳 GDP 2026 多少?")
        for ev in client.chat_stream("session-1", "..."):
            ...
    """

    def __init__(self, config: Optional[AIConfig] = None):
        """构造。

        Args:
            config: 自定义 AIConfig(覆盖 env)。None = load_config()。
        """
        self._cfg = config if config is not None else load_config()

    # 9 tool — 纯委托
    def forecast(self, scope: str, name: str, indicator: str, years: int = 5) -> dict[str, Any]:
        return _tools.forecast(scope=scope, name=name, indicator=indicator, years=years)

    def diagnostics(self, scope: str, name: str, indicator: str) -> dict[str, Any]:
        return _tools.diagnostics(scope=scope, name=name, indicator=indicator)

    def backtest(self, scope: str, name: str, indicator: str) -> dict[str, Any]:
        return _tools.backtest(scope=scope, name=name, indicator=indicator)

    def risk(self, scope: str, name: str, indicator: str) -> dict[str, Any]:
        return _tools.risk(scope=scope, name=name, indicator=indicator)

    def scenarios(self, scope: str, name: str, indicator: str, years: int = 5) -> dict[str, Any]:
        return _tools.scenarios(scope=scope, name=name, indicator=indicator, years=years)

    def monte_carlo(self, scope: str, name: str, indicator: str, years: int = 5) -> dict[str, Any]:
        return _tools.monte_carlo(scope=scope, name=name, indicator=indicator, years=years)

    def data_provenance(self, name: str) -> dict[str, Any]:
        return _tools.data_provenance(name=name)

    def macro_data(self) -> dict[str, Any]:
        return _tools.macro_data()

    def list_cities(self) -> dict[str, Any]:
        return _tools.list_cities()

    # LLM agent
    def chat(self, session_id: str, user_message: str) -> dict[str, Any]:
        """单轮 LLM agent。"""
        return _chat_fn(session_id=session_id, user_message=user_message)

    def chat_stream(self, session_id: str, user_message: str) -> Iterator[dict[str, Any]]:
        """流式 LLM agent。"""
        return _chat_stream_fn(session_id=session_id, user_message=user_message)
