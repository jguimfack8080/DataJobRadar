"""Service-Schicht fuer Stellenanzeigen."""
from __future__ import annotations

from typing import Optional

from analytics.engine.duckdb_engine import DuckDBEngine
from analytics.queries.kennzahlen import JobsFilter, abfrage_jobs_seite

from backend.app.schemas.antworten import Job, JobsSeite


class JobsService:
    def __init__(self, engine: DuckDBEngine) -> None:
        self._engine = engine

    def seite_laden(
        self,
        *,
        suche: Optional[str] = None,
        stadt: Optional[str] = None,
        unternehmen: Optional[str] = None,
        skill: Optional[str] = None,
        nach_keyset: Optional[str] = None,
        limit: int = 25,
    ) -> JobsSeite:
        zeilen = abfrage_jobs_seite(
            self._engine,
            JobsFilter(
                suche=suche,
                stadt=stadt,
                unternehmen=unternehmen,
                skill=skill,
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
