"""Endpunkte fuer Stellenanzeigen mit umfassenden Filtern."""
from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query

from analytics.engine.duckdb_engine import DuckDBEngine

from backend.app.core.abhaengigkeiten import get_engine
from backend.app.schemas.antworten import (
    FilterFacetten,
    JobsSeite,
    QuellenVerteilungEintrag,
)
from backend.app.services.jobs_service import JobsService

router = APIRouter(prefix="/jobs", tags=["Stellenanzeigen"])


@router.get(
    "",
    response_model=JobsSeite,
    summary="Stellenanzeigen abrufen",
    description=(
        "Liefert eine seitenweise Liste mit umfassenden Filtern. Unterstuetzt "
        "Volltextsuche, Geographie, Unternehmen, Kategorie, Vertrag, Gehalt, "
        "Datumsbereich, Skill-Mehrfachauswahl, Quellen-Filter und Keyset-Pagination."
    ),
)
def jobs_auflisten(
    engine: Annotated[DuckDBEngine, Depends(get_engine)],
    suche: Annotated[Optional[str], Query(min_length=1, max_length=120)] = None,
    stadt: Annotated[Optional[str], Query(min_length=1, max_length=120)] = None,
    bundesland: Annotated[Optional[str], Query(min_length=1, max_length=80)] = None,
    unternehmen: Annotated[Optional[str], Query(min_length=1, max_length=160)] = None,
    kategorie: Annotated[Optional[str], Query(min_length=1, max_length=120)] = None,
    vertragstyp: Annotated[Optional[str], Query(min_length=1, max_length=40)] = None,
    vertragszeit: Annotated[Optional[str], Query(min_length=1, max_length=40)] = None,
    waehrung: Annotated[Optional[str], Query(min_length=3, max_length=3)] = None,
    gehalt_min: Annotated[Optional[float], Query(ge=0)] = None,
    gehalt_max: Annotated[Optional[float], Query(ge=0)] = None,
    nur_mit_gehalt: Annotated[bool, Query()] = False,
    veroeffentlicht_seit: Annotated[Optional[str], Query()] = None,
    veroeffentlicht_bis: Annotated[Optional[str], Query()] = None,
    skill: Annotated[Optional[List[str]], Query(description="Skill, mehrfach (UND)")] = None,
    quelle: Annotated[Optional[List[str]], Query(description="Quellen, mehrfach (ODER)")] = None,
    nach: Annotated[Optional[str], Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> JobsSeite:
    service = JobsService(engine)
    return service.seite_laden(
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
        skills=skill,
        quellen=quelle,
        nach_keyset=nach,
        limit=limit,
    )


@router.get(
    "/facetten",
    response_model=FilterFacetten,
    summary="Verfuegbare Filterwerte (Facetten)",
)
def jobs_facetten(engine: Annotated[DuckDBEngine, Depends(get_engine)]) -> FilterFacetten:
    return FilterFacetten(**JobsService(engine).facetten())


@router.get(
    "/quellen",
    response_model=List[QuellenVerteilungEintrag],
    summary="Verteilung der Stellen ueber die Quellen",
)
def jobs_quellen(engine: Annotated[DuckDBEngine, Depends(get_engine)]) -> List[QuellenVerteilungEintrag]:
    return JobsService(engine).quellen_verteilung()
