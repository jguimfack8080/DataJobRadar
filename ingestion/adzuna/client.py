"""Robuster Adzuna API Client mit Backoff und Quota-Erkennung."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Iterator, Optional

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from djr_core.config import AdzunaSettings, get_settings
from djr_core.exceptions import ExterneApiFehler, QuotaErschoepftFehler
from djr_core.logging import get_logger

_logger = get_logger("ingestion.adzuna.client")


@dataclass(frozen=True)
class AdzunaSeite:
    """Repraesentiert eine Ergebnisseite der Adzuna API."""

    seite: int
    treffer: list[dict[str, Any]]
    gesamt: int
    abruf_zeitpunkt: float
    quell_kategorie: str


class _TransienterFehler(ExterneApiFehler):
    code = "adzuna_transient"


def _log_versuch(retry_state: RetryCallState) -> None:
    """Strukturierte Protokollierung jedes Wiederholungsversuchs."""
    if retry_state.attempt_number > 1:
        _logger.warning(
            "adzuna_wiederholung",
            versuch=retry_state.attempt_number,
            wartezeit=retry_state.next_action.sleep if retry_state.next_action else 0.0,
        )


class AdzunaClient:
    """Synchroner Adzuna API Client.

    Idempotent: gleiche Anfrageparameter erzeugen dasselbe Ergebnis. Liefert
    Seiten als Iterator zurueck, damit Konsumenten streamen koennen.
    """

    def __init__(
        self,
        einstellungen: Optional[AdzunaSettings] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self._einstellungen = einstellungen or get_settings().adzuna
        self._eigener_client = http_client is None
        self._client = http_client or httpx.Client(
            timeout=httpx.Timeout(self._einstellungen.timeout_seconds),
            headers={"Accept": "application/json", "User-Agent": "data-job-radar/0.1"},
        )

    def __enter__(self) -> "AdzunaClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.schliessen()

    def schliessen(self) -> None:
        if self._eigener_client:
            self._client.close()

    def seiten_abrufen(
        self,
        such_query: str,
        *,
        kategorie: str,
        max_seiten: int = 20,
        startseite: int = 1,
    ) -> Iterator[AdzunaSeite]:
        """Iteriert ueber Suchergebnisseiten der Adzuna API."""
        if max_seiten < 1:
            raise ValueError("max_seiten muss mindestens 1 sein")

        for seite in range(startseite, startseite + max_seiten):
            antwort = self._seite_abrufen(seite=seite, query=such_query)
            treffer = antwort.get("results") or []
            gesamt = int(antwort.get("count") or 0)

            yield AdzunaSeite(
                seite=seite,
                treffer=treffer,
                gesamt=gesamt,
                abruf_zeitpunkt=time.time(),
                quell_kategorie=kategorie,
            )

            if not treffer:
                _logger.info("adzuna_keine_weiteren_treffer", seite=seite, kategorie=kategorie)
                break

            if seite * self._einstellungen.results_per_page >= gesamt:
                _logger.info(
                    "adzuna_gesamt_erreicht",
                    seite=seite,
                    kategorie=kategorie,
                    gesamt=gesamt,
                )
                break

    def _seite_abrufen(self, *, seite: int, query: str) -> dict[str, Any]:
        @retry(
            retry=retry_if_exception_type(_TransienterFehler),
            wait=wait_exponential_jitter(initial=1.0, max=30.0, jitter=1.5),
            stop=stop_after_attempt(self._einstellungen.max_retries + 1),
            before_sleep=_log_versuch,
            reraise=True,
        )
        def _aufrufen() -> dict[str, Any]:
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
            return self._antwort_verarbeiten(antwort, seite=seite, query=query)

        return _aufrufen()

    def _antwort_verarbeiten(
        self, antwort: httpx.Response, *, seite: int, query: str
    ) -> dict[str, Any]:
        if antwort.status_code == 200:
            try:
                return antwort.json()
            except ValueError as fehler:
                raise ExterneApiFehler(
                    "Antwort der Adzuna API war kein gueltiges JSON",
                    kontext={"seite": seite, "query": query},
                ) from fehler

        if antwort.status_code in (401, 403):
            raise QuotaErschoepftFehler(
                "Adzuna lehnt den Zugriff ab (Quota oder Authentifizierung)",
                kontext={"status": antwort.status_code, "seite": seite, "query": query},
            )

        if antwort.status_code == 429:
            wartezeit = self._wartezeit_aus_kopf(antwort) or random.uniform(2.0, 5.0)
            _logger.warning("adzuna_rate_limit", wartezeit=wartezeit, seite=seite)
            time.sleep(wartezeit)
            raise _TransienterFehler(
                "Adzuna Rate Limit erreicht",
                kontext={"seite": seite, "wartezeit": wartezeit},
            )

        if 500 <= antwort.status_code < 600:
            raise _TransienterFehler(
                "Adzuna meldet Serverfehler",
                kontext={"status": antwort.status_code, "seite": seite},
            )

        raise ExterneApiFehler(
            "Unerwartete Antwort der Adzuna API",
            kontext={
                "status": antwort.status_code,
                "seite": seite,
                "query": query,
                "text_auszug": antwort.text[:200],
            },
        )

    @staticmethod
    def _wartezeit_aus_kopf(antwort: httpx.Response) -> Optional[float]:
        wert = antwort.headers.get("Retry-After")
        if not wert:
            return None
        try:
            return float(wert)
        except (TypeError, ValueError):
            return None
