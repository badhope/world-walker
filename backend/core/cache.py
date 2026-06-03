"""
内存缓存管理模块 - 线程安全 + TTL + 容量限制
"""

import inspect
import json
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from typing import Any

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class MemoryCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._default_ttl = default_ttl

    def get(self, key: str):
        with self._lock:
            if key not in self._cache:
                return None
            value, expire_at = self._cache[key]
            if expire_at and time.time() > expire_at:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return value

    def set(self, key: str, value, ttl: int = None):
        with self._lock:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            expire_at = time.time() + (ttl or self._default_ttl)
            self._cache[key] = (value, expire_at)
            self._cache.move_to_end(key)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear_pattern(self, pattern: str) -> int:
        count = 0
        with self._lock:
            prefix = pattern.replace("*", "")
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._cache[k]
                count += 1
        return count

    def exists(self, key: str) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            value, expire_at = self._cache[key]
            if expire_at and time.time() > expire_at:
                del self._cache[key]
                return False
            return True


class CacheManager:
    """缓存管理器"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: str | None = None):
        self.redis_client = None
        self.memory_cache = MemoryCache()
        if redis is None:
            logger.warning("redis 模块未安装，使用内存缓存")
            return
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, password=password, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"Redis 连接成功: {host}:{port}/{db}")
        except Exception as e:
            logger.warning(f"Redis 连接失败，使用内存缓存: {e}")
            self.redis_client = None
            self.memory_cache = MemoryCache()

    def get(self, key: str) -> Any | None:
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
            except Exception as e:
                logger.warning(f"Redis 读取失败: {e}")
        return self.memory_cache.get(key)

    def set(self, key: str, value: Any, expire: int | None = None) -> bool:
        if isinstance(value, dict | list | tuple):
            serialized_value = json.dumps(value, ensure_ascii=False)
        else:
            serialized_value = str(value)

        if self.redis_client:
            try:
                if expire:
                    self.redis_client.setex(key, expire, serialized_value)
                else:
                    self.redis_client.set(key, serialized_value)
                return True
            except Exception as e:
                logger.warning(f"Redis 写入失败: {e}")

        self.memory_cache.set(key, value, ttl=expire)
        return True

    def delete(self, key: str) -> bool:
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.warning(f"Redis 删除失败: {e}")
        return self.memory_cache.delete(key)

    def clear_pattern(self, pattern: str) -> int:
        count = 0
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = len(keys)
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis 清除失败: {e}")
        count += self.memory_cache.clear_pattern(pattern)
        return count

    def exists(self, key: str) -> bool:
        if self.redis_client:
            try:
                return self.redis_client.exists(key) > 0
            except Exception as e:
                logger.warning(f"Redis 检查失败: {e}")
        return self.memory_cache.exists(key)

    @staticmethod
    def generate_cache_key(prefix: str, *args, **kwargs) -> str:
        key_parts = [prefix]
        for arg in args:
            key_parts.append(str(arg))
        for k in sorted(kwargs.keys()):
            key_parts.append(f"{k}:{kwargs[k]}")
        return ":".join(key_parts)


def cached(expire: int = 3600, key_prefix: str | None = None):
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            prefix = key_prefix or func.__name__
            cache_key = CacheManager.generate_cache_key(prefix, *args, **kwargs)
            result = cache_manager.get(cache_key)
            if result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, expire=expire)
            logger.debug(f"缓存设置: {cache_key}")
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            prefix = key_prefix or func.__name__
            cache_key = CacheManager.generate_cache_key(prefix, *args, **kwargs)
            result = cache_manager.get(cache_key)
            if result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, expire=expire)
            logger.debug(f"缓存设置: {cache_key}")
            return result

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


cache_manager = CacheManager()
