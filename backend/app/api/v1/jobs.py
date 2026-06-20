"""Endpunkte fuer Stellenanzeigen."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from analytics.engine.duckdb_engine import DuckDBEngine

from backend.app.core.abhaengigkeiten import get_engine
from backend.app.schemas.antworten import JobsSeite
from backend.app.services.jobs_service import JobsService

router = APIRouter(prefix="/jobs", tags=["Stellenanzeigen"])


@router.get(
    "",
    response_model=JobsSeite,
    summary="Stellenanzeigen abrufen",
    description=(
        "Liefert eine seitenweise Liste der Stellenanzeigen. "
        "Unterstuetzt Volltextsuche, Filter und Keyset-Pagination."
    ),
)
def jobs_auflisten(
    engine: Annotated[DuckDBEngine, Depends(get_engine)],
    suche: Annotated[Optional[str], Query(min_length=1, max_length=100, description="Volltextsuche")] = None,
    stadt: Annotated[Optional[str], Query(min_length=1, max_length=80)] = None,
    unternehmen: Annotated[Optional[str], Query(min_length=1, max_length=120)] = None,
    skill: Annotated[Optional[str], Query(min_length=1, max_length=40)] = None,
    nach: Annotated[Optional[str], Query(description="Keyset-Token fuer naechste Seite")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> JobsSeite:
    service = JobsService(engine)
    return service.seite_laden(
        suche=suche,
        stadt=stadt,
        unternehmen=unternehmen,
        skill=skill,
        nach_keyset=nach,
        limit=limit,
    )
