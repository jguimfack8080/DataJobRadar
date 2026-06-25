"""Airflow-DAG: 9 Quellen -> Bronze -> Silver -> dbt Gold."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

DBT_PROJEKT_PFAD = "/opt/airflow/transform/dbt_project"

STANDARD_ARGUMENTE = {
    "owner": "Jordan Jeuna",
    "depends_on_past": False,
    "email": ["jeunaj3@gmail.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=30),
}


def _ingestion_lauf(ds: str, **kontext: Any) -> dict[str, Any]:
    from ingestion.pipeline import IngestionPipeline

    pipeline = IngestionPipeline()
    bericht = pipeline.ausfuehren(
        ausfuehrungsdatum=datetime.strptime(ds, "%Y-%m-%d").date(),
        max_seiten_pro_kategorie=5,
    )
    je_quelle = {
        q.value: {
            "geladen": b.geladene_treffer,
            "gueltig": b.gueltige_treffer,
            "quarantaene": b.quarantaenierte_treffer,
            "abgebrochen": b.abgebrochen,
            "abbruchgrund": b.abbruchgrund,
        }
        for q, b in bericht.je_quelle.items()
    }
    return {
        "kennung": bericht.korrelationskennung,
        "gesamt_geladen": bericht.gesamt_geladen(),
        "gesamt_gueltig": bericht.gesamt_gueltig(),
        "gesamt_quarantaene": bericht.gesamt_quarantaene(),
        "je_quelle": je_quelle,
    }


def _silver_transformation(ds: str, **kontext: Any) -> dict[str, Any]:
    from data_lake.silver.normalisieren import SilverTransformator

    pfad = SilverTransformator().transformieren(
        ausfuehrungsdatum=datetime.strptime(ds, "%Y-%m-%d").date(),
    )
    return {"silver_pfad": str(pfad)}


def _gold_initialisieren(**kontext: Any) -> dict[str, str]:
    from data_lake.gold.materialisierung import GoldMaterialisierung

    pfad = GoldMaterialisierung().initialisieren()
    return {"duckdb_pfad": str(pfad)}


with DAG(
    dag_id="arbeitsmarkt_data_pipeline",
    description=(
        "9 Quellen -> Bronze -> Silver -> dbt Gold (DuckDB). Laeuft viermal taeglich "
        "(00:00 / 06:00 / 12:00 / 18:00 UTC). Mehrere Laeufe pro Tag erzeugen "
        "garantiert keine Duplikate (Silver-Dedup, Staging-Dedup, dbt unique-Test)."
    ),
    default_args=STANDARD_ARGUMENTE,
    schedule="0 */6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["data-engineering", "deutschland", "multi-source"],
) as dag:
    ingest = PythonOperator(
        task_id="ingestion_lauf",
        python_callable=_ingestion_lauf,
    )

    silver = PythonOperator(
        task_id="silver_transformation",
        python_callable=_silver_transformation,
    )

    gold_init = PythonOperator(
        task_id="gold_initialisieren",
        python_callable=_gold_initialisieren,
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_PROJEKT_PFAD} && dbt deps --profiles-dir .",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJEKT_PFAD} && dbt run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PROJEKT_PFAD} && dbt test --profiles-dir .",
    )

    ingest >> silver >> gold_init >> dbt_deps >> dbt_run >> dbt_test
