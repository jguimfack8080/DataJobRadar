"""Endpunkte fuer Unternehmen."""
from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from analytics.engine.duckdb_engine import DuckDBEngine

from backend.app.core.abhaengigkeiten import get_engine
from backend.app.schemas.antworten import UnternehmensKennzahl
from backend.app.services.stats_service import StatsService

router = APIRouter(prefix="/companies", tags=["Unternehmen"])


@router.get(
    "",
    response_model=List[UnternehmensKennzahl],
    summary="Unternehmen nach Anzahl Anzeigen (paginiert)",
)
def top_unternehmen(
    engine: Annotated[DuckDBEngine, Depends(get_engine)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> List[UnternehmensKennzahl]:
    return StatsService(engine).top_unternehmen(limit=limit, offset=offset)
