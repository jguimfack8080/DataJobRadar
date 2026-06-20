# API-Referenz

Die vollstaendige, jederzeit aktuelle Spezifikation ist unter
`GET /api/v1/openapi.json` verfuegbar; eine interaktive Swagger-Ansicht unter
`GET /api/v1/docs`.

## Endpunkte (v1)

| Pfad                              | Methode | Beschreibung                                                  |
|-----------------------------------|---------|---------------------------------------------------------------|
| `/api/v1/health`                  | GET     | Gesundheitspruefung (200 = laeuft)                            |
| `/api/v1/ready`                   | GET     | Bereitschaftspruefung                                         |
| `/api/v1/stats`                   | GET     | Gesamtkennzahlen                                              |
| `/api/v1/jobs`                    | GET     | Stellenanzeigen mit Filtern und Keyset-Pagination             |
| `/api/v1/skills`                  | GET     | Top-Skills, optional `limit`                                  |
| `/api/v1/companies`               | GET     | Top-Unternehmen                                               |
| `/api/v1/cities`                  | GET     | Top-Staedte                                                   |
| `/api/v1/trends/zeitreihe`        | GET     | Anzahl neuer Anzeigen je Tag                                  |
| `/api/v1/trends/gehaltsverteilung`| GET     | P25/P50/P75 nach Kategorie, Stadt oder Bundesland             |

## Fehlerformat

Alle Fehlerantworten folgen demselben Schema:

```json
{
  "code": "rate_limit_ueberschritten",
  "meldung": "Zu viele Anfragen. Bitte versuchen Sie es spaeter erneut.",
  "korrelationskennung": "ab12cd34...",
  "kontext": {}
}
```

Die Korrelationskennung steht zusaetzlich im Antwortheader
`X-Korrelations-Kennung` und wird durchgaengig protokolliert.

## Beispielanfragen

```bash
curl http://127.0.0.1:8081/api/v1/stats
curl "http://127.0.0.1:8081/api/v1/jobs?suche=spark&limit=10"
curl "http://127.0.0.1:8081/api/v1/trends/gehaltsverteilung?gruppierung=bundesland"
```
