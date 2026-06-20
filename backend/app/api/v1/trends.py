"""Endpunkte fuer zeitliche Trends und Verteilungen."""
from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from analytics.engine.duckdb_engine import DuckDBEngine

from backend.app.core.abhaengigkeiten import get_engine
from backend.app.schemas.antworten import GehaltsverteilungEintrag, ZeitreihePunkt
from backend.app.services.stats_service import StatsService

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.get(
    "/zeitreihe",
    response_model=List[ZeitreihePunkt],
    summary="Zeitreihe der veroeffentlichten Stellenanzeigen",
)
def zeitreihe(
    engine: Annotated[DuckDBEngine, Depends(get_engine)],
    tage: Annotated[int, Query(ge=1, le=365)] = 30,
) -> List[ZeitreihePunkt]:
    return StatsService(engine).zeitreihe(tage=tage)


@router.get(
    "/gehaltsverteilung",
    response_model=List[GehaltsverteilungEintrag],
    summary="Gehaltsverteilung nach Gruppierung",
)
def gehaltsverteilung(
    engine: Annotated[DuckDBEngine, Depends(get_engine)],
    gruppierung: Annotated[str, Query(pattern="^(kategorie|stadt|bundesland)$")] = "kategorie",
) -> List[GehaltsverteilungEintrag]:
    return StatsService(engine).gehaltsverteilung(gruppierung=gruppierung)
