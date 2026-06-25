"""JSearch (RapidAPI) - https://jsearch.p.rapidapi.com

Aggregiert Google for Jobs, LinkedIn, Indeed, Glassdoor.
Monatliches Limit: 200 Anfragen/Monat (Free Plan).
Alert bei 80% (160 Anfragen). Drei Queries pro Lauf (je 1 API-Call).
num_pages=5 liefert 50 Ergebnisse pro API-Call ohne Mehrkosten.
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Iterator, List, Optional

from djr_core.exceptions import QuotaErschoepftFehler
from djr_core.logging import get_logger
from djr_core.models import JobQuelle, RohStellenanzeige
from djr_core.utils import aktueller_zeitpunkt_utc

from ingestion.base.client import BasisQuelleClient, QuelleSeite, Suchanfrage
from ingestion.quota.tracker import QuotaTracker

_logger = get_logger("ingestion.jsearch.client")

_RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
_GRENZE = int(os.getenv("JSEARCH_QUOTA_GRENZE", "200"))
_BASIS_URL = "https://jsearch.p.rapidapi.com/search-v2"

_HEADERS = {
    "x-rapidapi-host": "jsearch.p.rapidapi.com",
    "x-rapidapi-key": _RAPIDAPI_KEY,
    "Content-Type": "application/json",
}


class JsearchClient(BasisQuelleClient):
    quelle = JobQuelle.JSEARCH

    STANDARD_ANFRAGEN = (
        Suchanfrage("it_dev_de", "software developer engineer", "Software Stellen Deutschland (JSearch)"),
        Suchanfrage("data_de", "data scientist analyst engineer", "Data Stellen Deutschland (JSearch)"),
        Suchanfrage("informatik_de", "informatik IT systems architect", "Informatik Stellen Deutschland (JSearch)"),
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._quota = QuotaTracker(
            api_name="jsearch",
            grenze=_GRENZE,
            warnschwelle=0.80,
            monatlich=True,
        )

    def standard_suchanfragen(self) -> List[Suchanfrage]:
        return list(self.STANDARD_ANFRAGEN)

    def quota_stand(self) -> dict:
        return self._quota.stand()

    def seiten_abrufen(
        self,
        anfrage: Suchanfrage,
        *,
        max_seiten: int,
        startseite: int = 1,
    ) -> Iterator[QuelleSeite]:
        if not _RAPIDAPI_KEY:
            _logger.warning("jsearch_kein_api_key")
            return

        if self._quota.ist_erschoepft():
            raise QuotaErschoepftFehler(
                "JSearch-Monatsquota erschoepft",
                kontext={"grenze": _GRENZE, **self._quota.stand()},
            )

        # 1 API-Call pro Query; num_pages=5 liefert bis zu 50 Ergebnisse
        daten = self._abrufen(query=anfrage.query, seite=startseite)
        jobs = daten.get("data", {}).get("jobs", [])

        anzeigen: List[RohStellenanzeige] = []
        for roh in jobs:
            if not isinstance(roh, dict):
                continue
            mapped = self._mappen(roh, anfrage.kategorie)
            if mapped:
                anzeigen.append(mapped)

        yield QuelleSeite(
            quelle=self.quelle,
            seite=startseite,
            anzeigen=anzeigen,
            gesamt_geschaetzt=len(anzeigen),
            abruf_zeitpunkt=time.time(),
            quell_kategorie=anfrage.kategorie,
        )

    def _abrufen(self, *, query: str, seite: int) -> dict[str, Any]:
        headers = {**_HEADERS, "x-rapidapi-key": _RAPIDAPI_KEY}

        @self._retry
        def aufrufen() -> dict[str, Any]:
            antwort = self._client.get(
                _BASIS_URL,
                params={
                    "query": query,
                    "page": str(seite),
                    "num_pages": "5",
                    "country": "de",
                    "date_posted": "all",
                },
                headers=headers,
            )
            if antwort.status_code == 404:
                _logger.warning(
                    "jsearch_endpoint_nicht_verfuegbar",
                    extra={"antwort": antwort.text[:200]},
                )
                return {"data": {"jobs": []}}
            self._quota.hinzufuegen(1)
            return self._antwort_verarbeiten(
                antwort, kontext={"quelle": "jsearch", "query": query, "seite": seite}
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

    def _mappen(self, roh: dict[str, Any], kategorie: str) -> Optional[RohStellenanzeige]:
        quell_id = roh.get("job_id")
        titel = roh.get("job_title")
        if not quell_id or not titel:
            return None
        return RohStellenanzeige(
            quelle=self.quelle,
            quell_id=str(quell_id),
            titel=str(titel),
            beschreibung=str(roh.get("job_description") or ""),
            unternehmen=roh.get("employer_name"),
            standort_anzeige=f"{roh.get('job_city') or ''} {roh.get('job_country') or ''}".strip() or None,
            standort_segmente=[],
            stadt=roh.get("job_city"),
            bundesland=roh.get("job_state"),
            region="Remote" if roh.get("job_is_remote") else None,
            gehalt_min=float(roh["job_min_salary"]) if roh.get("job_min_salary") else None,
            gehalt_max=float(roh["job_max_salary"]) if roh.get("job_max_salary") else None,
            gehalt_ist_vorhanden=bool(roh.get("job_min_salary") or roh.get("job_max_salary")),
            waehrung=roh.get("job_salary_currency") or "EUR",
            vertragstyp=roh.get("job_employment_type"),
            vertragszeit=None,
            kategorie_kennung=roh.get("job_publisher"),
            kategorie_bezeichnung=roh.get("job_publisher"),
            veroeffentlicht_am=self._datum_parsen(roh.get("job_posted_at_datetime_utc")),
            angebots_url=roh.get("job_apply_link"),
            quell_kategorie=kategorie,
            abruf_zeitpunkt=aktueller_zeitpunkt_utc(),
        )
