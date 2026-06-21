"""Parametrisierte SQL-Abfragen fuer die Gold-Schicht."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from analytics.engine.duckdb_engine import DuckDBEngine

_FAKT = "gold.fact_jobs"
_DIM_UNTERNEHMEN = "gold.dim_company"
_DIM_STANDORT = "gold.dim_location"
_DIM_DATUM = "gold.dim_date"
_FAKT_SKILLS = "gold.fact_skills"


@dataclass
class JobsFilter:
    """Vollstaendige Filterspezifikation fuer die Jobs-Abfrage."""

    suche: Optional[str] = None
    stadt: Optional[str] = None
    bundesland: Optional[str] = None
    unternehmen: Optional[str] = None
    kategorie: Optional[str] = None
    vertragstyp: Optional[str] = None
    vertragszeit: Optional[str] = None
    waehrung: Optional[str] = None
    gehalt_min: Optional[float] = None
    gehalt_max: Optional[float] = None
    nur_mit_gehalt: bool = False
    veroeffentlicht_seit: Optional[str] = None
    veroeffentlicht_bis: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    quellen: List[str] = field(default_factory=list)
    nach_keyset: Optional[str] = None
    limit: int = 25


def abfrage_jobs_seite(engine: DuckDBEngine, filter: JobsFilter) -> List[dict[str, Any]]:
    bedingungen: list[str] = ["1=1"]
    parameter: list[Any] = []

    if filter.suche:
        bedingungen.append(
            "(LOWER(f.titel) LIKE ? OR LOWER(COALESCE(d.unternehmen_normalisiert,'')) LIKE ?)"
        )
        muster = f"%{filter.suche.lower()}%"
        parameter.extend([muster, muster])

    if filter.stadt:
        bedingungen.append("LOWER(s.stadt) = ?")
        parameter.append(filter.stadt.lower())

    if filter.bundesland:
        bedingungen.append("LOWER(s.bundesland) = ?")
        parameter.append(filter.bundesland.lower())

    if filter.unternehmen:
        bedingungen.append("LOWER(d.unternehmen_normalisiert) = ?")
        parameter.append(filter.unternehmen.lower())

    if filter.kategorie:
        bedingungen.append("LOWER(f.kategorie) = ?")
        parameter.append(filter.kategorie.lower())

    if filter.vertragstyp:
        bedingungen.append("LOWER(f.vertragstyp) = ?")
        parameter.append(filter.vertragstyp.lower())

    if filter.vertragszeit:
        bedingungen.append("LOWER(f.vertragszeit) = ?")
        parameter.append(filter.vertragszeit.lower())

    if filter.waehrung:
        bedingungen.append("UPPER(f.waehrung) = ?")
        parameter.append(filter.waehrung.upper())

    if filter.gehalt_min is not None:
        bedingungen.append("COALESCE(f.gehalt_mittel, f.gehalt_max) >= ?")
        parameter.append(float(filter.gehalt_min))

    if filter.gehalt_max is not None:
        bedingungen.append("COALESCE(f.gehalt_mittel, f.gehalt_min) <= ?")
        parameter.append(float(filter.gehalt_max))

    if filter.nur_mit_gehalt:
        bedingungen.append("f.gehalt_mittel IS NOT NULL")

    if filter.veroeffentlicht_seit:
        bedingungen.append("f.veroeffentlicht_am >= CAST(? AS TIMESTAMP)")
        parameter.append(filter.veroeffentlicht_seit)

    if filter.veroeffentlicht_bis:
        bedingungen.append("f.veroeffentlicht_am <= CAST(? AS TIMESTAMP)")
        parameter.append(filter.veroeffentlicht_bis)

    if filter.skills:
        for skill in filter.skills:
            bedingungen.append(
                f"EXISTS (SELECT 1 FROM {_FAKT_SKILLS} fs WHERE fs.job_id = f.job_id AND fs.skill = ?)"
            )
            parameter.append(skill)

    if filter.quellen:
        platzhalter = ",".join("?" for _ in filter.quellen)
        bedingungen.append(f"LOWER(f.quelle) IN ({platzhalter})")
        parameter.extend(q.lower() for q in filter.quellen)

    if filter.nach_keyset:
        bedingungen.append(
            "(f.veroeffentlicht_am, f.job_id) < (CAST(? AS TIMESTAMP), CAST(? AS VARCHAR))"
        )
        zeitstempel, kennung = _keyset_parsen(filter.nach_keyset)
        parameter.extend([zeitstempel, kennung])

    where = " AND ".join(bedingungen)
    sql = f"""
        SELECT
            f.job_id AS kennung,
            f.quelle,
            f.quell_id,
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
        ORDER BY f.veroeffentlicht_am DESC NULLS LAST, f.job_id DESC
        LIMIT ?
    """
    parameter.append(min(max(filter.limit, 1), 200))
    return engine.abfragen(sql, parameter)


def abfrage_filter_facetten(engine: DuckDBEngine) -> dict[str, list[str]]:
    sql_kategorien = f"SELECT DISTINCT kategorie FROM {_FAKT} WHERE kategorie IS NOT NULL ORDER BY kategorie"
    sql_vertragstyp = (
        f"SELECT DISTINCT vertragstyp FROM {_FAKT} "
        "WHERE vertragstyp IS NOT NULL AND vertragstyp <> '' ORDER BY vertragstyp"
    )
    sql_vertragszeit = (
        f"SELECT DISTINCT vertragszeit FROM {_FAKT} "
        "WHERE vertragszeit IS NOT NULL AND vertragszeit <> '' ORDER BY vertragszeit"
    )
    sql_bundeslaender = (
        f"SELECT DISTINCT s.bundesland FROM {_DIM_STANDORT} s "
        "WHERE s.bundesland IS NOT NULL AND s.bundesland <> '' AND s.bundesland <> 'unbekannt' "
        "ORDER BY s.bundesland"
    )
    sql_staedte = (
        f"SELECT s.stadt, COUNT(*)::BIGINT AS n FROM {_FAKT} f "
        f"JOIN {_DIM_STANDORT} s ON s.standort_id = f.standort_id "
        "WHERE s.stadt IS NOT NULL AND s.stadt <> '' AND s.stadt <> 'unbekannt' "
        "GROUP BY s.stadt ORDER BY n DESC LIMIT 50"
    )
    sql_skills = (
        f"SELECT skill, COUNT(*)::BIGINT AS n FROM {_FAKT_SKILLS} "
        "GROUP BY skill ORDER BY n DESC LIMIT 50"
    )
    sql_quellen = (
        f"SELECT quelle, COUNT(*)::BIGINT AS n FROM {_FAKT} "
        "WHERE quelle IS NOT NULL GROUP BY quelle ORDER BY n DESC"
    )

    return {
        "kategorien": [str(zeile["kategorie"]) for zeile in engine.abfragen(sql_kategorien)],
        "vertragstypen": [str(z["vertragstyp"]) for z in engine.abfragen(sql_vertragstyp)],
        "vertragszeiten": [str(z["vertragszeit"]) for z in engine.abfragen(sql_vertragszeit)],
        "bundeslaender": [str(z["bundesland"]) for z in engine.abfragen(sql_bundeslaender)],
        "staedte": [str(z["stadt"]) for z in engine.abfragen(sql_staedte)],
        "skills": [str(z["skill"]) for z in engine.abfragen(sql_skills)],
        "quellen": [str(z["quelle"]) for z in engine.abfragen(sql_quellen)],
    }


def abfrage_kennzahlen_gesamt(engine: DuckDBEngine) -> dict[str, Any]:
    sql = f"""
        SELECT
            COUNT(*)::BIGINT AS anzahl_jobs,
            COUNT(DISTINCT unternehmens_id)::BIGINT AS anzahl_unternehmen,
            COUNT(DISTINCT standort_id)::BIGINT AS anzahl_standorte,
            COUNT(DISTINCT quelle)::BIGINT AS anzahl_quellen,
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
               COUNT(DISTINCT job_id)::BIGINT AS anzahl_jobs
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
    erlaubt = {"kategorie", "stadt", "bundesland", "quelle"}
    if gruppierung not in erlaubt:
        raise ValueError(f"Unerlaubte Gruppierung: {gruppierung}")
    spalte = {
        "kategorie": "f.kategorie",
        "stadt": "s.stadt",
        "bundesland": "s.bundesland",
        "quelle": "f.quelle",
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


def abfrage_quellen_verteilung(engine: DuckDBEngine) -> List[dict[str, Any]]:
    """Wie viele Stellen kommen aus welcher Quelle."""
    sql = f"""
        SELECT quelle,
               COUNT(*)::BIGINT AS anzahl_jobs,
               AVG(gehalt_mittel) AS gehalt_mittel
        FROM {_FAKT}
        WHERE quelle IS NOT NULL
        GROUP BY quelle
        ORDER BY anzahl_jobs DESC
    """
    return engine.abfragen(sql)


def _keyset_parsen(wert: str) -> tuple[str, str]:
    parts = wert.split("|", 1)
    if len(parts) != 2:
        raise ValueError("Keyset muss im Format <iso8601>|<id> uebergeben werden")
    zeitstempel = parts[0].replace(" ", "+")
    return zeitstempel, parts[1]
