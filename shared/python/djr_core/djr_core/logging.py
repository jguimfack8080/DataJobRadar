"""Strukturierte Protokollierung mit Korrelationskennungen."""
from __future__ import annotations

import logging
import sys
from typing import Any

import orjson
import structlog


def _orjson_dumps(obj: Any, default=None) -> str:
    return orjson.dumps(obj, default=default).decode("utf-8")


def configure_logging(level: str = "INFO", as_json: bool = True) -> None:
    """Initialisiert globale Logging-Konfiguration einmalig pro Prozess."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.StackInfoRenderer(),
        timestamper,
    ]

    if as_json:
        renderer = structlog.processors.JSONRenderer(serializer=_orjson_dumps)
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=False)

    structlog.configure(
        processors=[*shared_processors, structlog.processors.format_exc_info, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(format="%(message)s", level=log_level, handlers=[logging.StreamHandler(sys.stdout)])


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Liefert einen konfigurierten Logger."""
    return structlog.get_logger(name)
