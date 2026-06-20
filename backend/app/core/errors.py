"""Zentrale Fehlerbehandlung mit konsistentem Antwortformat."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse

from djr_core.exceptions import (
    DJRError,
    NichtGefundenFehler,
    QuotaErschoepftFehler,
    ValidierungsFehler,
)
from djr_core.logging import get_logger

_logger = get_logger("backend.errors")


def _antwort(status: int, code: str, meldung: str, kennung: str | None = None, kontext: dict | None = None):
    return ORJSONResponse(
        status_code=status,
        content={
            "code": code,
            "meldung": meldung,
            "korrelationskennung": kennung,
            "kontext": kontext or {},
        },
    )


def fehlerbehandler_registrieren(app: FastAPI) -> None:
    @app.exception_handler(NichtGefundenFehler)
    async def _nicht_gefunden(request: Request, exc: NichtGefundenFehler):
        return _antwort(
            404,
            exc.code,
            exc.meldung,
            getattr(request.state, "korrelationskennung", None),
            exc.kontext,
        )

    @app.exception_handler(ValidierungsFehler)
    async def _validierung(request: Request, exc: ValidierungsFehler):
        return _antwort(
            400,
            exc.code,
            exc.meldung,
            getattr(request.state, "korrelationskennung", None),
            exc.kontext,
        )

    @app.exception_handler(QuotaErschoepftFehler)
    async def _quota(request: Request, exc: QuotaErschoepftFehler):
        return _antwort(
            503,
            exc.code,
            exc.meldung,
            getattr(request.state, "korrelationskennung", None),
            exc.kontext,
        )

    @app.exception_handler(DJRError)
    async def _djr(request: Request, exc: DJRError):
        return _antwort(
            500,
            exc.code,
            exc.meldung,
            getattr(request.state, "korrelationskennung", None),
            exc.kontext,
        )

    @app.exception_handler(RequestValidationError)
    async def _request_validierung(request: Request, exc: RequestValidationError):
        return _antwort(
            422,
            "ungueltige_anfrage",
            "Die Anfrageparameter sind ungueltig.",
            getattr(request.state, "korrelationskennung", None),
            {"fehler": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def _unbekannt(request: Request, exc: Exception):
        kennung = getattr(request.state, "korrelationskennung", None)
        _logger.error("interner_fehler", fehler=str(exc), kennung=kennung)
        return _antwort(
            500,
            "interner_fehler",
            "Ein interner Fehler ist aufgetreten.",
            kennung,
        )
