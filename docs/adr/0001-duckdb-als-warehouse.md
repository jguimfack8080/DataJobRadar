# ADR 0001: DuckDB als analytisches Warehouse

## Status
Akzeptiert.

## Kontext
Das Projekt benoetigt ein leistungsfaehiges, ressourcenschonendes Warehouse fuer
Aggregationen ueber Stellenanzeigen, Skills und Zeitreihen. Es laeuft in einem
einzelnen VPS-Setup hinter Nginx und soll weder einen separaten DB-Server noch
zusaetzliche Cluster-Komponenten erfordern.

## Entscheidung
Wir setzen DuckDB als prozessinternes Warehouse ein. Die Gold-Schicht wird von
dbt-duckdb materialisiert. Das Backend liest die DuckDB-Datei direkt im
Read-only-Modus.

## Alternativen
- **PostgreSQL.** Bewaehrt, aber teurer im Betrieb, schwerer bei OLAP-Lasten.
- **ClickHouse.** Sehr schnell, jedoch zusaetzlicher Dienst und hoeherer Footprint.
- **BigQuery / Snowflake.** Bewaehrte Warehouse-Loesungen, aber Cloud-gebunden
  und kostenpflichtig.

## Konsequenzen
- Keine zusaetzlichen Serverprozesse, sehr geringer RAM-Bedarf.
- Backend und dbt teilen sich die Datei (Backend read-only, dbt schreibt).
- Migrationen erfolgen ueber dbt; Strukturaenderungen sind klar versioniert.
