"""
Redis 缓存管理模块 - 高性能缓存系统
"""
import json
import pickle
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
import logging

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis 缓存管理器"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.redis_client = None
        self.memory_cache = {}
        if redis is None:
            logger.warning("redis 模块未安装，使用内存缓存")
            return
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True  # 自动解码字符串
            )
            # 测试连接
            self.redis_client.ping()
            logger.info(f"Redis 连接成功: {host}:{port}/{db}")
        except Exception as e:
            logger.warning(f"Redis 连接失败，使用内存缓存: {e}")
            self.redis_client = None
            self.memory_cache = {}  # 内存缓存作为备选

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的值，如果不存在返回 None
        """
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    # 尝试 JSON 解析
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
            except Exception as e:
                logger.warning(f"Redis 读取失败: {e}")
        
        # 回退到内存缓存
        return self.memory_cache.get(key)

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
            
        Returns:
            是否成功
        """
        # 序列化复杂对象
        if isinstance(value, (dict, list, tuple)):
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
        
        # 回退到内存缓存
        self.memory_cache[key] = value
        return True

    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.warning(f"Redis 删除失败: {e}")
        
        # 回退到内存缓存
        if key in self.memory_cache:
            del self.memory_cache[key]
            return True
        
        return False

    def clear_pattern(self, pattern: str) -> int:
        """
        按模式清除缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            删除的数量
        """
        count = 0
        
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    count = len(keys)
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis 清除失败: {e}")
        
        # 同时清理内存缓存
        keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(pattern.replace('*', ''))]
        for k in keys_to_delete:
            del self.memory_cache[k]
        
        return count

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        if self.redis_client:
            try:
                return self.redis_client.exists(key) > 0
            except Exception as e:
                logger.warning(f"Redis 检查失败: {e}")
        
        # 回退到内存缓存
        return key in self.memory_cache

    @staticmethod
    def generate_cache_key(prefix: str, *args, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 前缀
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            缓存键
        """
        key_parts = [prefix]
        
        for arg in args:
            key_parts.append(str(arg))
        
        for k in sorted(kwargs.keys()):
            key_parts.append(f"{k}:{kwargs[k]}")
        
        return ":".join(key_parts)


def cached(expire: int = 3600, key_prefix: Optional[str] = None):
    """
    缓存装饰器
    
    Args:
        expire: 过期时间（秒）
        key_prefix: 键前缀
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            prefix = key_prefix or func.__name__
            cache_key = CacheManager.generate_cache_key(prefix, *args, **kwargs)
            
            # 先尝试从缓存获取
            result = cache_manager.get(cache_key)
            if result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return result
            
            # 执行函数
            result = await func(*args, **kwargs) if hasattr(func, '__code__') and 'async' in func.__code__.co_flags else func(*args, **kwargs)
            
            # 缓存结果
            cache_manager.set(cache_key, result, expire=expire)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        return wrapper
    return decorator


# 全局缓存管理器实例
cache_manager = CacheManager()
