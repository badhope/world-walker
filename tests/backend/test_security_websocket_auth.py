"""
安全回归测试:WebSocket 身份认证 (H-01)

防御 websocket 端点接受客户端自报的 user_id / 任意广播 / 任意私发。
"""

import pytest


@pytest.mark.unit
class TestWebSocketAuthResolver:
    """websocket 端点应只信任通过 token 解析出的 user_id,绝不信任客户端自报。"""

    def test_resolve_user_with_valid_token(self, monkeypatch):
        """提供合法 token 时,从 token 中提取 user_id。"""
        from backend.api.auth import create_access_token
        from backend.api.routes import websocket as ws_module

        real_token = create_access_token({"sub": "alice"})

        resolved = ws_module.resolve_websocket_user(
            token=real_token,
            client_user_id="evil-impersonator",
        )
        assert resolved == "alice", f"token-derived user must win, got {resolved!r}"

    def test_resolve_user_without_token_returns_none(self):
        """无 token 时返回 None,不允许匿名用户冒名。"""
        from backend.api.routes import websocket as ws_module

        assert ws_module.resolve_websocket_user(token=None, client_user_id="alice") is None
        assert ws_module.resolve_websocket_user(token="", client_user_id="alice") is None
        assert ws_module.resolve_websocket_user(token="garbage.token.value", client_user_id="alice") is None

    def test_resolve_user_ignores_client_user_id_when_no_token(self):
        """无 token 时,客户端自报的 user_id 必须被忽略。"""
        from backend.api.routes import websocket as ws_module

        # 客户端想冒充 bob,但没 token
        resolved = ws_module.resolve_websocket_user(token=None, client_user_id="bob")
        assert resolved is None

    def test_resolve_user_with_tampered_token_fails(self):
        """被篡改的 token 必须失败(不抛出,但返回 None)。"""
        from backend.api.routes import websocket as ws_module

        resolved = ws_module.resolve_websocket_user(
            token="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhbGljZSJ9.tampered",
            client_user_id="alice",
        )
        assert resolved is None

    def test_resolve_user_with_expired_token_fails(self, monkeypatch):
        """过期 token 必须返回 None。"""
        from datetime import timedelta

        from backend.api.auth import create_access_token
        from backend.api.routes import websocket as ws_module

        expired = create_access_token(
            {"sub": "alice", "exp": 1},  # 1970-01-01
            expires_delta=timedelta(seconds=-1),
        )
        resolved = ws_module.resolve_websocket_user(token=expired, client_user_id="alice")
        assert resolved is None
