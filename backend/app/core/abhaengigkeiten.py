"""FastAPI-Abhaengigkeiten."""
from __future__ import annotations

from functools import lru_cache

from analytics.engine.duckdb_engine import DuckDBEngine


@lru_cache(maxsize=1)
def engine_singleton() -> DuckDBEngine:
    return DuckDBEngine(nur_lesen=True)


def get_engine() -> DuckDBEngine:
    return engine_singleton()
