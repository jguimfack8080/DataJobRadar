SHELL := /bin/bash

.PHONY: help bauen starten stoppen logs backfill ingest tests format lint typcheck dbt-run dbt-test

help:
	@echo "Verfuegbare Ziele:"
	@echo "  bauen      - Docker-Images bauen"
	@echo "  starten    - Stack starten"
	@echo "  stoppen    - Stack stoppen"
	@echo "  logs       - Logs des Backends folgen"
	@echo "  ingest     - Einmaligen Ingestion-Lauf im Airflow ausloesen"
	@echo "  backfill   - Backfill-DAG ausloesen"
	@echo "  tests      - Test-Suite ausfuehren"
	@echo "  format     - ruff format"
	@echo "  lint       - ruff check"
	@echo "  typcheck   - mypy"
	@echo "  dbt-run    - dbt run im Container"
	@echo "  dbt-test   - dbt test im Container"

bauen:
	docker compose build

starten:
	docker compose up -d

stoppen:
	docker compose down

logs:
	docker compose logs -f backend

ingest:
	docker compose exec airflow-scheduler airflow dags trigger arbeitsmarkt_data_pipeline

backfill:
	docker compose exec airflow-scheduler airflow dags trigger arbeitsmarkt_backfill

tests:
	docker compose run --rm backend pytest -q

format:
	ruff format .

lint:
	ruff check .

typcheck:
	mypy backend ingestion data_lake skills analytics

dbt-run:
	docker compose exec airflow-scheduler bash -lc "cd /opt/airflow/transform/dbt_project && dbt run --profiles-dir ."

dbt-test:
	docker compose exec airflow-scheduler bash -lc "cd /opt/airflow/transform/dbt_project && dbt test --profiles-dir ."
