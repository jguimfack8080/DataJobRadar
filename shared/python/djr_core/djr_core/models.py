"""Geteilte Datenmodelle der Plattform."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field, field_validator


class JobQuelle(str, Enum):
    """Alle unterstuetzten Stellenboerse-Quellen.

    Reihenfolge bestimmt die Prioritaet bei Cross-Source-Deduplizierung.
    Hoeher = bevorzugt behalten, wenn dieselbe Stelle in mehreren Quellen erscheint.
    """

    BUNDESAGENTUR = "bundesagentur"
    ADZUNA = "adzuna"
    ARBEITNOW = "arbeitnow"
    JOOBLE = "jooble"
    JSEARCH = "jsearch"
    MUSE = "muse"
    REMOTIVE = "remotive"
    JOBICY = "jobicy"
    REMOTEOK = "remoteok"


QUELLEN_PRIORITAET: dict[JobQuelle, int] = {
    JobQuelle.BUNDESAGENTUR: 100,
    JobQuelle.ADZUNA: 90,
    JobQuelle.ARBEITNOW: 85,
    JobQuelle.JOOBLE: 75,
    JobQuelle.JSEARCH: 65,
    JobQuelle.MUSE: 70,
    JobQuelle.REMOTIVE: 60,
    JobQuelle.JOBICY: 50,
    JobQuelle.REMOTEOK: 45,
}


_WHITESPACE = re.compile(r"\s+")


def _normalisiere(text: Optional[str]) -> str:
    if not text:
        return ""
    norm = unicodedata.normalize("NFKD", text)
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = norm.lower().strip()
    norm = _WHITESPACE.sub(" ", norm)
    return norm


def job_id_berechnen(quelle: JobQuelle, quell_id: str) -> str:
    """Deterministischer, kollisionssicherer Primaerschluessel pro Job."""
    rohwert = f"{quelle.value}:{quell_id}".encode("utf-8")
    return hashlib.sha256(rohwert).hexdigest()[:24]


def dedup_signatur_berechnen(
    titel: str, unternehmen: Optional[str], stadt: Optional[str]
) -> str:
    """Cross-Source-Schluessel zum Erkennen derselben Stelle in verschiedenen Quellen."""
    teile = "|".join([_normalisiere(titel), _normalisiere(unternehmen), _normalisiere(stadt)])
    return hashlib.sha256(teile.encode("utf-8")).hexdigest()[:24]


class GeoKoordinate(BaseModel):
    breitengrad: float = Field(..., ge=-90.0, le=90.0)
    laengengrad: float = Field(..., ge=-180.0, le=180.0)


class RohStellenanzeige(BaseModel):
    """Validierte Rohanzeige aus einer beliebigen Quelle (Bronze).

    Generisches Modell - alle Quellen-spezifischen Adapter mappen auf diese Struktur.
    """

    quelle: JobQuelle
    quell_id: str = Field(..., min_length=1, description="ID innerhalb der Quelle")
    titel: str = Field(..., min_length=1)
    beschreibung: str = Field(default="")
    unternehmen: Optional[str] = None
    standort_anzeige: Optional[str] = None
    standort_segmente: List[str] = Field(default_factory=list)
    stadt: Optional[str] = None
    bundesland: Optional[str] = None
    region: Optional[str] = None
    breitengrad: Optional[float] = None
    laengengrad: Optional[float] = None
    gehalt_min: Optional[float] = None
    gehalt_max: Optional[float] = None
    gehalt_ist_vorhanden: bool = False
    waehrung: Optional[str] = None
    vertragstyp: Optional[str] = None
    vertragszeit: Optional[str] = None
    kategorie_kennung: Optional[str] = None
    kategorie_bezeichnung: Optional[str] = None
    veroeffentlicht_am: Optional[datetime] = None
    angebots_url: Optional[str] = None
    quell_kategorie: str = Field(..., min_length=1)
    abruf_zeitpunkt: datetime
    rohdaten_pfad: Optional[str] = None

    @field_validator("gehalt_min", "gehalt_max")
    @classmethod
    def _nicht_negativ(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            return None
        return value

    @computed_field  # type: ignore[misc]
    @property
    def job_id(self) -> str:
        return job_id_berechnen(self.quelle, self.quell_id)

    @computed_field  # type: ignore[misc]
    @property
    def dedup_signatur(self) -> str:
        return dedup_signatur_berechnen(self.titel, self.unternehmen, self.stadt)

    @computed_field  # type: ignore[misc]
    @property
    def quellen_prioritaet(self) -> int:
        return QUELLEN_PRIORITAET[self.quelle]


class StellenanzeigeSilber(BaseModel):
    """Bereinigte und normalisierte Stellenanzeige (Silver)."""

    job_id: str
    quelle: JobQuelle
    quell_id: str
    titel: str
    titel_normalisiert: str
    beschreibung: str
    unternehmen: Optional[str]
    unternehmen_normalisiert: Optional[str]
    stadt: Optional[str]
    bundesland: Optional[str]
    region: Optional[str]
    gehalt_min: Optional[float]
    gehalt_max: Optional[float]
    gehalt_mittel: Optional[float]
    waehrung: Optional[str]
    vertragstyp: Optional[str]
    vertragszeit: Optional[str]
    kategorie: Optional[str]
    veroeffentlicht_am: Optional[datetime]
    abruf_zeitpunkt: datetime
    skills: List[str] = Field(default_factory=list)
    angebots_url: Optional[str] = None
    dedup_signatur: str
