"""Transformation der Bronze-Schicht in die Silver-Schicht.

Aufgaben:
- Vereinheitlichung von Orten, Unternehmen und Gehaltsangaben
- Deduplizierung anhand der Adzuna-ID
- Skill-Extraktion und Anreicherung
- Schreiben als partitioniertes Parquet
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

import duckdb

from djr_core.config import DataLakeSettings, get_settings
from djr_core.logging import get_logger

_logger = get_logger("data_lake.silver")


class SilverTransformator:
    """Wandelt Bronze-Parquet-Dateien in die bereinigte Silver-Schicht."""

    def __init__(
        self,
        einstellungen: Optional[DataLakeSettings] = None,
        skill_extraktor=None,
    ) -> None:
        self._einstellungen = einstellungen or get_settings().data_lake
        if skill_extraktor is None:
            from skills.extraktor import SkillExtraktor

            skill_extraktor = SkillExtraktor()
        self._skill_extraktor = skill_extraktor

    def transformieren(
        self,
        *,
        ausfuehrungsdatum: date,
        kategorien: Optional[Iterable[str]] = None,
    ) -> Path:
        """Liest Bronze-Daten, normalisiert sie und schreibt Silver-Parquet."""
        bronze_glob = (
            self._einstellungen.bronze_path()
            / "stellenanzeigen"
            / f"jahr={ausfuehrungsdatum.year:04d}"
            / f"monat={ausfuehrungsdatum.month:02d}"
            / f"tag={ausfuehrungsdatum.day:02d}"
        )

        if not bronze_glob.exists():
            raise FileNotFoundError(
                f"Keine Bronze-Daten fuer {ausfuehrungsdatum.isoformat()} gefunden"
            )

        ziel_verzeichnis = self._einstellungen.silver_path() / "stellenanzeigen"
        ziel_verzeichnis.mkdir(parents=True, exist_ok=True)
        ziel = ziel_verzeichnis / f"datum={ausfuehrungsdatum.isoformat()}.parquet"

        verbindung = duckdb.connect(":memory:")
        try:
            verbindung.execute("SET memory_limit='512MB'")
            verbindung.execute("SET threads=2")
            self._funktionen_registrieren(verbindung)

            kategorie_filter = self._kategorie_filter(kategorien)
            abfrage = self._silver_abfrage(bronze_glob, kategorie_filter)

            verbindung.execute(
                f"COPY ({abfrage.rstrip().rstrip(';')}) TO '{ziel}' "
                "(FORMAT 'parquet', COMPRESSION 'zstd', ROW_GROUP_SIZE 100000)"
            )
        finally:
            verbindung.close()

        _logger.info(
            "silver_geschrieben",
            ziel=str(ziel),
            ausfuehrungsdatum=str(ausfuehrungsdatum),
        )
        return ziel

    def _funktionen_registrieren(self, verbindung) -> None:
        skills = self._skill_extraktor

        def _skills_extrahieren(text):
            if text is None:
                return []
            return skills.extrahieren(text)

        verbindung.create_function(
            "skills_extrahieren",
            _skills_extrahieren,
            ["VARCHAR"],
            "VARCHAR[]",
        )

    @staticmethod
    def _kategorie_filter(kategorien: Optional[Iterable[str]]) -> str:
        if not kategorien:
            return ""
        liste = ", ".join(f"'{k}'" for k in kategorien)
        return f"WHERE quell_kategorie IN ({liste})"

    @staticmethod
    def _silver_abfrage(bronze_glob: Path, kategorie_filter: str) -> str:
        return f"""
        WITH roh AS (
            SELECT * FROM read_parquet('{bronze_glob}/**/*.parquet', union_by_name=true)
            {kategorie_filter}
        ),
        dedup AS (
            SELECT *
            FROM (
                SELECT *,
                       ROW_NUMBER() OVER (
                           PARTITION BY adzuna_id
                           ORDER BY abruf_zeitpunkt DESC
                       ) AS rang
                FROM roh
            )
            WHERE rang = 1
        )
        SELECT
            adzuna_id,
            titel,
            LOWER(TRIM(titel)) AS titel_normalisiert,
            beschreibung,
            unternehmen,
            LOWER(TRIM(unternehmen)) AS unternehmen_normalisiert,
            COALESCE(
                NULLIF(CASE WHEN len(standort_segmente) >= 3 THEN standort_segmente[3] ELSE NULL END, ''),
                NULLIF(CASE WHEN len(standort_segmente) >= 2 THEN standort_segmente[2] ELSE NULL END, ''),
                standort_anzeige
            ) AS stadt,
            COALESCE(NULLIF(CASE WHEN len(standort_segmente) >= 2 THEN standort_segmente[2] ELSE NULL END, ''),
                     region) AS bundesland,
            region,
            gehalt_min,
            gehalt_max,
            CASE
                WHEN gehalt_min IS NOT NULL AND gehalt_max IS NOT NULL
                    THEN (gehalt_min + gehalt_max) / 2.0
                WHEN gehalt_min IS NOT NULL THEN gehalt_min
                WHEN gehalt_max IS NOT NULL THEN gehalt_max
                ELSE NULL
            END AS gehalt_mittel,
            waehrung,
            vertragstyp,
            vertragszeit,
            kategorie_bezeichnung AS kategorie,
            veroeffentlicht_am,
            abruf_zeitpunkt,
            skills_extrahieren(beschreibung) AS skills
        FROM dedup
        """
