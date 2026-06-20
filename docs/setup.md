# Setup

## Voraussetzungen

- Docker Engine und Docker Compose Plugin v2 oder hoeher
- Linux-Host mit mindestens 2 GB freiem Speicher
- Adzuna-Zugangsdaten (App ID, App Key)

## Lokale Einrichtung

1. Repository klonen und in das Projekt wechseln.
2. `.env` aus `.env.example` ableiten und `ADZUNA_APP_ID` sowie
   `ADZUNA_APP_KEY` setzen. Optional weitere Variablen anpassen.
3. Container bauen:

   ```bash
   make bauen
   ```

4. Stack starten:

   ```bash
   make starten
   ```

5. Pipeline manuell ausloesen:

   ```bash
   make ingest
   ```

## Dienste und Ports (alle nur auf 127.0.0.1)

| Dienst        | Port | Zweck                                                           |
|---------------|------|-----------------------------------------------------------------|
| backend       | 8081 | API und statisch ausgeliefertes Frontend                        |
| airflow-web   | 8080 | Airflow-Webinterface (intern)                                   |
| postgres      | 5432 | Nur intern erreichbar, Airflow-Metadaten                        |

Die Host-Nginx leitet `pgadmin.thetransporterlabs.de` auf `127.0.0.1:8081`
weiter; eine eigene Reverse-Proxy-Konfiguration ist nicht erforderlich.

## Daten- und Pipelineflows pruefen

- DuckDB-Datei: `/data/warehouse/djr.duckdb` (im Volume `djr-warehouse`).
- Data Lake: `/data/lake/{bronze,silver,gold}` (im Volume `djr-lake`).
- Logs: `docker compose logs backend` bzw. `airflow-scheduler`.
