"""Service-Schicht fuer Stellenanzeigen."""
from __future__ import annotations

from typing import List, Optional

from analytics.engine.duckdb_engine import DuckDBEngine
from analytics.queries.kennzahlen import (
    JobsFilter,
    abfrage_filter_facetten,
    abfrage_jobs_seite,
)

from backend.app.schemas.antworten import Job, JobsSeite


class JobsService:
    def __init__(self, engine: DuckDBEngine) -> None:
        self._engine = engine

    def seite_laden(
        self,
        *,
        suche: Optional[str] = None,
        stadt: Optional[str] = None,
        bundesland: Optional[str] = None,
        unternehmen: Optional[str] = None,
        kategorie: Optional[str] = None,
        vertragstyp: Optional[str] = None,
        vertragszeit: Optional[str] = None,
        waehrung: Optional[str] = None,
        gehalt_min: Optional[float] = None,
        gehalt_max: Optional[float] = None,
        nur_mit_gehalt: bool = False,
        veroeffentlicht_seit: Optional[str] = None,
        veroeffentlicht_bis: Optional[str] = None,
        skills: Optional[List[str]] = None,
        nach_keyset: Optional[str] = None,
        limit: int = 25,
    ) -> JobsSeite:
        zeilen = abfrage_jobs_seite(
            self._engine,
            JobsFilter(
                suche=suche,
                stadt=stadt,
                bundesland=bundesland,
                unternehmen=unternehmen,
                kategorie=kategorie,
                vertragstyp=vertragstyp,
                vertragszeit=vertragszeit,
                waehrung=waehrung,
                gehalt_min=gehalt_min,
                gehalt_max=gehalt_max,
                nur_mit_gehalt=nur_mit_gehalt,
                veroeffentlicht_seit=veroeffentlicht_seit,
                veroeffentlicht_bis=veroeffentlicht_bis,
                skills=skills or [],
                nach_keyset=nach_keyset,
                limit=limit,
            ),
        )
        jobs = [
            Job(
                kennung=zeile["kennung"],
                titel=zeile["titel"],
                unternehmen=zeile.get("unternehmen"),
                stadt=zeile.get("stadt"),
                bundesland=zeile.get("bundesland"),
                gehalt_min=zeile.get("gehalt_min"),
                gehalt_max=zeile.get("gehalt_max"),
                gehalt_mittel=zeile.get("gehalt_mittel"),
                waehrung=zeile.get("waehrung"),
                vertragstyp=zeile.get("vertragstyp"),
                vertragszeit=zeile.get("vertragszeit"),
                veroeffentlicht_am=zeile.get("veroeffentlicht_am"),
                kategorie=zeile.get("kategorie"),
                skills=list(zeile.get("skills") or []),
                angebots_url=zeile.get("angebots_url"),
            )
            for zeile in zeilen
        ]
        naechstes_keyset: Optional[str] = None
        if jobs and len(jobs) == limit:
            letzter = jobs[-1]
            if letzter.veroeffentlicht_am:
                naechstes_keyset = f"{letzter.veroeffentlicht_am.isoformat()}|{letzter.kennung}"
        return JobsSeite(treffer=jobs, naechstes_keyset=naechstes_keyset)

    def facetten(self) -> dict[str, list[str]]:
        return abfrage_filter_facetten(self._engine)
