"""Admin-Dashboard: Besucherstatistiken. Token-geschuetzt."""
from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

_BERLIN = ZoneInfo("Europe/Berlin")

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/admin", tags=["admin"])

_BESUCH_PFAD = Path(os.getenv("BESUCH_LOG_PFAD", "/data/logs/visites.txt"))
_ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")


def _token_pruefen(token: str) -> None:
    if not _ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="ADMIN_TOKEN nicht konfiguriert.")
    if token != _ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Ungueltig.")


def _zeilen_lesen() -> list[dict[str, str]]:
    if not _BESUCH_PFAD.exists():
        return []
    eintraege: list[dict[str, str]] = []
    try:
        for zeile in _BESUCH_PFAD.read_text(encoding="utf-8").splitlines():
            teile = [t.strip() for t in zeile.split("|")]
            if len(teile) < 7:
                continue
            eintraege.append({
                "zeitpunkt": teile[0],
                "ip":        teile[1],
                "geo":       teile[2],
                "pfad":      teile[3],
                "status":    teile[4],
                "ua":        teile[5],
                "referrer":  teile[6] if len(teile) > 6 else "-",
            })
    except Exception:
        pass
    return eintraege


def _heute_str() -> str:
    return datetime.now(_BERLIN).strftime("%Y-%m-%d")


def _woche_tage() -> set[str]:
    from datetime import timedelta
    heute = datetime.now(_BERLIN).date()
    return {str(heute - timedelta(days=i)) for i in range(7)}


def _monat_str() -> str:
    return datetime.now(_BERLIN).strftime("%Y-%m")


def _geo_teil(geo: str, index: int) -> str:
    teile = [t.strip() for t in geo.split("|")]
    return teile[index] if index < len(teile) else "?"


def _referrer_domain(ref: str) -> str:
    if not ref or ref == "-":
        return "Direkt"
    try:
        from urllib.parse import urlparse
        d = urlparse(ref).netloc or ref
        return d.replace("www.", "")
    except Exception:
        return ref[:40]


def _ua_kuerzen(ua: str) -> str:
    if not ua or ua == "-":
        return "Unbekannt"
    ua_l = ua.lower()
    if "googlebot" in ua_l or "bingbot" in ua_l or "bot/" in ua_l or "crawler" in ua_l:
        return "Bot/Crawler"
    if "mobile" in ua_l or "android" in ua_l or "iphone" in ua_l:
        return "Mobile"
    if "windows" in ua_l:
        return "Windows"
    if "macintosh" in ua_l or "mac os" in ua_l:
        return "macOS"
    if "linux" in ua_l:
        return "Linux"
    return "Sonstige"


@router.get("/visites-stats", include_in_schema=False)
def visites_stats(
    request: Request,
    token: str = Query(default=""),
) -> JSONResponse:
    _token_pruefen(token)

    eintraege = _zeilen_lesen()
    heute = _heute_str()
    woche = _woche_tage()
    monat = _monat_str()

    gesamt = len(eintraege)
    ips = {e["ip"] for e in eintraege}
    heute_n = sum(1 for e in eintraege if e["zeitpunkt"].startswith(heute))
    woche_n = sum(1 for e in eintraege if any(e["zeitpunkt"].startswith(t) for t in woche))
    monat_n = sum(1 for e in eintraege if e["zeitpunkt"].startswith(monat))

    tage_zaehler: Counter = Counter()
    laender_zaehler: Counter = Counter()
    staedte_zaehler: Counter = Counter()
    isps_zaehler: Counter = Counter()
    pfade_zaehler: Counter = Counter()
    referrer_zaehler: Counter = Counter()
    status_zaehler: Counter = Counter()
    ua_zaehler: Counter = Counter()

    for e in eintraege:
        tag = e["zeitpunkt"][:10]
        tage_zaehler[tag] += 1
        laender_zaehler[_geo_teil(e["geo"], 0)] += 1
        staedte_zaehler[_geo_teil(e["geo"], 1)] += 1
        isps_zaehler[_geo_teil(e["geo"], 2)] += 1
        pfade_zaehler[e["pfad"].split("?")[0]] += 1
        referrer_zaehler[_referrer_domain(e["referrer"])] += 1
        status_zaehler[e["status"]] += 1
        ua_zaehler[_ua_kuerzen(e["ua"])] += 1

    from datetime import timedelta
    heute_dt = datetime.now(_BERLIN).date()
    pro_tag = []
    for i in range(29, -1, -1):
        t = str(heute_dt - timedelta(days=i))
        pro_tag.append({"tag": t, "anzahl": tage_zaehler.get(t, 0)})

    def top(c: Counter, n: int = 10) -> list[dict[str, Any]]:
        return [{"name": k, "anzahl": v} for k, v in c.most_common(n)]

    alle_besuche = list(reversed(eintraege))

    return JSONResponse({
        "gesamt": gesamt,
        "eindeutige_ips": len(ips),
        "heute": heute_n,
        "diese_woche": woche_n,
        "diesen_monat": monat_n,
        "pro_tag": pro_tag,
        "top_laender": top(laender_zaehler),
        "top_staedte": top(staedte_zaehler),
        "top_pfade": top(pfade_zaehler),
        "top_referrer": top(referrer_zaehler),
        "top_isps": top(isps_zaehler),
        "status_verteilung": top(status_zaehler, 20),
        "geraete": top(ua_zaehler),
        "alle_besuche": alle_besuche,
    })
