"""
轻量限流:不依赖 slowapi(避免新增重依赖),用内存 token bucket。
为单进程设计;多 worker 部署时需要换 Redis 后端。
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request, status


class _RateLimiter:
    """滑动窗口限流(按 IP+路径 计数)。"""

    def __init__(self, default_limit: str = "60/minute"):
        self._default = default_limit
        self._buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._rules: dict[str, tuple[int, int]] = {}
        # 预解析 default
        self._rules["__default__"] = self._parse(default_limit)

    @staticmethod
    def _parse(rule: str) -> tuple[int, int]:
        """
        "5/minute" -> (5, 60)
        "100/hour"  -> (100, 3600)
        """
        n, _, unit = rule.partition("/")
        count = int(n.strip())
        unit = unit.strip().lower()
        window = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}.get(unit, 60)
        return count, window

    def _key(self, request: Request) -> tuple[str, str]:
        ip = request.client.host if request.client else "unknown"
        # 路径模板(strip query)
        return ip, request.url.path

    def check(self, request: Request) -> None:
        key = self._key(request)
        count, window = self._rules["__default__"]
        now = time.time()
        with self._lock:
            bucket = self._buckets[key]
            cutoff = now - window
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= count:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {count} requests per {window}s",
                    headers={"Retry-After": str(window)},
                )
            bucket.append(now)

    def limit(self, rule: str) -> Callable:
        """
        装饰器用法:
            @limiter.limit("5/minute")
            def login(...): ...
        """
        count, window = self._parse(rule)
        rule_key = f"custom_{rule}_{count}_{window}"

        def decorator(fn: Callable) -> Callable:
            self._rules[rule_key] = (count, window)
            # 包装原函数,执行前检查
            from functools import wraps

            @wraps(fn)
            def wrapper(*args, **kwargs):
                # 找到 request 参数(FastAPI 会注入)
                request = kwargs.get("request") or (args[0] if args and isinstance(args[0], Request) else None)
                if request is not None:
                    self._apply(request, count, window)
                return fn(*args, **kwargs)

            return wrapper

        return decorator

    def _apply(self, request: Request, count: int, window: int) -> None:
        key = (request.client.host if request.client else "unknown", request.url.path)
        now = time.time()
        with self._lock:
            bucket = self._buckets[key]
            cutoff = now - window
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= count:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {count} requests per {window}s",
                    headers={"Retry-After": str(window)},
                )
            bucket.append(now)


limiter = _RateLimiter(default_limit="120/minute")  # 默认每分钟 120 次
