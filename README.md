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

## Verifizierter Deploymentstand

Stand des letzten Deployments auf diesem Repository:

- Docker-Build erfolgreich fuer alle 4 Images (`backend`, `airflow-init`, `airflow-scheduler`, `airflow-webserver`).
- `docker compose up -d` startet Postgres, Airflow-Init, Scheduler, Webserver und Backend stabil.
- `GET http://127.0.0.1:8081/api/v1/health` antwortet `{"status":"ok"}`.
- `GET http://127.0.0.1:8081/api/v1/ready` antwortet `{"status":"ok"}`.
- `GET http://127.0.0.1:8081/api/v1/openapi.json` liefert die vollstaendige Spezifikation.
- `GET http://127.0.0.1:8081/` liefert das statisch exportierte Dashboard (HTTP 200, HTML).
- DAGs `arbeitsmarkt_data_pipeline` und `arbeitsmarkt_backfill` sind in Airflow registriert.
- Datenendpunkte (`/api/v1/stats`, `/jobs`, `/skills`, `/companies`, `/cities`, `/trends/...`) sind erst nach erfolgreicher Pipeline antwortfaehig; bis dahin geben sie strukturierte Fehler im einheitlichen Format zurueck.

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
