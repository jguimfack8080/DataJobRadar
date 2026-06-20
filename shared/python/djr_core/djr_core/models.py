"""Geteilte Datenmodelle der Plattform."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class GeoKoordinate(BaseModel):
    breitengrad: float = Field(..., ge=-90.0, le=90.0)
    laengengrad: float = Field(..., ge=-180.0, le=180.0)


class RohStellenanzeige(BaseModel):
    """Validierte Rohanzeige aus der Adzuna API (Bronze)."""

    adzuna_id: str = Field(..., min_length=1)
    titel: str = Field(..., min_length=1)
    beschreibung: str = Field(default="")
    unternehmen: Optional[str] = None
    standort_anzeige: Optional[str] = None
    standort_segmente: List[str] = Field(default_factory=list)
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


class StellenanzeigeSilber(BaseModel):
    """Bereinigte und normalisierte Stellenanzeige (Silver)."""

    adzuna_id: str
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
