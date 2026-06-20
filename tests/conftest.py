"""Geteilte pytest-Fixtures."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PROJEKT_WURZEL = Path(__file__).resolve().parent.parent

# Quellverzeichnisse als importierbare Pfade ergaenzen, damit das Test-Setup
# unabhaengig von einer pip-Installation funktioniert.
for unterordner in ("shared/python/djr_core", ".", "ingestion", "data_lake", "skills", "analytics", "backend"):
    pfad = (PROJEKT_WURZEL / unterordner).resolve()
    if str(pfad) not in sys.path:
        sys.path.insert(0, str(pfad))

# Minimale Umgebung fuer Tests setzen, damit Settings nicht aus echter .env laden.
os.environ.setdefault("ADZUNA_APP_ID", "test-id")
os.environ.setdefault("ADZUNA_APP_KEY", "test-key")
os.environ.setdefault("ADZUNA_COUNTRY", "de")
os.environ.setdefault("ADZUNA_BASE_URL", "https://api.adzuna.example")
os.environ.setdefault("ADZUNA_RESULTS_PER_PAGE", "5")
os.environ.setdefault("BACKEND_CORS_ORIGINS", "http://localhost:3000")


@pytest.fixture
def beispiel_treffer() -> list[dict]:
    return [
        {
            "id": "1001",
            "title": "Senior Data Engineer (m/w/d)",
            "description": "Wir suchen eine Person mit Python, SQL, Spark und Airflow Erfahrung. AWS ist ein Plus.",
            "company": {"display_name": "Example GmbH"},
            "location": {
                "display_name": "Berlin, Deutschland",
                "area": ["Deutschland", "Berlin", "Berlin"],
            },
            "salary_min": 70000.0,
            "salary_max": 90000.0,
            "salary_currency": "EUR",
            "contract_type": "permanent",
            "contract_time": "full_time",
            "category": {"tag": "it-jobs", "label": "IT Jobs"},
            "created": "2025-06-01T12:00:00Z",
            "redirect_url": "https://adzuna.example/anzeigen/1001",
            "latitude": 52.52,
            "longitude": 13.405,
        },
        {
            "id": "1002",
            "title": "Data Analyst",
            "description": "Analyse mit SQL, Power BI, Tableau. Kenntnisse in dbt und Snowflake erwuenscht.",
            "company": {"display_name": "Acme AG"},
            "location": {
                "display_name": "Muenchen, Deutschland",
                "area": ["Deutschland", "Bayern", "Muenchen"],
            },
            "salary_min": None,
            "salary_max": 75000.0,
            "salary_currency": "EUR",
            "contract_type": None,
            "contract_time": "full_time",
            "category": {"tag": "it-jobs", "label": "IT Jobs"},
            "created": "2025-06-02T08:00:00Z",
            "redirect_url": "https://adzuna.example/anzeigen/1002",
        },
        {
            "title": "Eintrag ohne id",
            "description": "Sollte quarantaeniert werden.",
        },
    ]
