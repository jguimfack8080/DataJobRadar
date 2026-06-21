"""Gemeinsame Basis fuer alle Quellen-Clients.

Stellt einheitliches Retry/Backoff-Verhalten, HTTP-Setup und Quotenkonzept bereit.
Jede konkrete Quelle implementiert nur die spezifische Mapping-Logik.
"""
from __future__ import annotations

import abc
import time
from dataclasses import dataclass
from typing import Any, Iterator, List, Optional

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from djr_core.exceptions import ExterneApiFehler, QuotaErschoepftFehler
from djr_core.logging import get_logger
from djr_core.models import JobQuelle, RohStellenanzeige

_logger = get_logger("ingestion.base.client")


@dataclass(frozen=True)
class Suchanfrage:
    kategorie: str
    query: str
    beschreibung: str


@dataclass(frozen=True)
class QuelleSeite:
    """Ergebnisseite einer beliebigen Quelle."""

    quelle: JobQuelle
    seite: int
    anzeigen: List[RohStellenanzeige]
    gesamt_geschaetzt: Optional[int]
    abruf_zeitpunkt: float
    quell_kategorie: str


class _TransienterFehler(ExterneApiFehler):
    code = "quelle_transient"


def _log_versuch(retry_state: RetryCallState) -> None:
    if retry_state.attempt_number > 1:
        _logger.warning(
            "quelle_wiederholung",
            versuch=retry_state.attempt_number,
            wartezeit=retry_state.next_action.sleep if retry_state.next_action else 0.0,
        )


class BasisQuelleClient(abc.ABC):
    """Abstrakte Basisklasse mit Retry/Backoff."""

    quelle: JobQuelle
    standardseiten_pro_kategorie: int = 5

    def __init__(
        self,
        *,
        timeout_seconds: int = 30,
        max_retries: int = 4,
        http_client: Optional[httpx.Client] = None,
        user_agent: str = "data-job-radar/0.2",
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._eigener_client = http_client is None
        self._client = http_client or httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            headers={"Accept": "application/json", "User-Agent": user_agent},
        )

    def __enter__(self) -> "BasisQuelleClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.schliessen()

    def schliessen(self) -> None:
        if self._eigener_client:
            self._client.close()

    # --- Pflicht-API jeder Subklasse --------------------------------------------------

    @abc.abstractmethod
    def standard_suchanfragen(self) -> List[Suchanfrage]:
        """Vorgegebene Suchen, falls der Aufrufer keine eigene Liste mitgibt."""

    @abc.abstractmethod
    def seiten_abrufen(
        self,
        anfrage: Suchanfrage,
        *,
        max_seiten: int,
        startseite: int = 1,
    ) -> Iterator[QuelleSeite]:
        """Iteriert ueber alle Ergebnis-Seiten dieser Suche."""

    # --- Gemeinsame Werkzeuge fuer Subklassen ----------------------------------------

    def _retry(self, fn):
        """Dekorator-Faktory fuer einheitliches Retry-Verhalten."""

        @retry(
            retry=retry_if_exception_type(_TransienterFehler),
            wait=wait_exponential_jitter(initial=1.0, max=30.0, jitter=1.5),
            stop=stop_after_attempt(self._max_retries + 1),
            before_sleep=_log_versuch,
            reraise=True,
        )
        def aufrufen(*args: Any, **kwargs: Any):
            return fn(*args, **kwargs)

        return aufrufen

    def _antwort_verarbeiten(
        self, antwort: httpx.Response, *, kontext: dict[str, Any]
    ) -> dict[str, Any]:
        if antwort.status_code == 200:
            try:
                return antwort.json()
            except ValueError as fehler:
                raise ExterneApiFehler(
                    "Antwort der Quelle war kein gueltiges JSON",
                    kontext=kontext,
                ) from fehler

        if antwort.status_code in (401, 403):
            raise QuotaErschoepftFehler(
                "Quelle lehnt den Zugriff ab (Quota oder Authentifizierung)",
                kontext={**kontext, "status": antwort.status_code},
            )

        if antwort.status_code == 429:
            wartezeit = self._wartezeit_aus_kopf(antwort) or 3.0
            time.sleep(wartezeit)
            raise _TransienterFehler(
                "Rate Limit erreicht",
                kontext={**kontext, "wartezeit": wartezeit},
            )

        if 500 <= antwort.status_code < 600:
            raise _TransienterFehler(
                "Quelle meldet Serverfehler",
                kontext={**kontext, "status": antwort.status_code},
            )

        raise ExterneApiFehler(
            "Unerwartete Antwort der Quelle",
            kontext={
                **kontext,
                "status": antwort.status_code,
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
