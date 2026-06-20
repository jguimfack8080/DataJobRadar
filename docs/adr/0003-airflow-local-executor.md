# ADR 0003: Airflow mit LocalExecutor

## Status
Akzeptiert.

## Kontext
Die Pipeline laeuft taeglich und ist linear (Ingestion -> Silver -> dbt). Ein
verteilter Executor mit Celery oder Kubernetes waere ueberdimensioniert und
wuerde Broker (Redis) sowie Worker zusaetzlich erfordern.

## Entscheidung
Wir betreiben Airflow mit LocalExecutor. Scheduler und Webserver laufen in
separaten Containern, teilen sich aber das Image und das Volume mit Postgres
fuer Metadaten.

## Alternativen
- **SequentialExecutor.** Zu eingeschraenkt fuer parallele Tasks.
- **CeleryExecutor.** Hoeherer Footprint, Redis und Worker zusaetzlich.
- **KubernetesExecutor.** Bei der Zielarchitektur nicht praktikabel.

## Konsequenzen
- Kein Broker, kein Worker-Pool, kein zusaetzlicher Speicherbedarf.
- Skalierung beim Wachsen der Pipeline durch Wechsel auf CeleryExecutor moeglich.
