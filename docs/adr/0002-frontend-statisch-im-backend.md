# ADR 0002: Frontend statisch exportiert und vom Backend ausgeliefert

## Status
Akzeptiert.

## Kontext
Auf dem Ziel-VPS existiert bereits eine Nginx-Konfiguration, die
`pgadmin.thetransporterlabs.de` auf `127.0.0.1:8081` proxyt. Eine eigene
Nginx-Komponente waere doppelte Konfiguration. Ein dauerhaft laufender Node-Server
fuer Next.js wuerde zusaetzliche Ressourcen binden.

## Entscheidung
Das Frontend wird mit Next.js `output: 'export'` zur Build-Zeit als statische
HTML- und JS-Bundles erzeugt. Diese werden in das Backend-Image kopiert; das
Backend mountet sie als StaticFiles unter `/` und behandelt `/api/v1/...`
weiter normal. Genau ein Container und ein Port (`127.0.0.1:8081`) reichen
fuer den oeffentlichen Zugriff.

## Alternativen
- **Next.js standalone als eigenstaendiger Dienst.** Mehr Speicher, zwei
  Container, zusaetzlicher Reverse-Proxy noetig.
- **Eigene Nginx im Compose-Stack.** Kollidiert mit der bestehenden Host-Nginx.

## Konsequenzen
- Kein Node-Runtime in Produktion, kein zusaetzlicher Proxy.
- Frontend-Aenderungen erfordern einen Rebuild des Backend-Images.
- Server-seitiges Rendering ist nicht moeglich; das Dashboard ist client-getrieben.
