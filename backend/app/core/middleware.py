"""Middleware: Korrelationskennung und einfaches Rate Limiting."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from djr_core.logging import get_logger
from djr_core.utils import neue_korrelationskennung

_logger = get_logger("backend.middleware")


class KorrelationsMiddleware(BaseHTTPMiddleware):
    """Setzt fuer jede Anfrage eine Korrelationskennung."""

    HEADER = "X-Korrelations-Kennung"

    async def dispatch(self, request: Request, call_next):
        kennung = request.headers.get(self.HEADER) or neue_korrelationskennung()
        request.state.korrelationskennung = kennung
        start = time.perf_counter()
        antwort: Response = await call_next(request)
        dauer_ms = (time.perf_counter() - start) * 1000.0
        antwort.headers[self.HEADER] = kennung
        _logger.info(
            "http_anfrage",
            methode=request.method,
            pfad=request.url.path,
            status=antwort.status_code,
            dauer_ms=round(dauer_ms, 2),
            kennung=kennung,
        )
        return antwort


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Einfaches IP-basiertes Token-Bucket-Pendant in-process.

    Bewusst leichtgewichtig (kein Redis). Ausreichend fuer ein einzelnes
    Backend hinter Nginx.
    """

    def __init__(self, app, anfragen_pro_minute: int = 120) -> None:
        super().__init__(app)
        self._limit = anfragen_pro_minute
        self._fenster = 60.0
        self._verlauf: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        klient = request.client.host if request.client else "unbekannt"
        jetzt = time.time()
        with self._lock:
            puffer = self._verlauf[klient]
            while puffer and jetzt - puffer[0] > self._fenster:
                puffer.popleft()
            if len(puffer) >= self._limit:
                _logger.warning("rate_limit_ueberschritten", klient=klient)
                from fastapi.responses import ORJSONResponse

                return ORJSONResponse(
                    status_code=429,
                    content={
                        "code": "rate_limit_ueberschritten",
                        "meldung": "Zu viele Anfragen. Bitte versuchen Sie es spaeter erneut.",
                    },
                )
            puffer.append(jetzt)
        return await call_next(request)
