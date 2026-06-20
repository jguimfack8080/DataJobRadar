# Architekturuebersicht

## Schichtenmodell

| Schicht       | Verantwortung                                              | Technologie               |
|---------------|------------------------------------------------------------|---------------------------|
| Ingestion     | Adzuna-Aufrufe, Schemavalidierung, Quarantaene             | httpx, tenacity, pydantic |
| Bronze        | Rohdaten unveraendert, partitioniert nach Datum/Kategorie  | Parquet (Zstd)            |
| Silver        | Bereinigung, Deduplizierung, Skill-Extraktion              | DuckDB SQL                |
| Gold          | Sternschema fuer Analytics                                 | dbt-duckdb                |
| Analytics API | Abfragen, Caching, Rate Limiting, Fehlermodelle            | FastAPI, cachetools       |
| Dashboard     | Visualisierung, Filter, Drilldowns                         | Next.js, Tailwind, Recharts |
| Orchestrierung | Idempotente Tagespipeline und Backfill                    | Apache Airflow            |

## Wesentliche Entscheidungen

- **DuckDB als analytische Engine.** Prozessintern, ohne Server, sehr schnell bei
  aggregationslastigen Abfragen auf Parquet. Sternschema wird ueber dbt
  materialisiert. Begruendung in
  [docs/adr/0001-duckdb-als-warehouse.md](adr/0001-duckdb-als-warehouse.md).
- **Statischer Frontend-Export, vom Backend ausgeliefert.** Genau ein Prozess
  hinter der bestehenden Nginx; minimaler Footprint. Begruendung in
  [docs/adr/0002-frontend-statisch-im-backend.md](adr/0002-frontend-statisch-im-backend.md).
- **Airflow mit LocalExecutor.** Kein Celery, kein Redis. Reicht fuer eine
  taegliche Pipeline und reduziert den Ressourcenbedarf deutlich. Begruendung in
  [docs/adr/0003-airflow-local-executor.md](adr/0003-airflow-local-executor.md).
- **Datengetriebene Skill-Taxonomie.** Synonyme und Wortgrenzenpruefung
  vermeiden Fehltreffer; Erweiterung ohne Codeaenderung moeglich.

## Datenmodell (Gold)

- `fact_jobs` (eine Zeile pro Stellenanzeige, mit Fremdschluesseln auf
  `dim_company` und `dim_location`).
- `fact_skills` (eine Zeile pro Skill je Anzeige, plus Gewichtung).
- `dim_company`, `dim_location`, `dim_date` als Surrogatschluessel-Dimensionen.

dbt-Tests sichern Eindeutigkeit, Nicht-Null-Constraints und referenzielle
Integritaet.

## Sicherheit und Betrieb

- Geheimnisse ausschliesslich via Umgebung.
- Konsistentes Fehlerschema mit Korrelationskennung in jedem Response-Header.
- Strukturierte JSON-Logs (`structlog`), kompatibel mit Loki/Promtail.
- Healthcheck und Readinesscheck unter `/api/v1/health` und `/api/v1/ready`.
