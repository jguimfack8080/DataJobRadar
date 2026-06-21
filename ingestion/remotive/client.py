"""Remotive - https://remotive.com/api/remote-jobs

Liefert eine globale Liste Remote-Stellen. Wir filtern auf Deutschland/Europe/Worldwide/Anywhere.
Quotenfrei, aber moeglicherweise hohe Antwortzeit, da kein Pagination-Konzept.
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Iterator, List, Optional

import httpx

from djr_core.logging import get_logger
from djr_core.models import JobQuelle, RohStellenanzeige
from djr_core.utils import aktueller_zeitpunkt_utc

from ingestion.base.client import BasisQuelleClient, QuelleSeite, Suchanfrage

_logger = get_logger("ingestion.remotive.client")

_BASIS_URL = "https://remotive.com/api/remote-jobs"
_RELEVANTE_LOCATIONS = (
    "germany",
    "deutschland",
    "europe",
    "european",
    "eu",
    "emea",
    "worldwide",
    "anywhere",
)


class RemotiveClient(BasisQuelleClient):
    quelle = JobQuelle.REMOTIVE

    STANDARD_ANFRAGEN = (
        Suchanfrage("data_engineer", "data engineer", "Remote Data Engineer Stellen"),
        Suchanfrage("data_scientist", "data scientist", "Remote Data Scientist Stellen"),
        Suchanfrage("software_dev", "software-dev", "Remote Software Engineering Stellen"),
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
        # Remotive liefert immer alle Treffer in einem Aufruf.
        antwort = self._abrufen(such=anfrage.query)
        jobs = antwort.get("jobs") or []
        anzeigen: List[RohStellenanzeige] = []
        for roh in jobs:
            if not isinstance(roh, dict) or not roh.get("id"):
                continue
            if not self._ist_relevant(roh.get("candidate_required_location") or ""):
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

    def _abrufen(self, *, such: str) -> dict[str, Any]:
        @self._retry
        def aufrufen() -> dict[str, Any]:
            antwort = self._client.get(_BASIS_URL, params={"search": such, "limit": 100})
            return self._antwort_verarbeiten(
                antwort, kontext={"quelle": "remotive", "search": such}
            )

        return aufrufen()

    @staticmethod
    def _ist_relevant(location: str) -> bool:
        l = location.lower()
        return any(stichwort in l for stichwort in _RELEVANTE_LOCATIONS) or l.strip() == ""

    @staticmethod
    def _datum_parsen(wert: Any) -> Optional[datetime]:
        if not wert or not isinstance(wert, str):
            return None
        try:
            return datetime.fromisoformat(wert.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _mappen(self, roh: dict[str, Any], kategorie: str) -> RohStellenanzeige:
        return RohStellenanzeige(
            quelle=self.quelle,
            quell_id=str(roh["id"]),
            titel=str(roh.get("title") or "Unbekannt"),
            beschreibung=str(roh.get("description") or ""),
            unternehmen=roh.get("company_name"),
            standort_anzeige=roh.get("candidate_required_location"),
            standort_segmente=[],
            stadt=None,
            bundesland=None,
            region="Remote",
            gehalt_min=None,
            gehalt_max=None,
            gehalt_ist_vorhanden=bool(roh.get("salary")),
            waehrung="EUR",
            vertragstyp=roh.get("job_type"),
            vertragszeit=None,
            kategorie_kennung=roh.get("category"),
            kategorie_bezeichnung=roh.get("category"),
            veroeffentlicht_am=self._datum_parsen(roh.get("publication_date")),
            angebots_url=roh.get("url"),
            quell_kategorie=kategorie,
            abruf_zeitpunkt=aktueller_zeitpunkt_utc(),
        )
