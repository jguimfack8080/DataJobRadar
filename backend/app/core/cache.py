"""In-Memory-Cache fuer teure Aggregationen.

Ressourcenarm: nutzt cachetools (TTL und Groessenbegrenzung) statt eines
externen Cache-Dienstes wie Redis.
"""
from __future__ import annotations

import threading
from functools import wraps
from typing import Any, Callable, Hashable, TypeVar

from cachetools import TTLCache

from djr_core import get_settings

T = TypeVar("T")

_einstellungen = get_settings()
_cache: TTLCache[Any, Any] = TTLCache(maxsize=512, ttl=_einstellungen.backend.cache_ttl_seconds)
_lock = threading.Lock()


def resultcache_leeren() -> None:
    with _lock:
        _cache.clear()


def cachen(schluessel_fn: Callable[..., Hashable]) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Dekorator fuer synchrones Caching mit TTL."""

    def wrapper(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def innere(*args: Any, **kwargs: Any) -> T:
            schluessel = schluessel_fn(*args, **kwargs)
            with _lock:
                if schluessel in _cache:
                    return _cache[schluessel]
            ergebnis = fn(*args, **kwargs)
            with _lock:
                _cache[schluessel] = ergebnis
            return ergebnis

        return innere

    return wrapper
