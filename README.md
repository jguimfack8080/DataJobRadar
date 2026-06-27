# Data Job Radar Deutschland

**Autor:** Jordan Jeuna

Analyseplattform fuer den deutschen IT-Arbeitsmarkt. Fuenf Quellen werden mehrmals
taeglich zusammengefuehrt: Bundesagentur fuer Arbeit, Adzuna, The Muse, Remotive
und Jobicy. Die Stellenangebote durchlaufen ein Bronze-Silver-Gold Data Lake,
werden als Sternschema in DuckDB modelliert und ueber ein live-aktualisierbares
Dashboard mit paginierten Ranglisten, Skill-Auswertungen und Gehaltsstatistiken
zugaenglich gemacht.

## Schluesseleigenschaften

- Echte Produktionsarchitektur mit Ingestion, Data Lake, dbt, Orchestrierung, API und Dashboard.
- Strikt ressourcenschonend: ein einziger Backend-Prozess hinter der bestehenden Nginx, kein zusaetzlicher Frontend-Runtime im Produktivbetrieb.
- Durchgaengig deutschsprachig, ohne Emojis, mit klarer Trennung der Verantwortlichkeiten.
- Vollstaendig containerisiert und durch ein einzelnes `docker compose up` startbar.

## Architektur auf einen Blick

```
Bundesagentur f. Arbeit
Adzuna
The Muse            }---> Ingestion (httpx + tenacity + Validierung)
Remotive                        |
Jobicy                          v
                        Bronze (Parquet, partitioniert nach Quelle und Tag)
                                |
                                v
                        Silver (DuckDB SQL, Normalisierung, Skill-Extraktion)
                                |
                                v
                        dbt Core (Staging + Marts, Cross-Source-Dedup)
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
  ingestion/        Clients fuer fuenf Quellen (Bundesagentur, Adzuna, Muse, Remotive, Jobicy),
                    Validierung, Pipeline mit Zero-Duplikat-Garantie
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

Jeder Lauf fragt alle fuenf Quellen ab: Bundesagentur fuer Arbeit, Adzuna, The Muse,
Remotive und Jobicy. Auch bei mehreren Laeufen und mehreren Quellen landet
**garantiert kein Duplikat** in den Gold-Tabellen. Es gibt vier unabhaengige Schutzebenen:

1. **Silver-SQL** dedupliziert per `ROW_NUMBER() OVER (PARTITION BY job_id ORDER BY abruf_zeitpunkt DESC)` innerhalb jedes Tagespartitions-Files.
2. **dbt-Staging-Modell** wiederholt die Deduplizierung quer ueber **alle** Silver-Dateien (also auch ueber alle Tage und Quellen hinweg).
3. **dbt-Unique-Test** auf `fact_jobs.job_id` prueft das Ergebnis nach jedem Lauf. Bei der kleinsten Verletzung faellt die Pipeline rot und der Verantwortliche bekommt eine Mail an `jeunaj3@gmail.com`.
4. **Bronze-Dateinamen** enthalten eine Korrelationskennung und den Quellnamen, sodass parallele Schreibvorgaenge sich nicht ueberschreiben koennen.

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
- Admin-Dashboard: `https://pgadmin.thetransporterlabs.de/admin/` (Token-Authentifizierung, Wert in `.env` unter `ADMIN_TOKEN`). Lokal: `http://127.0.0.1:8081/admin/`.
- Pipeline `arbeitsmarkt_data_pipeline` einmal komplett durchgelaufen mit allen sechs Tasks `success`: `ingestion_lauf -> silver_transformation -> gold_initialisieren -> dbt_deps -> dbt_run -> dbt_test`.
- Backend antwortet mit echten Daten aus der Adzuna API:
    - Mehr als 3000 aktive Stellenanzeigen aus Deutschland im Bestand
    - Hunderte Unternehmen, dutzende Standorte mit Gehaltsstatistiken
    - Live-Beispiel: Berlin Median 80.000 EUR, Bayern Median 91.250 EUR
- Alle 19 ueberprueften Endpunkte (API + Frontend-Seiten) antworten mit HTTP 200:
    - System: `/api/v1/health`, `/api/v1/ready`, `/api/v1/openapi.json`, `/api/v1/docs`
    - Daten: `/api/v1/stats`, `/api/v1/jobs`, `/api/v1/skills`, `/api/v1/companies`, `/api/v1/cities`, `/api/v1/trends/zeitreihe`, `/api/v1/trends/gehaltsverteilung`
    - Frontend: `/`, `/anzeigen/`, `/skills/`, `/unternehmen/`, `/staedte/`, `/trends/`, `/gespeichert/`, `/wiki/`
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

## Social-Media-Vorschaubild (OG-Image)

Das Vorschaubild fuer LinkedIn, WhatsApp, Facebook und X (Twitter) liegt in zwei Formaten vor:

| Datei | Rolle |
|---|---|
| [`frontend/public/og-image.svg`](frontend/public/og-image.svg) | Quelldatei zum Bearbeiten (Vektorgrafik, 1200x630) |
| [`frontend/public/og-image.png`](frontend/public/og-image.png) | Produktionsdatei, die von den Crawlern geladen wird |

Um das Bild anzupassen: SVG mit einem Editor (Inkscape, VS Code, Browser) oeffnen und aendern,
dann das PNG neu erzeugen und das Backend neu bauen:

```bash
python3 -c "
import cairosvg
cairosvg.svg2png(
    url='frontend/public/og-image.svg',
    write_to='frontend/public/og-image.png',
    output_width=1200,
    output_height=630
)
"
docker compose build backend && docker compose up -d backend
```

## Live-Dashboard

Alle Seiten laden initial 50 Eintraege und bieten einen "Mehr laden"-Button, sobald weitere
Eintraege vorhanden sind.

| Seite | URL | Inhalt |
|---|---|---|
| Uebersicht | `/` | Kennzahlen, Zeitreihe, Gehaltsverteilung |
| Stellenanzeigen | `/anzeigen/` | Filterbarer Katalog mit Quell-Links, Speicherfunktion, Status-Badges (Gesehen, Gespeichert, Beworben) und "Nur Neue"-Filter |
| Skills | `/skills/` | Rangliste und Balkendiagramm der gefragtesten Technologien |
| Unternehmen | `/unternehmen/` | Rangliste nach Stellenanzahl und mittlerem Gehalt |
| Staedte | `/staedte/` | Regionale Verteilung mit Karte und Tabelle |
| Trends | `/trends/` | Zeitreihe und Gehaltsverteilung nach Kategorie |
| Gespeichert | `/gespeichert/` | Verwaltung gespeicherter und beworbener Stellen (lokaler Browserspeicher) |
| Wiki | `/wiki/` | Projekt-Erklaerung, Architektur und alle Diagramme |
