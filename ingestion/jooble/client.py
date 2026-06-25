"""Jooble REST API - https://jooble.org/api

POST-basiert. Konfiguriertes Lifetime-Limit von 500 Anfragen (Standard).
Bei 80% (400 Anfragen) wird eine Warn-E-Mail gesendet.
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

_logger = get_logger("ingestion.jooble.client")

_API_KEY = os.getenv("JOOBLE_API_KEY", "")
_GRENZE = int(os.getenv("JOOBLE_QUOTA_GRENZE", "500"))
_BASIS_URL_TPL = "https://jooble.org/api/{key}"


class JoobleClient(BasisQuelleClient):
    quelle = JobQuelle.JOOBLE

    STANDARD_ANFRAGEN = (
        Suchanfrage("data_engineer", "data engineer", "Data Engineering Stellen (Jooble DE)"),
        Suchanfrage("data_scientist", "data scientist", "Data Science Stellen (Jooble DE)"),
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._quota = QuotaTracker(
            api_name="jooble",
            grenze=_GRENZE,
            warnschwelle=0.80,
            monatlich=False,
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
        if not _API_KEY:
            _logger.warning("jooble_kein_api_key")
            return

        if self._quota.ist_erschoepft():
            raise QuotaErschoepftFehler(
                "Jooble-Quota erschoepft",
                kontext={"grenze": _GRENZE, **self._quota.stand()},
            )

        for seitennr in range(startseite, startseite + max_seiten):
            daten = self._abrufen(keywords=anfrage.query, seite=seitennr)
            jobs = daten.get("jobs") or []
            if not jobs:
                break

            anzeigen = [self._mappen(roh, anfrage.kategorie) for roh in jobs if isinstance(roh, dict)]

            gesamt = daten.get("totalCount")

            yield QuelleSeite(
                quelle=self.quelle,
                seite=seitennr,
                anzeigen=anzeigen,
                gesamt_geschaetzt=gesamt,
                abruf_zeitpunkt=time.time(),
                quell_kategorie=anfrage.kategorie,
            )

            if gesamt and seitennr * 20 >= gesamt:
                break

    def _abrufen(self, *, keywords: str, seite: int) -> dict[str, Any]:
        url = _BASIS_URL_TPL.format(key=_API_KEY)

        @self._retry
        def aufrufen() -> dict[str, Any]:
            antwort = self._client.post(
                url,
                json={
                    "keywords": keywords,
                    "location": "Germany",
                    "page": seite,
                    "resultonpage": 20,
                },
                headers={"Content-Type": "application/json"},
            )
            self._quota.hinzufuegen(1)
            return self._antwort_verarbeiten(
                antwort, kontext={"quelle": "jooble", "keywords": keywords, "seite": seite}
            )

        return aufrufen()

    @staticmethod
    def _datum_parsen(wert: Any) -> Optional[datetime]:
        if not wert or not isinstance(wert, str):
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(wert[:19], fmt)
            except ValueError:
                continue
        return None

    def _mappen(self, roh: dict[str, Any], kategorie: str) -> RohStellenanzeige:
        return RohStellenanzeige(
            quelle=self.quelle,
            quell_id=str(roh.get("id") or ""),
            titel=str(roh.get("title") or "Unbekannt"),
            beschreibung=str(roh.get("snippet") or ""),
            unternehmen=roh.get("company"),
            standort_anzeige=roh.get("location"),
            standort_segmente=[],
            stadt=roh.get("location"),
            bundesland=None,
            region=None,
            gehalt_min=None,
            gehalt_max=None,
            gehalt_ist_vorhanden=bool(roh.get("salary")),
            waehrung="EUR",
            vertragstyp=roh.get("type"),
            vertragszeit=None,
            kategorie_kennung=None,
            kategorie_bezeichnung=None,
            veroeffentlicht_am=self._datum_parsen(roh.get("updated")),
            angebots_url=roh.get("link"),
            quell_kategorie=kategorie,
            abruf_zeitpunkt=aktueller_zeitpunkt_utc(),
        )
