"""End-to-End-Tests des FastAPI-Backends gegen eine echte DuckDB."""
import duckdb
import pytest
from fastapi.testclient import TestClient

from backend.app.core.abhaengigkeiten import engine_singleton, get_engine
from analytics.engine.duckdb_engine import DuckDBEngine
from djr_core.config import DataLakeSettings


@pytest.fixture
def klient(tmp_path):
    pfad = tmp_path / "djr.duckdb"
    verbindung = duckdb.connect(str(pfad))
    verbindung.execute("CREATE SCHEMA gold")
    verbindung.execute(
        """
        CREATE TABLE gold.fact_jobs AS
        SELECT
            '1' AS adzuna_id,
            'u1' AS unternehmens_id,
            's1' AS standort_id,
            'Data Engineer' AS titel,
            'beschreibung' AS beschreibung,
            'it' AS kategorie,
            'permanent' AS vertragstyp,
            'full_time' AS vertragszeit,
            60000.0 AS gehalt_min,
            80000.0 AS gehalt_max,
            70000.0 AS gehalt_mittel,
            'EUR' AS waehrung,
            TIMESTAMP '2025-06-01 12:00:00' AS veroeffentlicht_am,
            TIMESTAMP '2025-06-01 12:30:00' AS abruf_zeitpunkt,
            ['Python','SQL'] AS skills;
        """
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
    verbindung.close()

    engine_singleton.cache_clear()
    test_engine = DuckDBEngine(DataLakeSettings(data_lake_root=tmp_path, duckdb_path=pfad), nur_lesen=True)

    from backend.app.main import app_erzeugen
    from backend.app.core.cache import resultcache_leeren

    resultcache_leeren()
    app = app_erzeugen()
    app.dependency_overrides[get_engine] = lambda: test_engine
    klient = TestClient(app)
    yield klient
    test_engine.schliessen()
    engine_singleton.cache_clear()


def test_health(klient) -> None:
    antwort = klient.get("/api/v1/health")
    assert antwort.status_code == 200
    assert antwort.json() == {"status": "ok"}


def test_stats(klient) -> None:
    antwort = klient.get("/api/v1/stats")
    assert antwort.status_code == 200
    daten = antwort.json()
    assert daten["anzahl_jobs"] == 1
    assert daten["anzahl_unternehmen"] == 1


def test_jobs_liste(klient) -> None:
    antwort = klient.get("/api/v1/jobs", params={"limit": 5})
    assert antwort.status_code == 200
    seite = antwort.json()
    assert seite["treffer"][0]["titel"] == "Data Engineer"
    assert "Python" in seite["treffer"][0]["skills"]


def test_skills(klient) -> None:
    antwort = klient.get("/api/v1/skills", params={"limit": 5})
    assert antwort.status_code == 200
    eintraege = antwort.json()
    namen = {eintrag["skill"] for eintrag in eintraege}
    assert "Python" in namen
    assert "SQL" in namen


def test_korrelationskennung_header(klient) -> None:
    antwort = klient.get("/api/v1/health")
    assert "X-Korrelations-Kennung" in antwort.headers
