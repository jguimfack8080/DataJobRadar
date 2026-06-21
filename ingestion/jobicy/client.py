"""Jobicy - https://jobicy.com/api/v2/remote-jobs

Liefert globale Remote-Stellen. Filter auf Deutschland/Europe/Worldwide/Anywhere wie bei Remotive.
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

_logger = get_logger("ingestion.jobicy.client")

_BASIS_URL = "https://jobicy.com/api/v2/remote-jobs"
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


class JobicyClient(BasisQuelleClient):
    quelle = JobQuelle.JOBICY

    STANDARD_ANFRAGEN = (
        Suchanfrage("data_engineer", "data-science", "Remote Data Engineer Stellen"),
        Suchanfrage("software_dev", "dev-engineering", "Remote Software Engineering Stellen"),
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
        antwort = self._abrufen(industry=anfrage.query)
        jobs = antwort.get("jobs") or []
        anzeigen: List[RohStellenanzeige] = []
        for roh in jobs:
            if not isinstance(roh, dict) or not roh.get("id"):
                continue
            geo = (roh.get("jobGeo") or "").lower()
            if not (
                geo.strip() == ""
                or any(stichwort in geo for stichwort in _RELEVANTE_LOCATIONS)
            ):
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

    def _abrufen(self, *, industry: str) -> dict[str, Any]:
        @self._retry
        def aufrufen() -> dict[str, Any]:
            antwort = self._client.get(_BASIS_URL, params={"industry": industry, "count": 100})
            return self._antwort_verarbeiten(
                antwort, kontext={"quelle": "jobicy", "industry": industry}
            )

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
        return RohStellenanzeige(
            quelle=self.quelle,
            quell_id=str(roh["id"]),
            titel=str(roh.get("jobTitle") or "Unbekannt"),
            beschreibung=str(roh.get("jobDescription") or ""),
            unternehmen=roh.get("companyName"),
            standort_anzeige=roh.get("jobGeo"),
            standort_segmente=[],
            stadt=None,
            bundesland=None,
            region="Remote",
            gehalt_min=float(roh["salaryMin"]) if roh.get("salaryMin") else None,
            gehalt_max=float(roh["salaryMax"]) if roh.get("salaryMax") else None,
            gehalt_ist_vorhanden=bool(roh.get("salaryMin") or roh.get("salaryMax")),
            waehrung=roh.get("salaryCurrency") or "EUR",
            vertragstyp=roh.get("jobType"),
            vertragszeit=None,
            kategorie_kennung=roh.get("jobIndustry"),
            kategorie_bezeichnung=roh.get("jobIndustry"),
            veroeffentlicht_am=self._datum_parsen(roh.get("pubDate")),
            angebots_url=roh.get("url"),
            quell_kategorie=kategorie,
            abruf_zeitpunkt=aktueller_zeitpunkt_utc(),
        )
