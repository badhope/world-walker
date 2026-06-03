"""
安全回归测试:CORS 与 TrustedHost 中间件 (M-02 / M-04)
"""

import pytest


@pytest.mark.unit
class TestCorsConfiguration:
    """CORS 不应允许任意方法 / 任意 header,而是显式白名单。"""

    def test_cors_methods_are_explicit_allowlist(self):
        from backend.api.main import app

        cors = next(
            (m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"),
            None,
        )
        assert cors is not None, "CORSMiddleware must be registered"
        methods = cors.kwargs.get("allow_methods")
        assert methods != ["*"], "allow_methods must be an explicit allowlist, not '*'"
        assert "GET" in methods
        assert "POST" in methods

    def test_cors_headers_are_explicit_allowlist(self):
        from backend.api.main import app

        cors = next(
            (m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"),
            None,
        )
        assert cors is not None
        headers = cors.kwargs.get("allow_headers")
        assert headers != ["*"], "allow_headers must be an explicit allowlist, not '*'"
        assert "Authorization" in headers
        assert "Content-Type" in headers

    def test_cors_origins_not_wildcard(self):
        from backend.api.main import app

        cors = next(
            (m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"),
            None,
        )
        origins = cors.kwargs.get("allow_origins")
        assert origins != ["*"]


@pytest.mark.unit
class TestTrustedHostMiddleware:
    """Host 头必须被 TrustedHostMiddleware 校验。"""

    def test_trusted_host_middleware_registered(self):
        from backend.api.main import app

        trusted = next(
            (m for m in app.user_middleware if m.cls.__name__ == "TrustedHostMiddleware"),
            None,
        )
        assert trusted is not None, "TrustedHostMiddleware must be registered"
        allowed = trusted.kwargs.get("allowed_hosts")
        # 必须是非空白名单,允许 localhost 用于开发
        assert allowed
        assert "*" not in allowed, "wildcard host is too permissive"
