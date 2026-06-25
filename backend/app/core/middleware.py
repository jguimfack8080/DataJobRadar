"""Middleware: Korrelationskennung, Rate Limiting und Besucherprotokoll."""
from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Deque, Dict, Optional

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from djr_core.logging import get_logger
from djr_core.utils import neue_korrelationskennung

_logger = get_logger("backend.middleware")

_BESUCH_PFAD = Path(os.getenv("BESUCH_LOG_PFAD", "/data/logs/visites.txt"))
_GEO_CACHE: Dict[str, str] = {}
_GEO_CACHE_MAX = 2000

_IGNORIERTE_PFADE = ("/api/v1/health", "/api/v1/ready")
_IGNORIERTE_PREFIXE = ("/_next/", "/favicon", "/static/", "/__nextjs")


async def _geo_nachschlagen(ip: str) -> str:
    """Fragt ip-api.com nach Land, Stadt und ISP. Gibt leeren String bei Fehler zurueck."""
    if ip in ("unbekannt", "127.0.0.1", "::1") or ip.startswith("192.168.") or ip.startswith("10."):
        return "lokal"
    if ip in _GEO_CACHE:
        return _GEO_CACHE[ip]
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,country,regionName,city,isp", "lang": "de"},
            )
            d = r.json()
            if d.get("status") == "success":
                geo = f"{d.get('country', '')} | {d.get('city', '')} | {d.get('isp', '')}"
            else:
                geo = "unbekannt"
    except Exception:
        geo = "unbekannt"
    if len(_GEO_CACHE) >= _GEO_CACHE_MAX:
        _GEO_CACHE.clear()
    _GEO_CACHE[ip] = geo
    return geo


def _ip_ermitteln(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unbekannt"


async def _zeile_schreiben(
    zeitpunkt: str,
    ip: str,
    geo: str,
    methode: str,
    pfad: str,
    status: int,
    ua: str,
    referer: str,
) -> None:
    try:
        _BESUCH_PFAD.parent.mkdir(parents=True, exist_ok=True)
        zeile = (
            f"{zeitpunkt} | {ip} | {geo} | {methode} {pfad} | {status} | "
            f"{ua[:120]} | {referer or '-'}\n"
        )
        with open(_BESUCH_PFAD, "a", encoding="utf-8") as f:
            f.write(zeile)
    except Exception:
        pass


class BesucherMiddleware(BaseHTTPMiddleware):
    """Protokolliert jeden Seitenaufruf mit IP, Geo-Standort und User-Agent."""

    async def dispatch(self, request: Request, call_next):
        pfad = request.url.path
        if pfad in _IGNORIERTE_PFADE or any(pfad.startswith(p) for p in _IGNORIERTE_PREFIXE):
            return await call_next(request)

        ip = _ip_ermitteln(request)
        zeitpunkt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        methode = request.method
        ua = request.headers.get("user-agent", "-")
        referer = request.headers.get("referer", "")

        antwort: Response = await call_next(request)

        asyncio.ensure_future(
            _zeile_schreiben(
                zeitpunkt=zeitpunkt,
                ip=ip,
                geo=await _geo_nachschlagen(ip),
                methode=methode,
                pfad=pfad,
                status=antwort.status_code,
                ua=ua,
                referer=referer,
            )
        )
        return antwort


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
