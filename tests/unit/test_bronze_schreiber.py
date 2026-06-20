"""Tests fuer den Bronze-Schreiber."""
from datetime import date

import pyarrow.parquet as pq

from data_lake.bronze.schreiber import BronzeSchreiber
from djr_core.config import DataLakeSettings
from ingestion.validation.schemata import validiere_adzuna_treffer


def test_bronze_schreibt_parquet(tmp_path, beispiel_treffer) -> None:
    einstellungen = DataLakeSettings(data_lake_root=tmp_path, duckdb_path=tmp_path / "djr.duckdb")
    schreiber = BronzeSchreiber(einstellungen=einstellungen)

    ergebnis = validiere_adzuna_treffer(beispiel_treffer, quell_kategorie="data_engineer")
    pfad = schreiber.schreiben(
        anzeigen=ergebnis.gueltig,
        ausfuehrungsdatum=date(2025, 6, 1),
        kategorie="data_engineer",
        seite=1,
        korrelationskennung="aaaabbbbcccc",
    )

    assert pfad.exists()
    tabelle = pq.read_table(pfad)
    assert tabelle.num_rows == ergebnis.anzahl_gueltig
    assert "adzuna_id" in tabelle.column_names

    quarantaene = schreiber.quarantaene_schreiben(
        rohdaten=ergebnis.quarantaene,
        ausfuehrungsdatum=date(2025, 6, 1),
        kategorie="data_engineer",
        seite=1,
        korrelationskennung="aaaabbbbcccc",
    )
    assert quarantaene is not None
    assert quarantaene.exists()
