"""Adzuna-Quellen-Client.

Implementiert das gemeinsame Quellen-Protokoll und mappt Adzuna-spezifische
Felder auf das generische `RohStellenanzeige`-Modell.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Iterator, List, Optional

import httpx

from djr_core.config import AdzunaSettings, get_settings
from djr_core.logging import get_logger
from djr_core.models import JobQuelle, RohStellenanzeige
from djr_core.utils import aktueller_zeitpunkt_utc

from ingestion.base.client import BasisQuelleClient, QuelleSeite, Suchanfrage

_logger = get_logger("ingestion.adzuna.client")


class AdzunaClient(BasisQuelleClient):
    """Synchroner Adzuna API Client mit Backoff und Quota-Erkennung."""

    quelle = JobQuelle.ADZUNA

    STANDARD_ANFRAGEN = (
        Suchanfrage("data_engineer", "data engineer", "Data Engineer Stellen"),
        Suchanfrage("data_scientist", "data scientist", "Data Scientist Stellen"),
        Suchanfrage("data_analyst", "data analyst", "Data Analyst Stellen"),
        Suchanfrage("ml_engineer", "machine learning engineer", "ML Engineer Stellen"),
        Suchanfrage("analytics_engineer", "analytics engineer", "Analytics Engineer Stellen"),
        Suchanfrage("bi_developer", "business intelligence", "BI Developer Stellen"),
        Suchanfrage("data_architect", "data architect", "Data Architect Stellen"),
        Suchanfrage("cloud_data_engineer", "cloud data engineer", "Cloud Data Engineer Stellen"),
    )

    def __init__(
        self,
        einstellungen: Optional[AdzunaSettings] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self._einstellungen = einstellungen or get_settings().adzuna
        super().__init__(
            timeout_seconds=self._einstellungen.timeout_seconds,
            max_retries=self._einstellungen.max_retries,
            http_client=http_client,
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
        if max_seiten < 1:
            raise ValueError("max_seiten muss mindestens 1 sein")

        for seite in range(startseite, startseite + max_seiten):
            roh_antwort = self._seite_abrufen(seite=seite, query=anfrage.query)
            treffer = roh_antwort.get("results") or []
            gesamt = int(roh_antwort.get("count") or 0)
            anzeigen = [self._mappen(t, anfrage.kategorie) for t in treffer if isinstance(t, dict) and "id" in t]

            yield QuelleSeite(
                quelle=self.quelle,
                seite=seite,
                anzeigen=anzeigen,
                gesamt_geschaetzt=gesamt,
                abruf_zeitpunkt=time.time(),
                quell_kategorie=anfrage.kategorie,
            )

            if not treffer:
                _logger.info("adzuna_keine_weiteren_treffer", seite=seite, kategorie=anfrage.kategorie)
                break

            if seite * self._einstellungen.results_per_page >= gesamt:
                break

    def _seite_abrufen(self, *, seite: int, query: str) -> dict[str, Any]:
        @self._retry
        def aufrufen() -> dict[str, Any]:
            url = (
                f"{self._einstellungen.base_url.rstrip('/')}"
                f"/jobs/{self._einstellungen.country}/search/{seite}"
            )
            parameter = {
                "app_id": self._einstellungen.app_id,
                "app_key": self._einstellungen.app_key,
                "results_per_page": self._einstellungen.results_per_page,
                "what": query,
                "content-type": "application/json",
            }
            antwort = self._client.get(url, params=parameter)
            return self._antwort_verarbeiten(
                antwort, kontext={"quelle": "adzuna", "seite": seite, "query": query}
            )

        return aufrufen()

    @staticmethod
    def _datum_parsen(wert: Any) -> Optional[datetime]:
        if not wert:
            return None
        if isinstance(wert, datetime):
            return wert if wert.tzinfo else wert.replace(tzinfo=timezone.utc)
        if isinstance(wert, str):
            try:
                return datetime.fromisoformat(wert.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _mappen(self, roh: dict[str, Any], kategorie: str) -> RohStellenanzeige:
        unternehmen = (roh.get("company") or {}).get("display_name")
        standort = roh.get("location") or {}
        segmente = list(standort.get("area") or [])
        # Adzuna: area = [Land, Bundesland, Region, Stadt] (in absteigender Spezifitaet wechselnd)
        stadt = segmente[3] if len(segmente) > 3 else (segmente[2] if len(segmente) > 2 else None)
        bundesland = segmente[1] if len(segmente) > 1 else None
        kat = roh.get("category") or {}
        return RohStellenanzeige(
            quelle=self.quelle,
            quell_id=str(roh["id"]),
            titel=str(roh.get("title") or "").strip() or "Unbekannt",
            beschreibung=str(roh.get("description") or ""),
            unternehmen=unternehmen,
            standort_anzeige=standort.get("display_name"),
            standort_segmente=segmente,
            stadt=stadt,
            bundesland=bundesland,
            region=segmente[1] if len(segmente) > 1 else None,
            breitengrad=roh.get("latitude"),
            laengengrad=roh.get("longitude"),
            gehalt_min=roh.get("salary_min") if isinstance(roh.get("salary_min"), (int, float)) else None,
            gehalt_max=roh.get("salary_max") if isinstance(roh.get("salary_max"), (int, float)) else None,
            gehalt_ist_vorhanden=bool(roh.get("salary_min")) or bool(roh.get("salary_max")),
            waehrung=roh.get("salary_currency") or "EUR",
            vertragstyp=roh.get("contract_type"),
            vertragszeit=roh.get("contract_time"),
            kategorie_kennung=kat.get("tag"),
            kategorie_bezeichnung=kat.get("label"),
            veroeffentlicht_am=self._datum_parsen(roh.get("created")),
            angebots_url=roh.get("redirect_url"),
            quell_kategorie=kategorie,
            abruf_zeitpunkt=aktueller_zeitpunkt_utc(),
        )
