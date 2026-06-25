"""The Muse - https://www.themuse.com/api/public/jobs

Anonyme Calls funktionieren ohne API-Schluessel, sind aber rate-limited.
Optionaler Key via MUSE_API_KEY.
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

_logger = get_logger("ingestion.muse.client")

_BASIS_URL = "https://www.themuse.com/api/public/jobs"
_API_KEY = os.getenv("MUSE_API_KEY")


class MuseClient(BasisQuelleClient):
    quelle = JobQuelle.MUSE

    STANDARD_ANFRAGEN = (
        Suchanfrage("software_engineer", "Software Engineering", "Software Engineering Stellen"),
        Suchanfrage("science_engineering", "Science and Engineering", "Science and Engineering Stellen"),
        Suchanfrage("data_analytics", "Data and Analytics", "Data und Analytics Stellen"),
        Suchanfrage("it", "IT", "IT Stellen"),
    )

    def __init__(self, http_client: Optional[httpx.Client] = None) -> None:
        super().__init__(timeout_seconds=30, max_retries=3, http_client=http_client)

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
            antwort = self._seite_abrufen(seite=seite, kategorie_label=anfrage.query)
            results = antwort.get("results") or []
            anzeigen = [
                self._mappen(r, anfrage.kategorie)
                for r in results
                if isinstance(r, dict) and r.get("id")
            ]
            seitencount = int(antwort.get("page_count") or 1)
            yield QuelleSeite(
                quelle=self.quelle,
                seite=seite,
                anzeigen=anzeigen,
                gesamt_geschaetzt=int(antwort.get("page_count") or 0) * 20,
                abruf_zeitpunkt=time.time(),
                quell_kategorie=anfrage.kategorie,
            )
            if not results or seite >= seitencount:
                break

    def _seite_abrufen(self, *, seite: int, kategorie_label: str) -> dict[str, Any]:
        @self._retry
        def aufrufen() -> dict[str, Any]:
            parameter = {
                "page": seite,
                "category": kategorie_label,
            }
            if _API_KEY:
                parameter["api_key"] = _API_KEY
            antwort = self._client.get(_BASIS_URL, params=parameter)
            return self._antwort_verarbeiten(
                antwort, kontext={"quelle": "muse", "seite": seite, "kategorie": kategorie_label}
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
        unternehmen = (roh.get("company") or {}).get("name")
        locations = roh.get("locations") or []
        location_name = locations[0].get("name") if locations else None
        stadt = (location_name or "").split(",")[0].strip() or None
        kats = roh.get("categories") or []
        kat_label = kats[0].get("name") if kats else None
        return RohStellenanzeige(
            quelle=self.quelle,
            quell_id=str(roh["id"]),
            titel=str(roh.get("name") or "Unbekannt"),
            beschreibung=str(roh.get("contents") or ""),
            unternehmen=unternehmen,
            standort_anzeige=location_name,
            standort_segmente=[stadt] if stadt else [],
            stadt=stadt,
            bundesland=None,
            region=None,
            gehalt_min=None,
            gehalt_max=None,
            gehalt_ist_vorhanden=False,
            waehrung="EUR",
            vertragstyp=roh.get("type"),
            vertragszeit=None,
            kategorie_kennung=kat_label,
            kategorie_bezeichnung=kat_label,
            veroeffentlicht_am=self._datum_parsen(roh.get("publication_date")),
            angebots_url=(roh.get("refs") or {}).get("landing_page"),
            quell_kategorie=kategorie,
            abruf_zeitpunkt=aktueller_zeitpunkt_utc(),
        )
