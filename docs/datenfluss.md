# Datenfluss von Adzuna bis Dashboard

## Schrittweise Beschreibung

1. **Aufruf der Adzuna API.** Pro Suchkategorie werden seitenweise Treffer
   abgerufen. Der Client wendet exponentielles Backoff mit Jitter und ein
   Rate-Limit-Handling auf 429-Antworten an. Bei 401, 403 oder 429 in Verbindung
   mit fehlendem Quota wird der Lauf kontrolliert abgebrochen.
2. **Validierung.** Jeder Treffer wird gegen das `RohStellenanzeige`-Schema
   gepruefst. Verletzungen landen in einer Quarantaene-Datei und gehen NICHT
   verloren.
3. **Bronze-Schicht.** Validierte Treffer werden als Parquet mit Zstd-Kompression
   geschrieben; Partitionierung: `jahr/monat/tag/kategorie/seite`.
4. **Silver-Schicht.** Ein DuckDB-Lauf vereinheitlicht Orte, Unternehmen und
   Gehaltsangaben, dedupliziert anhand der Adzuna-ID und reichert um Skills an
   (ueber die `SkillExtraktor`-Funktion, die DuckDB als UDF registriert).
5. **dbt Core.** Staging-Views auf die Silver-Schicht erzeugen anschliessend die
   Gold-Tabellen `dim_company`, `dim_location`, `dim_date`, `fact_jobs` und
   `fact_skills`. Datenqualitaetstests von dbt sichern Eindeutigkeit,
   Nicht-Null-Bedingungen, referenzielle Integritaet und erlaubte Werte.
6. **FastAPI Backend.** Liest direkt aus der DuckDB-Datei, cached teure
   Aggregationen in einem TTL-Cache und gibt strukturierte, typisierte
   Antworten zurueck.
7. **Next.js Dashboard.** Statisch exportiert, wird vom Backend ausgeliefert,
   spricht die API ueber `/api/v1/...` an und rendert Kacheln, Listen,
   Linien- und Balkendiagramme mit Recharts.

## Diagramm (SVG, schwarz auf weiss)

Eine simple, druckfreundliche Skizze liegt unter [docs/datenfluss.svg](datenfluss.svg).
