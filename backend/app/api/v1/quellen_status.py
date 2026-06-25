"""Endpunkt fuer den Echtzeit-Status aller Datenquellen."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/quellen", tags=["Quellen"])

_STATUS_DATEI = Path(os.getenv("QUELLEN_STATUS_PFAD", "/data/warehouse/quellen_status.json"))

_BEZEICHNUNGEN: dict[str, str] = {
    "bundesagentur": "Bundesagentur f. Arbeit",
    "adzuna": "Adzuna",
    "arbeitnow": "Arbeitnow",
    "jooble": "Jooble",
    "jsearch": "JSearch (RapidAPI)",
    "muse": "The Muse",
    "remotive": "Remotive",
    "jobicy": "Jobicy",
    "remoteok": "RemoteOK",
}

_ALLE_QUELLEN = list(_BEZEICHNUNGEN.keys())


class QuotaInfo(BaseModel):
    verbraucht: int
    grenze: int
    prozent: float
    monatlich: bool
    reset_datum: Optional[str] = None


class QuelleStatusEintrag(BaseModel):
    name: str
    bezeichnung: str
    geladen: int = 0
    gueltig: int = 0
    quarantaene: int = 0
    abgebrochen: bool = False
    abbruchgrund: Optional[str] = None
    quota: Optional[QuotaInfo] = None


class QuellenStatusAntwort(BaseModel):
    zeitstempel: Optional[str] = None
    quellen: List[QuelleStatusEintrag]


@router.get(
    "/status",
    response_model=QuellenStatusAntwort,
    summary="Aktueller Status aller Datenquellen",
)
def quellen_status() -> QuellenStatusAntwort:
    rohdaten: dict = {}
    zeitstempel: Optional[str] = None

    if _STATUS_DATEI.exists():
        try:
            inhalt = json.loads(_STATUS_DATEI.read_text(encoding="utf-8"))
            rohdaten = inhalt.get("quellen", {})
            zeitstempel = inhalt.get("zeitstempel")
        except Exception:
            pass

    eintraege: List[QuelleStatusEintrag] = []
    for name in _ALLE_QUELLEN:
        roh = rohdaten.get(name, {})
        quota_roh = roh.get("quota")
        quota = None
        if isinstance(quota_roh, dict):
            quota = QuotaInfo(
                verbraucht=quota_roh.get("verbraucht", 0),
                grenze=quota_roh.get("grenze", 0),
                prozent=quota_roh.get("prozent", 0.0),
                monatlich=quota_roh.get("monatlich", False),
                reset_datum=quota_roh.get("reset_datum"),
            )
        eintraege.append(
            QuelleStatusEintrag(
                name=name,
                bezeichnung=_BEZEICHNUNGEN[name],
                geladen=roh.get("geladen", 0),
                gueltig=roh.get("gueltig", 0),
                quarantaene=roh.get("quarantaene", 0),
                abgebrochen=roh.get("abgebrochen", False),
                abbruchgrund=roh.get("abbruchgrund"),
                quota=quota,
            )
        )

    return QuellenStatusAntwort(zeitstempel=zeitstempel, quellen=eintraege)
