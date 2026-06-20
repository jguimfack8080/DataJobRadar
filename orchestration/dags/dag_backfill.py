"""Airflow-DAG fuer den manuellen Backfill ueber mehrere Tage."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from airflow import DAG
from airflow.decorators import task

STANDARD_ARGUMENTE = {
    "owner": "Jordan Jeuna",
    "depends_on_past": False,
    "email": ["jeunaj3@gmail.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(hours=2),
}


with DAG(
    dag_id="arbeitsmarkt_backfill",
    description="Backfill mehrerer Tage fuer initialen Datenbestand",
    default_args=STANDARD_ARGUMENTE,
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["backfill", "adzuna"],
    params={
        "von": "2025-01-01",
        "bis": "2025-01-07",
        "seiten_pro_kategorie": 5,
    },
) as dag:

    @task
    def backfill(params: dict[str, Any]) -> dict[str, Any]:
        from ingestion.pipeline import IngestionPipeline

        von = datetime.strptime(params["von"], "%Y-%m-%d").date()
        bis = datetime.strptime(params["bis"], "%Y-%m-%d").date()
        seiten = int(params.get("seiten_pro_kategorie") or 5)

        pipeline = IngestionPipeline()
        berichte: list[dict[str, Any]] = []
        kursor = von
        while kursor <= bis:
            bericht = pipeline.ausfuehren(
                ausfuehrungsdatum=kursor,
                max_seiten_pro_kategorie=seiten,
            )
            berichte.append(
                {
                    "ausfuehrungsdatum": kursor.isoformat(),
                    "geladen": bericht.geladene_treffer,
                    "gueltig": bericht.gueltige_treffer,
                    "quarantaene": bericht.quarantaenierte_treffer,
                    "abgebrochen": bericht.abgebrochen,
                }
            )
            if bericht.abgebrochen:
                break
            kursor += timedelta(days=1)
        return {"berichte": berichte}

    backfill()
