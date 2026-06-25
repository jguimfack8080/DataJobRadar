"""RemoteOK - https://remoteok.com/api

Kostenlos, kein API-Key. Liefert alle Remote-Stellen in einem Aufruf (kein Paging).
Erstes Element der Antwort ist ein Haftungsausschluss-Objekt ohne 'id'.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Iterator, List, Optional

from djr_core.logging import get_logger
from djr_core.models import JobQuelle, RohStellenanzeige
from djr_core.utils import aktueller_zeitpunkt_utc

from ingestion.base.client import BasisQuelleClient, QuelleSeite, Suchanfrage

_logger = get_logger("ingestion.remoteok.client")

_BASIS_URL = "https://remoteok.com/api"

_RELEVANTE_TAGS = (
    "data-engineer", "data-scientist", "python", "machine-learning",
    "backend", "software-engineer", "devops", "cloud",
)


class RemoteokClient(BasisQuelleClient):
    quelle = JobQuelle.REMOTEOK

    STANDARD_ANFRAGEN = (
        Suchanfrage("data_engineer", "data-engineer", "Remote Data Engineer Stellen"),
        Suchanfrage("python", "python", "Remote Python Stellen"),
    )

    def standard_suchanfragen(self) -> List[Suchanfrage]:
        return list(self.STANDARD_ANFRAGEN)

    def seiten_abrufen(
        self,
        anfrage: Suchanfrage,
        *,
        max_seiten: int,
        startseite: int = 1,
    ) -> Iterator[QuelleSeite]:
        daten = self._abrufen(tag=anfrage.query)
        anzeigen: List[RohStellenanzeige] = []
        for roh in daten:
            if not isinstance(roh, dict) or not roh.get("id"):
                continue
            anzeigen.append(self._mappen(roh, anfrage.kategorie))

        yield QuelleSeite(
            quelle=self.quelle,
            seite=1,
            anzeigen=anzeigen,
            gesamt_geschaetzt=len(anzeigen),
            abruf_zeitpunkt=time.time(),
            quell_kategorie=anfrage.kategorie,
        )

    def _abrufen(self, *, tag: str) -> list:
        @self._retry
        def aufrufen() -> list:
            antwort = self._client.get(_BASIS_URL, params={"tag": tag})
            kontext = {"quelle": "remoteok", "tag": tag}
            if antwort.status_code == 200:
                try:
                    return antwort.json()
                except ValueError:
                    from djr_core.exceptions import ExterneApiFehler
                    raise ExterneApiFehler("Keine gueltiges JSON", kontext=kontext)
            return self._antwort_verarbeiten(antwort, kontext=kontext)
        return aufrufen()

    @staticmethod
    def _datum_parsen(wert: Any) -> Optional[datetime]:
        if not wert or not isinstance(wert, str):
            return None
        try:
            return datetime.fromisoformat(wert.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _mappen(self, roh: dict[str, Any], kategorie: str) -> RohStellenanzeige:
        tags = roh.get("tags") or []
        return RohStellenanzeige(
            quelle=self.quelle,
            quell_id=str(roh["id"]),
            titel=str(roh.get("position") or "Unbekannt"),
            beschreibung=str(roh.get("description") or ""),
            unternehmen=roh.get("company"),
            standort_anzeige=roh.get("location") or "Remote",
            standort_segmente=[],
            stadt=None,
            bundesland=None,
            region="Remote",
            gehalt_min=None,
            gehalt_max=None,
            gehalt_ist_vorhanden=False,
            waehrung="USD",
            vertragstyp=None,
            vertragszeit=None,
            kategorie_kennung=tags[0] if tags else None,
            kategorie_bezeichnung=", ".join(tags[:3]) if tags else None,
            veroeffentlicht_am=self._datum_parsen(roh.get("date")),
            angebots_url=roh.get("apply_url") or roh.get("url"),
            quell_kategorie=kategorie,
            abruf_zeitpunkt=aktueller_zeitpunkt_utc(),
        )
