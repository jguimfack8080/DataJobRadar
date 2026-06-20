"""Materialisiert die Gold-Schicht in DuckDB als analytisches Sternschema.

Diese Schicht wird durch dbt-Modelle aufgebaut. Diese Klasse uebernimmt die
Initialisierung der DuckDB-Datei und das Einspielen der Silver-Parquet-Dateien
als externe Tabelle, die dbt als Quelle verwendet.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import duckdb

from djr_core.config import DataLakeSettings, get_settings
from djr_core.logging import get_logger

_logger = get_logger("data_lake.gold")


class GoldMaterialisierung:
    """Bereitet die DuckDB-Datei fuer dbt vor."""

    def __init__(self, einstellungen: Optional[DataLakeSettings] = None) -> None:
        self._einstellungen = einstellungen or get_settings().data_lake

    def initialisieren(self) -> Path:
        duckdb_pfad = self._einstellungen.duckdb_path
        duckdb_pfad.parent.mkdir(parents=True, exist_ok=True)

        verbindung = duckdb.connect(str(duckdb_pfad))
        try:
            verbindung.execute("PRAGMA memory_limit='1GB'")
            verbindung.execute("PRAGMA threads=2")
            verbindung.execute("CREATE SCHEMA IF NOT EXISTS bronze")
            verbindung.execute("CREATE SCHEMA IF NOT EXISTS silver")
            verbindung.execute("CREATE SCHEMA IF NOT EXISTS gold")

            silver_glob = self._einstellungen.silver_path() / "stellenanzeigen" / "*.parquet"
            verbindung.execute(
                f"""
                CREATE OR REPLACE VIEW silver.stellenanzeigen AS
                SELECT * FROM read_parquet('{silver_glob}', union_by_name=true);
                """
            )
        finally:
            verbindung.close()

        _logger.info("gold_initialisiert", duckdb_pfad=str(duckdb_pfad))
        return duckdb_pfad

    def silver_partition_pruefen(self, ausfuehrungsdatum: date) -> bool:
        ziel = (
            self._einstellungen.silver_path()
            / "stellenanzeigen"
            / f"datum={ausfuehrungsdatum.isoformat()}.parquet"
        )
        return ziel.exists()
