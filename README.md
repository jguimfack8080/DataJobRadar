# Data Job Radar Deutschland

Analyseplattform fuer den deutschen IT-Arbeitsmarkt. Die Anwendung extrahiert
taeglich Stellenangebote ueber die Adzuna API, normalisiert und transformiert
sie ueber ein Bronze-Silver-Gold Data Lake, modelliert sie als Sternschema in
DuckDB und stellt die Ergebnisse ueber ein modernes Dashboard zur Verfuegung.

## Schluesseleigenschaften

- Echte Produktionsarchitektur mit Ingestion, Data Lake, dbt, Orchestrierung, API und Dashboard.
- Strikt ressourcenschonend: ein einziger Backend-Prozess hinter der bestehenden Nginx, kein zusaetzlicher Frontend-Runtime im Produktivbetrieb.
- Durchgaengig deutschsprachig, ohne Emojis, mit klarer Trennung der Verantwortlichkeiten.
- Vollstaendig containerisiert und durch ein einzelnes `docker compose up` startbar.

## Architektur auf einen Blick

```
Adzuna API
   |
   v
Ingestion (httpx + tenacity + Validierung) ---> Bronze (Parquet, partitioniert)
                                                       |
                                                       v
                                                Silver (DuckDB SQL,
                                                        Normalisierung,
                                                        Skill-Extraktion)
                                                       |
                                                       v
                                          dbt Core (Staging + Marts)
                                                       |
                                                       v
                                          Gold (Sternschema in DuckDB)
                                                       |
                                                       v
                                            FastAPI Backend (Port 8081)
                                                       |
                                                       v
                                       Next.js Dashboard (statisch exportiert,
                                       vom Backend ausgeliefert)
```

Eine detaillierte Datenflussbeschreibung steht in [docs/datenfluss.md](docs/datenfluss.md).

## Projektstruktur

```
data-job-radar/
  ingestion/        Adzuna-Client, Validierung, Pipeline
  data_lake/        Bronze, Silver, Gold (Parquet, DuckDB)
  skills/           Skill-Taxonomie und Extraktor
  transform/        dbt-Core-Projekt (Staging + Marts)
  analytics/        DuckDB-Engine und vorgefertigte Abfragen
  orchestration/    Airflow-DAGs (Tagespipeline, Backfill)
  backend/          FastAPI-Anwendung (Port 8081, serviert auch das Frontend)
  frontend/         Next.js-Dashboard (statischer Export)
  shared/           Geteilte Python-Bibliothek (djr_core)
  infra/docker/     Dockerfiles und Requirements pro Service
  tests/            Unit- und Integrationstests
  docs/             ADRs, Datenfluss, Architektur, Setup
```

## Pipeline-Lauf und Zero-Duplikat-Garantie

Die Pipeline laeuft **viermal pro Tag** automatisch: jeweils um 00:00, 06:00, 12:00
und 18:00 UTC (Cron `0 */6 * * *`). `max_active_runs=1` verhindert ueberlappende
Laeufe; eine laufende Pipeline blockiert den naechsten Schedule, bis sie fertig ist.

Auch bei mehreren Laeufen pro Tag wird **garantiert kein Duplikat** in den Gold-Tabellen
landen. Es gibt vier unabhaengige Schutzebenen:

1. **Silver-SQL** dedupliziert mit `ROW_NUMBER() OVER (PARTITION BY adzuna_id ORDER BY abruf_zeitpunkt DESC)` innerhalb des Tagespartitions-Files.
2. **dbt-Staging-Modell** wiederholt die Deduplizierung quer ueber **alle** Silver-Dateien (also auch ueber alle Tage hinweg).
3. **dbt-Unique-Test** auf `fact_jobs.adzuna_id` prueft das Ergebnis nach jedem Lauf. Bei der kleinsten Verletzung faellt die Pipeline rot und der Verantwortliche bekommt eine Mail an `jeunaj3@gmail.com`.
4. **Bronze-Dateinamen** enthalten eine Korrelationskennung, sodass parallele Schreibvorgaenge sich nicht ueberschreiben koennen.

