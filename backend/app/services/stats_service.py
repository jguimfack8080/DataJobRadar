"""Service-Schicht fuer Statistiken und Aggregationen."""
from __future__ import annotations

from typing import List

from analytics.engine.duckdb_engine import DuckDBEngine
from analytics.queries.kennzahlen import (
    abfrage_gehaltsverteilung,
    abfrage_kennzahlen_gesamt,
    abfrage_top_skills,
    abfrage_top_staedte,
    abfrage_top_unternehmen,
    abfrage_zeitreihe_neue_jobs,
)

from backend.app.core.cache import cachen
from backend.app.schemas.antworten import (
    GehaltsverteilungEintrag,
    KennzahlenGesamt,
    SkillKennzahl,
    StadtKennzahl,
    UnternehmensKennzahl,
    ZeitreihePunkt,
)


class StatsService:
    def __init__(self, engine: DuckDBEngine) -> None:
        self._engine = engine

    @cachen(lambda self: ("kennzahlen",))
    def kennzahlen(self) -> KennzahlenGesamt:
        zeile = abfrage_kennzahlen_gesamt(self._engine)
        if not zeile:
            return KennzahlenGesamt(anzahl_jobs=0, anzahl_unternehmen=0, anzahl_standorte=0)
        return KennzahlenGesamt(
            anzahl_jobs=int(zeile.get("anzahl_jobs") or 0),
            anzahl_unternehmen=int(zeile.get("anzahl_unternehmen") or 0),
            anzahl_standorte=int(zeile.get("anzahl_standorte") or 0),
            anzahl_quellen=int(zeile.get("anzahl_quellen") or 0),
            gehalt_mittel=zeile.get("gehalt_mittel"),
            frueheste_anzeige=zeile.get("frueheste_anzeige"),
            spaeteste_anzeige=zeile.get("spaeteste_anzeige"),
        )

    @cachen(lambda self, limit=20: ("skills", limit))
    def top_skills(self, limit: int = 20) -> List[SkillKennzahl]:
        zeilen = abfrage_top_skills(self._engine, limit=limit)
        return [
            SkillKennzahl(
                skill=z["skill"],
                anzahl=int(z["anzahl"]),
                anzahl_jobs=int(z["anzahl_jobs"]),
            )
            for z in zeilen
        ]

    @cachen(lambda self, limit=20: ("unternehmen", limit))
    def top_unternehmen(self, limit: int = 20) -> List[UnternehmensKennzahl]:
        zeilen = abfrage_top_unternehmen(self._engine, limit=limit)
        return [
            UnternehmensKennzahl(
                unternehmen=z["unternehmen"],
                anzahl_jobs=int(z["anzahl_jobs"]),
                gehalt_mittel=z.get("gehalt_mittel"),
            )
            for z in zeilen
        ]

    @cachen(lambda self, limit=20: ("staedte", limit))
    def top_staedte(self, limit: int = 20) -> List[StadtKennzahl]:
        zeilen = abfrage_top_staedte(self._engine, limit=limit)
        return [
            StadtKennzahl(
                stadt=z["stadt"],
                bundesland=z.get("bundesland"),
                anzahl_jobs=int(z["anzahl_jobs"]),
                gehalt_mittel=z.get("gehalt_mittel"),
            )
            for z in zeilen
        ]

    @cachen(lambda self, tage=30: ("zeitreihe", tage))
    def zeitreihe(self, tage: int = 30) -> List[ZeitreihePunkt]:
        zeilen = abfrage_zeitreihe_neue_jobs(self._engine, tage=tage)
        return [
            ZeitreihePunkt(tag=z["tag"], anzahl=int(z["anzahl"]))
            for z in zeilen
            if z.get("tag")
        ]

    @cachen(lambda self, gruppierung="kategorie": ("verteilung", gruppierung))
    def gehaltsverteilung(self, gruppierung: str = "kategorie") -> List[GehaltsverteilungEintrag]:
        zeilen = abfrage_gehaltsverteilung(self._engine, gruppierung=gruppierung)
        return [
            GehaltsverteilungEintrag(
                gruppe=str(z.get("gruppe") or ""),
                anzahl=int(z.get("anzahl") or 0),
                gehalt_p25=z.get("gehalt_p25"),
                gehalt_median=z.get("gehalt_median"),
                gehalt_p75=z.get("gehalt_p75"),
                gehalt_mittel=z.get("gehalt_mittel"),
            )
            for z in zeilen
            if z.get("gruppe")
        ]
