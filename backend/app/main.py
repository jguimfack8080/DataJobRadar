"""Einstiegspunkt der FastAPI-Anwendung."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from starlette.staticfiles import StaticFiles

from djr_core import configure_logging, get_logger, get_settings

from backend.app.api.v1.router import router as v1_router
from backend.app.core.cache import resultcache_leeren
from backend.app.core.errors import fehlerbehandler_registrieren
from backend.app.core.middleware import KorrelationsMiddleware, RateLimitMiddleware


_logger = get_logger("backend.main")


@asynccontextmanager
async def lebenszyklus(app: FastAPI):
    konfiguration = get_settings()
    configure_logging(level=konfiguration.log_level, as_json=konfiguration.log_format == "json")
    _logger.info("backend_start", port=konfiguration.backend.port)
    yield
    resultcache_leeren()
    _logger.info("backend_stopp")


def app_erzeugen() -> FastAPI:
    einstellungen = get_settings()
    app = FastAPI(
        title="Data Job Radar Deutschland",
        version="0.1.0",
        description=(
            "Analyseplattform fuer den deutschen IT-Arbeitsmarkt auf Basis der Adzuna API. "
            "Die API stellt Stellenanzeigen, Statistiken, Skills, Unternehmen, Staedte und "
            "Trends bereit."
        ),
        default_response_class=ORJSONResponse,
        lifespan=lebenszyklus,
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=einstellungen.backend.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(KorrelationsMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        anfragen_pro_minute=einstellungen.backend.rate_limit_per_minute,
    )

    fehlerbehandler_registrieren(app)
    app.include_router(v1_router, prefix="/api/v1")

    @app.get("/api/v1/health", tags=["system"], summary="Gesundheitspruefung")
    async def health(request: Request) -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/ready", tags=["system"], summary="Bereitschaftspruefung")
    async def ready(request: Request) -> dict[str, str]:
        return {"status": "ok"}

    frontend_pfad = Path(os.environ.get("FRONTEND_STATIC_PATH", "/app/frontend_static"))
    if frontend_pfad.exists():
        app.mount(
            "/",
            StaticFiles(directory=str(frontend_pfad), html=True),
            name="frontend",
        )
        _logger.info("frontend_statisch_montiert", pfad=str(frontend_pfad))
    else:
        _logger.info("frontend_statisch_nicht_vorhanden", pfad=str(frontend_pfad))

    return app


app = app_erzeugen()
