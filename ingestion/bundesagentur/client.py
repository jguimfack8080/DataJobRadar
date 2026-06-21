"""Bundesagentur fuer Arbeit (BA) - offizielle deutsche Jobboerse.

Endpunkt: rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs
Default Anonymous Key: 'jobboerse-jobsuche' (oeffentlich bekannt, unverbindlich).
Kann ueber Env BA_API_KEY ueberschrieben werden, wenn ein registrierter Schluessel vorliegt.
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Iterator, List, Optional

import httpx

from djr_core.logging import get_logger
from djr_core.models import JobQuelle, RohStellenanzeige
from djr_core.utils import aktueller_zeitpunkt_utc

from ingestion.base.client import BasisQuelleClient, QuelleSeite, Suchanfrage

_logger = get_logger("ingestion.bundesagentur.client")

_BASIS_URL = os.getenv("BA_BASE_URL", "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs")
_API_KEY = os.getenv("BA_API_KEY", "jobboerse-jobsuche")
_SEITENGROESSE = int(os.getenv("BA_RESULTS_PER_PAGE", "50"))


class BundesagenturClient(BasisQuelleClient):
    """Client fuer die offizielle Jobsuche der Bundesagentur fuer Arbeit."""

    quelle = JobQuelle.BUNDESAGENTUR

    STANDARD_ANFRAGEN = (
        Suchanfrage("data_engineer", "Data Engineer", "Data Engineer Stellen"),
        Suchanfrage("data_scientist", "Data Scientist", "Data Scientist Stellen"),
        Suchanfrage("data_analyst", "Data Analyst", "Data Analyst Stellen"),
        Suchanfrage("ml_engineer", "Machine Learning Engineer", "ML Engineer Stellen"),
        Suchanfrage("bi_developer", "Business Intelligence", "BI Stellen"),
        Suchanfrage("data_architect", "Data Architect", "Data Architect Stellen"),
    )

    def __init__(self, http_client: Optional[httpx.Client] = None) -> None:
        super().__init__(
            timeout_seconds=30,
            max_retries=4,
            http_client=http_client or httpx.Client(
                timeout=httpx.Timeout(30),
                headers={
                    "Accept": "application/json",
                    "User-Agent": "data-job-radar/0.2",
                    "X-API-Key": _API_KEY,
                },
            ),
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
        for seite in range(startseite, startseite + max_seiten):
            antwort = self._seite_abrufen(seite=seite, query=anfrage.query)
            angebote = antwort.get("stellenangebote") or []
            anzeigen = [self._mappen(s, anfrage.kategorie) for s in angebote if isinstance(s, dict) and s.get("refnr")]
            gesamt = int(antwort.get("maxErgebnisse") or 0)

            yield QuelleSeite(
                quelle=self.quelle,
                seite=seite,
                anzeigen=anzeigen,
                gesamt_geschaetzt=gesamt,
                abruf_zeitpunkt=time.time(),
                quell_kategorie=anfrage.kategorie,
            )

            if not angebote:
                break
            if seite * _SEITENGROESSE >= gesamt:
                break

    def _seite_abrufen(self, *, seite: int, query: str) -> dict[str, Any]:
        @self._retry
        def aufrufen() -> dict[str, Any]:
            parameter = {
                "was": query,
                "wo": "Deutschland",
                "page": seite,
                "size": _SEITENGROESSE,
            }
            antwort = self._client.get(_BASIS_URL, params=parameter)
            return self._antwort_verarbeiten(
                antwort, kontext={"quelle": "bundesagentur", "seite": seite, "query": query}
            )

        return aufrufen()

    @staticmethod
    def _datum_parsen(wert: Any) -> Optional[datetime]:
        if not wert or not isinstance(wert, str):
            return None
        try:
            # BA-Format: "2026-06-15"
            return datetime.fromisoformat(wert)
        except ValueError:
            return None

    def _mappen(self, roh: dict[str, Any], kategorie: str) -> RohStellenanzeige:
        ort = roh.get("arbeitsort") or {}
        plz_und_ort = ort.get("ort")
        segmente = [s for s in (ort.get("region"), ort.get("land"), plz_und_ort) if s]
        refnr = str(roh["refnr"])
        angebots_url = f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"
        return RohStellenanzeige(
            quelle=self.quelle,
            quell_id=refnr,
            titel=str(roh.get("titel") or roh.get("beruf") or "Unbekannt").strip(),
            beschreibung="",
            unternehmen=roh.get("arbeitgeber"),
            standort_anzeige=plz_und_ort,
            standort_segmente=segmente,
            stadt=plz_und_ort,
            bundesland=ort.get("region"),
            region=ort.get("region"),
            breitengrad=ort.get("koordinaten", {}).get("lat") if isinstance(ort.get("koordinaten"), dict) else None,
            laengengrad=ort.get("koordinaten", {}).get("lon") if isinstance(ort.get("koordinaten"), dict) else None,
            gehalt_min=None,
            gehalt_max=None,
            gehalt_ist_vorhanden=False,
            waehrung="EUR",
            vertragstyp=None,
            vertragszeit=None,
            kategorie_kennung=roh.get("beruf"),
            kategorie_bezeichnung=roh.get("beruf"),
            veroeffentlicht_am=self._datum_parsen(
                roh.get("aktuelleVeroeffentlichungsdatum") or roh.get("eintrittsdatum")
            ),
            angebots_url=angebots_url,
            quell_kategorie=kategorie,
            abruf_zeitpunkt=aktueller_zeitpunkt_utc(),
        )
