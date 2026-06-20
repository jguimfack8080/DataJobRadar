"""Endpunkte fuer Staedte."""
from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from analytics.engine.duckdb_engine import DuckDBEngine

from backend.app.core.abhaengigkeiten import get_engine
from backend.app.schemas.antworten import StadtKennzahl
from backend.app.services.stats_service import StatsService

router = APIRouter(prefix="/cities", tags=["Staedte"])


@router.get(
    "",
    response_model=List[StadtKennzahl],
    summary="Top Staedte nach Anzahl Anzeigen",
)
def top_staedte(
    engine: Annotated[DuckDBEngine, Depends(get_engine)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> List[StadtKennzahl]:
    return StatsService(engine).top_staedte(limit=limit)
