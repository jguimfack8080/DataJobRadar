"""Integrationstests fuer die DuckDB-Analyse-Engine."""
import duckdb

from analytics.engine.duckdb_engine import DuckDBEngine
from djr_core.config import DataLakeSettings


def _datenbank_befuellen(pfad) -> None:
    verbindung = duckdb.connect(str(pfad))
    try:
        verbindung.execute("CREATE SCHEMA gold")
        verbindung.execute(
            """
            CREATE TABLE gold.fact_jobs (
                adzuna_id VARCHAR,
                unternehmens_id VARCHAR,
                standort_id VARCHAR,
                titel VARCHAR,
                kategorie VARCHAR,
                vertragstyp VARCHAR,
                vertragszeit VARCHAR,
                gehalt_min DOUBLE,
                gehalt_max DOUBLE,
                gehalt_mittel DOUBLE,
                waehrung VARCHAR,
                veroeffentlicht_am TIMESTAMP,
                abruf_zeitpunkt TIMESTAMP,
                skills VARCHAR[]
            );
            """
        )
        verbindung.execute(
            "INSERT INTO gold.fact_jobs VALUES ('1','u1','s1','Data Engineer','it','permanent','full',60000,80000,70000,'EUR',TIMESTAMP '2025-06-01 12:00:00',TIMESTAMP '2025-06-01 12:30:00',['Python','SQL'])"
        )
        verbindung.execute(
            "CREATE TABLE gold.dim_company AS SELECT 'u1' AS unternehmens_id, 'Example GmbH' AS unternehmen, 'example gmbh' AS unternehmen_normalisiert"
        )
        verbindung.execute(
            "CREATE TABLE gold.dim_location AS SELECT 's1' AS standort_id, 'Berlin' AS stadt, 'Berlin' AS bundesland, 'Deutschland' AS region"
        )
        verbindung.execute(
            "CREATE TABLE gold.fact_skills (adzuna_id VARCHAR, skill VARCHAR, gewichtung INTEGER)"
        )
        verbindung.execute("INSERT INTO gold.fact_skills VALUES ('1','Python',1),('1','SQL',1)")
    finally:
        verbindung.close()


def test_kennzahlen_abfrage(tmp_path) -> None:
    pfad = tmp_path / "djr.duckdb"
    _datenbank_befuellen(pfad)
    engine = DuckDBEngine(DataLakeSettings(data_lake_root=tmp_path, duckdb_path=pfad), nur_lesen=True)
    try:
        from analytics.queries.kennzahlen import abfrage_kennzahlen_gesamt, abfrage_top_skills

        kennzahlen = abfrage_kennzahlen_gesamt(engine)
        assert kennzahlen["anzahl_jobs"] == 1
        skills = abfrage_top_skills(engine, limit=5)
        skill_namen = {eintrag["skill"] for eintrag in skills}
        assert {"Python", "SQL"}.issubset(skill_namen)
    finally:
        engine.schliessen()
