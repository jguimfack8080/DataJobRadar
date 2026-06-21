"""Parametrisierte SQL-Abfragen fuer die Gold-Schicht."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from analytics.engine.duckdb_engine import DuckDBEngine

_FAKT = "gold.fact_jobs"
_DIM_UNTERNEHMEN = "gold.dim_company"
_DIM_STANDORT = "gold.dim_location"
_DIM_DATUM = "gold.dim_date"
_FAKT_SKILLS = "gold.fact_skills"


@dataclass
class JobsFilter:
    suche: Optional[str] = None
    stadt: Optional[str] = None
    unternehmen: Optional[str] = None
    skill: Optional[str] = None
    nach_keyset: Optional[str] = None
    limit: int = 25


def abfrage_jobs_seite(engine: DuckDBEngine, filter: JobsFilter) -> List[dict[str, Any]]:
    bedingungen: list[str] = ["1=1"]
    parameter: list[Any] = []

    if filter.suche:
        bedingungen.append(
            "(LOWER(f.titel) LIKE ? OR LOWER(d.unternehmen_normalisiert) LIKE ?)"
        )
        muster = f"%{filter.suche.lower()}%"
        parameter.extend([muster, muster])

    if filter.stadt:
        bedingungen.append("LOWER(s.stadt) = ?")
        parameter.append(filter.stadt.lower())

    if filter.unternehmen:
        bedingungen.append("LOWER(d.unternehmen_normalisiert) = ?")
        parameter.append(filter.unternehmen.lower())

    if filter.skill:
        bedingungen.append(
            f"EXISTS (SELECT 1 FROM {_FAKT_SKILLS} fs WHERE fs.adzuna_id = f.adzuna_id AND fs.skill = ?)"
        )
        parameter.append(filter.skill)

    if filter.nach_keyset:
        bedingungen.append("(f.veroeffentlicht_am, f.adzuna_id) < (?, ?)")
        zeitstempel, kennung = _keyset_parsen(filter.nach_keyset)
        parameter.extend([zeitstempel, kennung])

    where = " AND ".join(bedingungen)
    sql = f"""
        SELECT
            f.adzuna_id AS kennung,
            f.titel,
            d.unternehmen,
            s.stadt,
            s.bundesland,
            f.gehalt_min,
            f.gehalt_max,
            f.gehalt_mittel,
            f.waehrung,
            f.vertragstyp,
            f.vertragszeit,
            f.veroeffentlicht_am,
            f.kategorie,
            f.skills,
            f.angebots_url
        FROM {_FAKT} f
        LEFT JOIN {_DIM_UNTERNEHMEN} d ON d.unternehmens_id = f.unternehmens_id
        LEFT JOIN {_DIM_STANDORT} s ON s.standort_id = f.standort_id
        WHERE {where}
        ORDER BY f.veroeffentlicht_am DESC NULLS LAST, f.adzuna_id DESC
        LIMIT ?
    """
    parameter.append(min(max(filter.limit, 1), 200))
    return engine.abfragen(sql, parameter)


def abfrage_kennzahlen_gesamt(engine: DuckDBEngine) -> dict[str, Any]:
    sql = f"""
        SELECT
            COUNT(*)::BIGINT AS anzahl_jobs,
            COUNT(DISTINCT unternehmens_id)::BIGINT AS anzahl_unternehmen,
            COUNT(DISTINCT standort_id)::BIGINT AS anzahl_standorte,
            AVG(gehalt_mittel) AS gehalt_mittel,
            MIN(veroeffentlicht_am) AS frueheste_anzeige,
            MAX(veroeffentlicht_am) AS spaeteste_anzeige
        FROM {_FAKT}
    """
    ergebnis = engine.erste(sql)
    return ergebnis or {}


def abfrage_top_skills(engine: DuckDBEngine, limit: int = 20) -> List[dict[str, Any]]:
    sql = f"""
        SELECT skill,
               COUNT(*)::BIGINT AS anzahl,
               COUNT(DISTINCT adzuna_id)::BIGINT AS anzahl_jobs
        FROM {_FAKT_SKILLS}
        GROUP BY skill
        ORDER BY anzahl DESC
        LIMIT ?
    """
    return engine.abfragen(sql, [limit])


def abfrage_top_unternehmen(engine: DuckDBEngine, limit: int = 20) -> List[dict[str, Any]]:
    sql = f"""
        SELECT d.unternehmen,
               COUNT(*)::BIGINT AS anzahl_jobs,
               AVG(f.gehalt_mittel) AS gehalt_mittel
        FROM {_FAKT} f
        JOIN {_DIM_UNTERNEHMEN} d ON d.unternehmens_id = f.unternehmens_id
        WHERE d.unternehmen IS NOT NULL
        GROUP BY d.unternehmen
        ORDER BY anzahl_jobs DESC
        LIMIT ?
    """
    return engine.abfragen(sql, [limit])


def abfrage_top_staedte(engine: DuckDBEngine, limit: int = 20) -> List[dict[str, Any]]:
    sql = f"""
        SELECT s.stadt,
               s.bundesland,
               COUNT(*)::BIGINT AS anzahl_jobs,
               AVG(f.gehalt_mittel) AS gehalt_mittel
        FROM {_FAKT} f
        JOIN {_DIM_STANDORT} s ON s.standort_id = f.standort_id
        WHERE s.stadt IS NOT NULL
        GROUP BY s.stadt, s.bundesland
        ORDER BY anzahl_jobs DESC
        LIMIT ?
    """
    return engine.abfragen(sql, [limit])


def abfrage_zeitreihe_neue_jobs(engine: DuckDBEngine, tage: int = 30) -> List[dict[str, Any]]:
    sql = f"""
        SELECT CAST(veroeffentlicht_am AS DATE) AS tag,
               COUNT(*)::BIGINT AS anzahl
        FROM {_FAKT}
        WHERE veroeffentlicht_am >= CURRENT_DATE - INTERVAL '{int(tage)}' DAY
        GROUP BY tag
        ORDER BY tag ASC
    """
    return engine.abfragen(sql)


def abfrage_gehaltsverteilung(engine: DuckDBEngine, gruppierung: str = "kategorie") -> List[dict[str, Any]]:
    erlaubt = {"kategorie", "stadt", "bundesland"}
    if gruppierung not in erlaubt:
        raise ValueError(f"Unerlaubte Gruppierung: {gruppierung}")
    spalte = {
        "kategorie": "f.kategorie",
        "stadt": "s.stadt",
        "bundesland": "s.bundesland",
    }[gruppierung]
    sql = f"""
        SELECT {spalte} AS gruppe,
               COUNT(*)::BIGINT AS anzahl,
               APPROX_QUANTILE(f.gehalt_mittel, 0.25) AS gehalt_p25,
               APPROX_QUANTILE(f.gehalt_mittel, 0.5)  AS gehalt_median,
               APPROX_QUANTILE(f.gehalt_mittel, 0.75) AS gehalt_p75,
               AVG(f.gehalt_mittel) AS gehalt_mittel
        FROM {_FAKT} f
        LEFT JOIN {_DIM_STANDORT} s ON s.standort_id = f.standort_id
        WHERE f.gehalt_mittel IS NOT NULL AND {spalte} IS NOT NULL
        GROUP BY {spalte}
        ORDER BY anzahl DESC
        LIMIT 25
    """
    return engine.abfragen(sql)


def _keyset_parsen(wert: str) -> tuple[str, str]:
    parts = wert.split("|", 1)
    if len(parts) != 2:
        raise ValueError("Keyset muss im Format <iso8601>|<id> uebergeben werden")
    return parts[0], parts[1]
