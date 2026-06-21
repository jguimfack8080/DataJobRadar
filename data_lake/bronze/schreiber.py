"""Schreibt Roh- und Quarantaenedaten in die Bronze-Schicht (Parquet).

Partitionierung: bronze/<datensatz>/quelle=Q/jahr=YYYY/monat=MM/tag=DD/kategorie=KAT/seite-<n>-<korrelation>.parquet
Format: Apache Parquet mit Zstd-Kompression fuer hohe Verdichtung.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import orjson
import pyarrow as pa
import pyarrow.parquet as pq

from djr_core.config import DataLakeSettings, get_settings
from djr_core.logging import get_logger
from djr_core.models import JobQuelle, RohStellenanzeige

_logger = get_logger("data_lake.bronze")


class BronzeSchreiber:
    """Verantwortlich fuer das Persistieren validierter Rohdaten."""

    KOMPRESSION = "zstd"
    KOMPRESSIONS_LEVEL = 7

    def __init__(self, einstellungen: Optional[DataLakeSettings] = None) -> None:
        self._einstellungen = einstellungen or get_settings().data_lake

    def schreiben(
        self,
        *,
        anzeigen: Sequence[RohStellenanzeige],
        quelle: JobQuelle,
        ausfuehrungsdatum: date,
        kategorie: str,
        seite: int,
        korrelationskennung: str,
    ) -> Path:
        if not anzeigen:
            raise ValueError("Es wurden keine Anzeigen zum Schreiben uebergeben")

        pfad = self._partitionspfad(
            datensatz="stellenanzeigen",
            quelle=quelle,
            ausfuehrungsdatum=ausfuehrungsdatum,
            kategorie=kategorie,
        )
        pfad.mkdir(parents=True, exist_ok=True)
        ziel = pfad / f"seite-{seite:03d}-{korrelationskennung[:8]}.parquet"

        tabelle = self._anzeigen_in_tabelle(anzeigen)
        pq.write_table(
            tabelle,
            ziel,
            compression=self.KOMPRESSION,
            compression_level=self.KOMPRESSIONS_LEVEL,
            use_dictionary=True,
            write_statistics=True,
        )
        _logger.info(
            "bronze_schicht_geschrieben",
            pfad=str(ziel),
            anzahl=len(anzeigen),
            quelle=quelle.value,
            kategorie=kategorie,
            seite=seite,
        )
        return ziel

    def quarantaene_schreiben(
        self,
        *,
        rohdaten: Iterable[dict],
        quelle: JobQuelle,
        ausfuehrungsdatum: date,
        kategorie: str,
        seite: int,
        korrelationskennung: str,
    ) -> Optional[Path]:
        rohdaten = list(rohdaten)
        if not rohdaten:
            return None

        pfad = self._partitionspfad(
            datensatz="quarantaene",
            quelle=quelle,
            ausfuehrungsdatum=ausfuehrungsdatum,
            kategorie=kategorie,
        )
        pfad.mkdir(parents=True, exist_ok=True)
        ziel = pfad / f"seite-{seite:03d}-{korrelationskennung[:8]}.jsonl"

        with ziel.open("wb") as datei:
            for eintrag in rohdaten:
                datei.write(orjson.dumps(eintrag, default=str))
                datei.write(b"\n")
        _logger.warning(
            "quarantaene_geschrieben",
            pfad=str(ziel),
            anzahl=len(rohdaten),
            quelle=quelle.value,
            kategorie=kategorie,
            seite=seite,
        )
        return ziel

    def _partitionspfad(
        self,
        *,
        datensatz: str,
        quelle: JobQuelle,
        ausfuehrungsdatum: date,
        kategorie: str,
    ) -> Path:
        kategorie_sicher = kategorie.replace("/", "_").replace("\\", "_")
        return (
            self._einstellungen.bronze_path()
            / datensatz
            / f"quelle={quelle.value}"
            / f"jahr={ausfuehrungsdatum.year:04d}"
            / f"monat={ausfuehrungsdatum.month:02d}"
            / f"tag={ausfuehrungsdatum.day:02d}"
            / f"kategorie={kategorie_sicher}"
        )

    @staticmethod
    def _anzeigen_in_tabelle(anzeigen: Sequence[RohStellenanzeige]) -> pa.Table:
        # `model_dump` schliesst computed fields ein (job_id, dedup_signatur, quellen_prioritaet).
        zeilen = [anzeige.model_dump(mode="python") for anzeige in anzeigen]
        # Enum -> String
        for zeile in zeilen:
            if "quelle" in zeile:
                zeile["quelle"] = (
                    zeile["quelle"].value if hasattr(zeile["quelle"], "value") else str(zeile["quelle"])
                )
        spalten: dict[str, List] = {}
        for zeile in zeilen:
            for feld, wert in zeile.items():
                spalten.setdefault(feld, []).append(wert)
        return pa.table(spalten)