Frequenz aendern: In `orchestration/dags/dag_arbeitsmarkt.py` den `schedule`-Wert anpassen:

```python
schedule="0 */6 * * *"   # alle 6 Stunden (Standard, 4x/Tag)
schedule="0 */4 * * *"   # alle 4 Stunden (6x/Tag)
schedule="0 */12 * * *"  # alle 12 Stunden (2x/Tag)
schedule="0 6 * * *"     # einmal taeglich 06:00 UTC
```

Anschliessend `docker compose restart airflow-scheduler`.

## Schnellstart

Voraussetzungen: Docker und Docker Compose v2 oder hoeher. `make` ist optional.

1. Datei `.env` anlegen, indem Sie `.env.example` kopieren und mit Ihren Adzuna-Zugangsdaten fuellen.
2. Container bauen: `make bauen` oder direkt `docker compose build`.
3. Stack starten: `make starten` oder `docker compose up -d`.
4. Im Browser `http://pgadmin.thetransporterlabs.de` (oder `http://127.0.0.1:8081`) oeffnen.
5. Airflow-Webinterface: `http://127.0.0.1:8080` (Standardkonto `admin/admin`, im Produktivbetrieb aendern).

Manueller Initiallauf:

- `make ingest` oder `docker compose exec airflow-scheduler airflow dags trigger arbeitsmarkt_data_pipeline`.
- `make backfill` oder analoges `dags trigger arbeitsmarkt_backfill` fuer einen Backfill.
- `make dbt-run` und `make dbt-test` lassen dbt isoliert im Airflow-Container laufen.

## Verifizierter Live-Stand

Stand des aktuellen Deployments:

- Erreichbar unter `https://pgadmin.thetransporterlabs.de/` (HTTP wird per 301 auf HTTPS umgeleitet, das Host-Nginx terminiert das TLS).
- Lokal: `http://127.0.0.1:8081/` (Backend mit eingebettetem Dashboard).
- Pipeline `arbeitsmarkt_data_pipeline` einmal komplett durchgelaufen mit allen sechs Tasks `success`: `ingestion_lauf -> silver_transformation -> gold_initialisieren -> dbt_deps -> dbt_run -> dbt_test`.
- Backend antwortet mit echten Daten aus der Adzuna API:
    - Mehr als 3000 aktive Stellenanzeigen aus Deutschland im Bestand
    - Hunderte Unternehmen, dutzende Standorte mit Gehaltsstatistiken
    - Live-Beispiel: Berlin Median 80.000 EUR, Bayern Median 91.250 EUR
- Alle 17 ueberprueften Endpunkte (API + Frontend-Seiten) antworten mit HTTP 200:
    - System: `/api/v1/health`, `/api/v1/ready`, `/api/v1/openapi.json`, `/api/v1/docs`
    - Daten: `/api/v1/stats`, `/api/v1/jobs`, `/api/v1/skills`, `/api/v1/companies`, `/api/v1/cities`, `/api/v1/trends/zeitreihe`, `/api/v1/trends/gehaltsverteilung`
    - Frontend: `/`, `/anzeigen/`, `/skills/`, `/unternehmen/`, `/staedte/`, `/trends/`
- Health-Header `X-Korrelations-Kennung` ist in jeder Antwort gesetzt.
- Container-Stack `docker compose ps`: `postgres`, `airflow-scheduler`, `airflow-webserver`, `backend` -> jeweils `running (healthy)`.

## Tests und Qualitaet

- `make tests` fuehrt die komplette Pytest-Suite im Backend-Container aus.
- `make lint` (ruff), `make format` (ruff format) und `make typcheck` (mypy) decken die Codequalitaet ab.
- dbt enthaelt explizite Datenqualitaetstests (`not_null`, `unique`, `relationships`, `accepted_values`).

## Mailbenachrichtigung bei Pipeline-Fehlern

Die DAGs `arbeitsmarkt_data_pipeline` und `arbeitsmarkt_backfill` haben `owner=jordan`
und senden bei finalen Fehlern an `jeunaj3@gmail.com`.

