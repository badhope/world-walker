"""
安全响应头中间件 — 弥补 <meta> CSP 限制。
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    为所有响应附加安全头:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: 禁用敏感 API
    - Strict-Transport-Security: HTTPS-only 站点生效
    - Content-Security-Policy: frame-ancestors 必须走 header,meta 不支持
    """

    def __init__(self, app: ASGIApp, *, hsts: bool = False):
        super().__init__(app)
        self.hsts = hsts

    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        # 防止 MIME 嗅探
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # 防止 clickjacking
        response.headers.setdefault("X-Frame-Options", "DENY")
        # 控制 referrer 泄露
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # 禁用浏览器敏感 API(摄像头/麦克风/地理/支付)
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
        )
        # HSTS(只在生产 HTTPS 启用)
        if self.hsts:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        # CSP frame-ancestors 必须走 header(meta 标签不生效)
        # 已通过 meta 设置其他指令,这里只补 frame-ancestors
        if "Content-Security-Policy" not in response.headers:
            response.headers.setdefault("Content-Security-Policy", "frame-ancestors 'none'")
        return response
