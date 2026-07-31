"""
菜谱方案缓存（MVP：内存 dict）
抽象 Cache 接口，未来切 Redis 时换实现。
"""
import threading
from typing import Optional, Protocol

from loguru import logger

from app.schemas import DishScheme


class Cache(Protocol):
    """缓存抽象接口"""

    def put(self, scheme_id: str, scheme: DishScheme) -> None: ...
    def get(self, scheme_id: str) -> Optional[DishScheme]: ...
    def invalidate(self, scheme_id: Optional[str] = None) -> None: ...


class InMemoryCache:
    """进程内 dict 缓存。线程安全。"""

    def __init__(self) -> None:
        self._store: dict[str, DishScheme] = {}
        self._lock = threading.RLock()

    def put(self, scheme_id: str, scheme: DishScheme) -> None:
        with self._lock:
            self._store[scheme_id] = scheme
        logger.debug(f"cache.put scheme_id={scheme_id}")

    def get(self, scheme_id: str) -> Optional[DishScheme]:
        with self._lock:
            return self._store.get(scheme_id)

    def invalidate(self, scheme_id: Optional[str] = None) -> None:
        with self._lock:
            if scheme_id:
                self._store.pop(scheme_id, None)
                logger.debug(f"cache.invalidate scheme_id={scheme_id}")
            else:
                self._store.clear()
                logger.debug("cache.invalidate all")


# 全局单例
_cache: Optional[Cache] = None


def get_cache() -> Cache:
    global _cache
    if _cache is None:
        _cache = InMemoryCache()
    return _cache