Damit Airflow Mails wirklich verschickt, muss eine SMTP-Konfiguration in `.env`
eingetragen sein. Sind die Werte leer, bleibt der Versand stumm. Beispiel fuer
Gmail mit App-Passwort (Erzeugung unter https://myaccount.google.com/apppasswords):

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_STARTTLS=True
SMTP_SSL=False
SMTP_USER=meine-mail@gmail.com
SMTP_PASSWORD=das-16-zeichen-app-passwort
SMTP_MAIL_FROM=meine-mail@gmail.com
```

Nach dem Setzen `docker compose up -d` neu ausfuehren, damit die Umgebungsvariablen
in den Airflow-Containern aktualisiert werden.

## Sicherheit

- Geheimnisse werden ausschliesslich ueber `.env` geladen und nie versioniert.
- Eingaben am API-Rand werden ueber Pydantic streng validiert.
- IP-basiertes Rate Limiting (`BACKEND_RATE_LIMIT_PER_MINUTE`).
- Konsistentes Fehlerformat ohne Preisgabe interner Details.
- CORS auf die definierten Frontends begrenzt.

## Deployment-Topologie

Auf dem Host existiert bereits eine Nginx-Konfiguration, die
`pgadmin.thetransporterlabs.de` auf `127.0.0.1:8081` proxyt. Dieses Projekt
liefert daher KEINE eigene Nginx-Komponente und veroeffentlicht den Backend-Port
ausschliesslich auf der Loopback-Schnittstelle. Die Architekturentscheidung ist
in [docs/adr/0002-frontend-statisch-im-backend.md](docs/adr/0002-frontend-statisch-im-backend.md)
festgehalten.

## Performance- und Ressourcenbudgets

- Backend laeuft mit einem Uvicorn-Worker und einer In-Memory-Cache-Schicht, Speicherbudget unter 512 MB.
- Airflow nutzt LocalExecutor (kein Celery/Redis), Postgres ausschliesslich als Airflow-Metadatenbank.
- DuckDB ist prozessintern, ohne zusaetzlichen Datenbankserver.
- Frontend wird statisch exportiert und vom Backend ausgeliefert; in Produktion laeuft kein Node-Runtime.
- Lighthouse-Performance- und Barrierefreiheits-Werte: jeweils mindestens 90 (Desktop).

## Weiterfuehrende Dokumente

- [Architekturuebersicht](docs/architektur.md)
- [Setup-Anleitung](docs/setup.md)
- [Deployment](docs/deployment.md)
- [Datenfluss](docs/datenfluss.md)
- [API-Referenz](docs/api.md)
- [ADRs](docs/adr/)

## Diagramme

Sechs schwarz-weisse, druckfreundliche Diagramme. Sie sind im Repository
abgelegt und werden zur Build-Zeit auch in das Dashboard kopiert, sodass sie
unter `/diagramme/<name>.svg` und in der `/wiki/`-Seite erreichbar sind.

| Diagramm                                    | Inhalt                                                       |
|---------------------------------------------|--------------------------------------------------------------|
| [Systemarchitektur](docs/architektur.svg)   | Schichten, Komponenten und Verantwortlichkeiten im Ueberblick|
| [Datenfluss](docs/datenfluss.svg)           | Adzuna bis Dashboard auf einer Linie                         |
| [Medallion-Schichten](docs/medallion.svg)   | Bronze, Silver, Gold mit Aufgaben und Garantien              |
| [Airflow-DAG](docs/airflow_dag.svg)         | Reihenfolge, Retries, Benachrichtigung                       |
| [Datenmodell](docs/datenmodell.svg)         | Sternschema mit fact_jobs, fact_skills und Dimensionen       |
| [Deployment-Topologie](docs/deployment.svg) | Host-Nginx, Docker-Stack, Volumes und Sicherheitsgrenzen     |

## Live-Dashboard

- Uebersicht: `https://pgadmin.thetransporterlabs.de/`
- Stellenanzeigen mit Mehr-Laden-Pagination und direkten Links zur Adzuna-Anzeige: `/anzeigen/`
- Wiki-Seite mit Projekt-Erklaerung, Architektur und allen Diagrammen: `/wiki/`
