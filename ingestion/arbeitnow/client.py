"""Arbeitnow - https://www.arbeitnow.com/api/job-board-api

Kostenlos, kein API-Key. Auf den deutschen Markt ausgerichtet, auch englischsprachige
und Visa-Sponsoring-Stellen. Paginiert (25 Treffer pro Seite).
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Iterator, List, Optional

from djr_core.logging import get_logger
from djr_core.models import JobQuelle, RohStellenanzeige
from djr_core.utils import aktueller_zeitpunkt_utc

from ingestion.base.client import BasisQuelleClient, QuelleSeite, Suchanfrage

_logger = get_logger("ingestion.arbeitnow.client")

_BASIS_URL = "https://www.arbeitnow.com/api/job-board-api"

_RELEVANTE_TAGS = (
    "python", "data", "machine-learning", "ai", "sql", "analytics",
    "data-engineering", "data-science", "backend", "software-engineer",
    "java", "typescript", "cloud", "aws", "azure", "devops",
)


class ArbeitnowClient(BasisQuelleClient):
    quelle = JobQuelle.ARBEITNOW

    STANDARD_ANFRAGEN = (
        Suchanfrage("data_engineer", "data-engineering", "Data Engineering Stellen DE"),
        Suchanfrage("data_scientist", "data-science", "Data Science Stellen DE"),
        Suchanfrage("software_dev", "python", "Python Stellen DE"),
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
        for seitennr in range(startseite, startseite + max_seiten):
            daten = self._abrufen(tag=anfrage.query, seite=seitennr)
            treffer = daten.get("data") or []
            if not treffer:
                break

            anzeigen: List[RohStellenanzeige] = []
            for roh in treffer:
                if not isinstance(roh, dict):
                    continue
                anzeigen.append(self._mappen(roh, anfrage.kategorie))

            gesamt = daten.get("meta", {}).get("total", None)

            yield QuelleSeite(
                quelle=self.quelle,
                seite=seitennr,
                anzeigen=anzeigen,
                gesamt_geschaetzt=gesamt,
                abruf_zeitpunkt=time.time(),
                quell_kategorie=anfrage.kategorie,
            )

            letzte = daten.get("meta", {}).get("last_page") or daten.get("links", {}).get("next")
            if letzte and isinstance(letzte, int) and seitennr >= letzte:
                break
            if not daten.get("links", {}).get("next"):
                break

    def _abrufen(self, *, tag: str, seite: int) -> dict[str, Any]:
        @self._retry
        def aufrufen() -> dict[str, Any]:
            antwort = self._client.get(
                _BASIS_URL,
                params={"page": seite, "tag": tag},
            )
            return self._antwort_verarbeiten(
                antwort, kontext={"quelle": "arbeitnow", "tag": tag, "seite": seite}
            )
        return aufrufen()

    @staticmethod
    def _datum_parsen(wert: Any) -> Optional[datetime]:
        if not wert:
            return None
        if isinstance(wert, int):
            try:
                return datetime.fromtimestamp(wert, tz=timezone.utc)
            except (OSError, OverflowError):
                return None
        if isinstance(wert, str):
            try:
                return datetime.fromisoformat(wert.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _mappen(self, roh: dict[str, Any], kategorie: str) -> RohStellenanzeige:
        tags = roh.get("tags") or []
        return RohStellenanzeige(
            quelle=self.quelle,
            quell_id=str(roh.get("slug") or roh.get("id") or ""),
            titel=str(roh.get("title") or "Unbekannt"),
            beschreibung=str(roh.get("description") or ""),
            unternehmen=roh.get("company_name"),
            standort_anzeige=roh.get("location"),
            standort_segmente=[],
            stadt=roh.get("location") if roh.get("location") else None,
            bundesland=None,
            region="Remote" if roh.get("remote") else "Deutschland",
            gehalt_min=None,
            gehalt_max=None,
            gehalt_ist_vorhanden=False,
            waehrung="EUR",
            vertragstyp=", ".join(roh.get("job_types") or []) or None,
            vertragszeit=None,
            kategorie_kennung=tags[0] if tags else None,
            kategorie_bezeichnung=", ".join(tags[:3]) if tags else None,
            veroeffentlicht_am=self._datum_parsen(roh.get("created_at")),
            angebots_url=roh.get("url"),
            quell_kategorie=kategorie,
            abruf_zeitpunkt=aktueller_zeitpunkt_utc(),
        )
