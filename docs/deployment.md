# Deployment

## Ziel-Topologie

- Bestehende Nginx auf dem Host proxyt Port 80 fuer
  `pgadmin.thetransporterlabs.de` auf `127.0.0.1:8081`.
- Das Backend bindet sich ausschliesslich auf die Loopback-Schnittstelle des Hosts.
- Es laeuft kein zusaetzlicher Reverse-Proxy und kein zusaetzliches Frontend.

## Schritte

1. `.env` mit Produktivwerten anlegen (insbesondere `ADZUNA_APP_ID`,
   `ADZUNA_APP_KEY`, `AIRFLOW__CORE__FERNET_KEY`,
   `AIRFLOW__WEBSERVER__SECRET_KEY`, `AIRFLOW_DB_PASSWORD`).
2. Container bauen und starten:

   ```bash
   docker compose build
   docker compose up -d
   ```

3. DAG `arbeitsmarkt_data_pipeline` einmalig ausloesen, damit die DuckDB-Datei
   gefuellt wird:

   ```bash
   docker compose exec airflow-scheduler airflow dags trigger arbeitsmarkt_data_pipeline
   ```

4. Bereitschaft pruefen:

   ```bash
   curl -fs http://127.0.0.1:8081/api/v1/health
   ```

5. Nginx auf dem Host laden (sofern nicht bereits aktiv):

   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

## Updates

- Images neu bauen, dann `docker compose up -d`.
- Die DuckDB-Datei und das Data Lake liegen in benannten Volumes; sie ueberleben
  Container-Neustarts.

## Sicherheit

- Standard-Airflow-Konto (admin/admin) im Produktivbetrieb ueber das
  Webinterface aendern oder ueber Umgebung initialisieren.
- HTTPS wird durch die Host-Nginx terminiert (Certbot empfohlen).
