"""Endpunkte fuer Skill-Statistiken."""
from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from analytics.engine.duckdb_engine import DuckDBEngine

from backend.app.core.abhaengigkeiten import get_engine
from backend.app.schemas.antworten import SkillKennzahl
from backend.app.services.stats_service import StatsService

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get(
    "",
    response_model=List[SkillKennzahl],
    summary="Top Skills nach Anzahl Nennungen (paginiert)",
)
def top_skills(
    engine: Annotated[DuckDBEngine, Depends(get_engine)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> List[SkillKennzahl]:
    return StatsService(engine).top_skills(limit=limit, offset=offset)
