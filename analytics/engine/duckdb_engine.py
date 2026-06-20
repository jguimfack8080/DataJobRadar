"""DuckDB-Engine fuer das Backend.

Die Engine ist prozessintern (kein separater Datenbankserver) und liefert eine
threadsichere Schnittstelle ueber kurzlebige Verbindungen. Resultate werden als
typisierte Datenstrukturen zurueckgegeben.
"""
from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, List, Optional, Sequence

import duckdb

from djr_core.config import DataLakeSettings, get_settings
from djr_core.logging import get_logger

_logger = get_logger("analytics.engine")


class AnalyticsEngine:
    """Abstrakte Schnittstelle fuer Analyse-Engines."""

    def abfragen(self, sql: str, parameter: Optional[Sequence[Any]] = None) -> List[dict[str, Any]]:
        raise NotImplementedError


class DuckDBEngine(AnalyticsEngine):
    """DuckDB-basierte Analyse-Engine.

    Verwendet eine prozessweite Verbindung mit einem Lock fuer schreibende
    Operationen. Lesende Operationen koennen kurzlebige Verbindungen anlegen,
    um die zentrale Verbindung nicht zu blockieren.
    """

    def __init__(
        self,
        einstellungen: Optional[DataLakeSettings] = None,
        nur_lesen: bool = True,
    ) -> None:
        self._einstellungen = einstellungen or get_settings().data_lake
        self._nur_lesen = nur_lesen
        self._sperre = threading.Lock()
        self._verbindung: Optional[duckdb.DuckDBPyConnection] = None

    @property
    def datenbank_pfad(self) -> Path:
        return self._einstellungen.duckdb_path

    def verbindung_oeffnen(self) -> duckdb.DuckDBPyConnection:
        if self._verbindung is None:
            self.datenbank_pfad.parent.mkdir(parents=True, exist_ok=True)
            self._verbindung = duckdb.connect(
                str(self.datenbank_pfad),
                read_only=self._nur_lesen and self.datenbank_pfad.exists(),
            )
            self._verbindung.execute("PRAGMA memory_limit='512MB'")
            self._verbindung.execute("PRAGMA threads=2")
        return self._verbindung

    def schliessen(self) -> None:
        if self._verbindung is not None:
            self._verbindung.close()
            self._verbindung = None

    @contextmanager
    def cursor(self) -> Iterator[duckdb.DuckDBPyConnection]:
        verbindung = self.verbindung_oeffnen()
        cursor = verbindung.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def abfragen(
        self,
        sql: str,
        parameter: Optional[Sequence[Any]] = None,
    ) -> List[dict[str, Any]]:
        with self._sperre, self.cursor() as cursor:
            try:
                if parameter:
                    relation = cursor.execute(sql, list(parameter))
                else:
                    relation = cursor.execute(sql)
                spalten = [beschreibung[0] for beschreibung in relation.description or []]
                zeilen = relation.fetchall()
            except duckdb.Error as fehler:
                _logger.error("duckdb_abfrage_fehler", sql=sql[:200], fehler=str(fehler))
                raise
        return [dict(zip(spalten, zeile)) for zeile in zeilen]

    def erste(self, sql: str, parameter: Optional[Sequence[Any]] = None) -> Optional[dict[str, Any]]:
        ergebnis = self.abfragen(sql, parameter)
        return ergebnis[0] if ergebnis else None
