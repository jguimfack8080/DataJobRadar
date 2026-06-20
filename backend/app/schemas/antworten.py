"""Pydantic-Antwortmodelle."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Job(BaseModel):
    kennung: str = Field(..., description="Stabile Adzuna-Kennung der Anzeige.")
    titel: str
    unternehmen: Optional[str] = None
    stadt: Optional[str] = None
    bundesland: Optional[str] = None
    gehalt_min: Optional[float] = None
    gehalt_max: Optional[float] = None
    gehalt_mittel: Optional[float] = None
    waehrung: Optional[str] = None
    vertragstyp: Optional[str] = None
    vertragszeit: Optional[str] = None
    veroeffentlicht_am: Optional[datetime] = None
    kategorie: Optional[str] = None
    skills: List[str] = Field(default_factory=list)


class JobsSeite(BaseModel):
    treffer: List[Job]
    naechstes_keyset: Optional[str] = Field(
        default=None,
        description="Token fuer die naechste Seite (Format: ISO8601|adzuna_id).",
    )


class KennzahlenGesamt(BaseModel):
    anzahl_jobs: int
    anzahl_unternehmen: int
    anzahl_standorte: int
    gehalt_mittel: Optional[float] = None
    frueheste_anzeige: Optional[datetime] = None
    spaeteste_anzeige: Optional[datetime] = None


class SkillKennzahl(BaseModel):
    skill: str
    anzahl: int
    anzahl_jobs: int


class UnternehmensKennzahl(BaseModel):
    unternehmen: str
    anzahl_jobs: int
    gehalt_mittel: Optional[float] = None


class StadtKennzahl(BaseModel):
    stadt: str
    bundesland: Optional[str] = None
    anzahl_jobs: int
    gehalt_mittel: Optional[float] = None


class ZeitreihePunkt(BaseModel):
    tag: datetime
    anzahl: int


class GehaltsverteilungEintrag(BaseModel):
    gruppe: str
    anzahl: int
    gehalt_p25: Optional[float] = None
    gehalt_median: Optional[float] = None
    gehalt_p75: Optional[float] = None
    gehalt_mittel: Optional[float] = None
