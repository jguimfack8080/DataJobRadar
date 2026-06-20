"""Endpunkte fuer Gesamtkennzahlen."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from analytics.engine.duckdb_engine import DuckDBEngine

from backend.app.core.abhaengigkeiten import get_engine
from backend.app.schemas.antworten import KennzahlenGesamt
from backend.app.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["Statistiken"])


@router.get(
    "",
    response_model=KennzahlenGesamt,
    summary="Gesamtkennzahlen des Arbeitsmarkts",
)
def kennzahlen(engine: Annotated[DuckDBEngine, Depends(get_engine)]) -> KennzahlenGesamt:
    return StatsService(engine).kennzahlen()
