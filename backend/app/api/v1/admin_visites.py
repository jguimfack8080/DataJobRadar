"""Besucherprotokoll-Dashboard. Nur von localhost abrufbar."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/admin", tags=["admin"])

_BESUCH_PFAD = Path(os.getenv("BESUCH_LOG_PFAD", "/data/logs/visites.txt"))
def _ip_pruefen(request: Request) -> None:
    # Requests durch Nginx tragen immer X-Forwarded-For.
    # Direkte Verbindungen auf Port 8081 (localhost) haben diesen Header nicht.
    if request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP"):
        raise HTTPException(status_code=403, detail="Zugriff nur von localhost erlaubt.")


@router.get("/visites", response_class=HTMLResponse, include_in_schema=False)
def visites_dashboard(request: Request) -> HTMLResponse:
    _ip_pruefen(request)

    zeilen: list[str] = []
    if _BESUCH_PFAD.exists():
        try:
            inhalt = _BESUCH_PFAD.read_text(encoding="utf-8")
            zeilen = [z for z in inhalt.splitlines() if z.strip()]
        except Exception:
            zeilen = []

    zeilen_umgekehrt = list(reversed(zeilen))

    def zeile_zu_zeilen_html(zeile: str) -> str:
        teile = [t.strip() for t in zeile.split("|")]
        zellen = "".join(f"<td>{t}</td>" for t in teile)
        return f"<tr>{zellen}</tr>"

    tabelle_html = "\n".join(zeile_zu_zeilen_html(z) for z in zeilen_umgekehrt[:500])
    anzahl = len(zeilen)

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Besucherprotokoll</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: #0f0f11; color: #e2e2e2; padding: 2rem; }}
  h1 {{ font-size: 1.5rem; font-weight: 600; margin-bottom: 0.25rem; }}
  .meta {{ font-size: 0.8rem; color: #888; margin-bottom: 1.5rem; }}
  .suche {{ margin-bottom: 1rem; }}
  .suche input {{
    background: #1a1a1e; border: 1px solid #333; color: #e2e2e2;
    border-radius: 6px; padding: 0.5rem 0.75rem; font-size: 0.85rem;
    width: 100%; max-width: 400px;
  }}
  .suche input::placeholder {{ color: #666; }}
  .wrapper {{ overflow-x: auto; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.78rem; }}
  thead tr {{ background: #1e1e24; }}
  th {{ padding: 0.6rem 0.75rem; text-align: left; font-weight: 500;
       color: #aaa; border-bottom: 1px solid #333; white-space: nowrap; }}
  td {{ padding: 0.45rem 0.75rem; border-bottom: 1px solid #1e1e24;
       max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  tr:hover td {{ background: #1a1a20; }}
  .badge {{ display: inline-block; background: #2a2a35; border-radius: 4px;
            padding: 0.1rem 0.4rem; font-size: 0.7rem; color: #888; }}
</style>
</head>
<body>
<h1>Besucherprotokoll</h1>
<p class="meta">
  {anzahl} Eintraege gesamt &nbsp;&mdash;&nbsp;
  Datei: {_BESUCH_PFAD} &nbsp;&mdash;&nbsp;
  Letzte 500 angezeigt (neueste zuerst)
</p>
<div class="suche">
  <input type="text" id="suche" placeholder="Filtern nach IP, Land, Pfad ..." oninput="filtern()" />
</div>
<div class="wrapper">
<table id="tabelle">
  <thead>
    <tr>
      <th>Zeitpunkt (UTC)</th>
      <th>IP</th>
      <th>Land | Stadt | ISP</th>
      <th>Methode + Pfad</th>
      <th>Status</th>
      <th>User-Agent</th>
      <th>Referrer</th>
    </tr>
  </thead>
  <tbody id="tbody">
{tabelle_html}
  </tbody>
</table>
</div>
<script>
function filtern() {{
  const q = document.getElementById('suche').value.toLowerCase();
  const zeilen = document.getElementById('tbody').querySelectorAll('tr');
  zeilen.forEach(z => {{
    z.style.display = z.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""
    return HTMLResponse(content=html)
