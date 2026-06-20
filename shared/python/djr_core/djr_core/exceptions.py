"""Fachliche Ausnahmen der Plattform mit deutschsprachigen Meldungen."""
from __future__ import annotations

from typing import Any


class DJRError(Exception):
    """Basisklasse fuer alle fachlichen Ausnahmen."""

    code: str = "djr_fehler"

    def __init__(self, meldung: str, *, kontext: dict[str, Any] | None = None) -> None:
        super().__init__(meldung)
        self.meldung = meldung
        self.kontext = kontext or {}

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "meldung": self.meldung, "kontext": self.kontext}


class KonfigurationsFehler(DJRError):
    code = "konfigurationsfehler"


class ValidierungsFehler(DJRError):
    code = "validierungsfehler"


class DatenqualitaetsFehler(DJRError):
    code = "datenqualitaetsfehler"


class ExterneApiFehler(DJRError):
    code = "externe_api_fehler"


class QuotaErschoepftFehler(ExterneApiFehler):
    code = "quota_erschoepft"


class NichtGefundenFehler(DJRError):
    code = "nicht_gefunden"
