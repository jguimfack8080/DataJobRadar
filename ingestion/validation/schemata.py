"""Schema-Validierung fuer Adzuna Rohdaten."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, List

from pydantic import ValidationError

from djr_core.models import RohStellenanzeige
from djr_core.utils import aktueller_zeitpunkt_utc


@dataclass
class ValidierungsErgebnis:
    gueltig: List[RohStellenanzeige] = field(default_factory=list)
    quarantaene: List[dict[str, Any]] = field(default_factory=list)

    @property
    def anzahl_gueltig(self) -> int:
        return len(self.gueltig)

    @property
    def anzahl_quarantaene(self) -> int:
        return len(self.quarantaene)


def _datum_parsen(wert: Any) -> datetime | None:
    if wert is None or wert == "":
        return None
    if isinstance(wert, datetime):
        return wert if wert.tzinfo else wert.replace(tzinfo=timezone.utc)
    if isinstance(wert, (int, float)):
        return datetime.fromtimestamp(float(wert), tz=timezone.utc)
    if isinstance(wert, str):
        try:
            normalisiert = wert.replace("Z", "+00:00")
            return datetime.fromisoformat(normalisiert)
        except ValueError:
            return None
    return None


def _treffer_in_rohanzeige(roh: dict[str, Any], *, quell_kategorie: str) -> RohStellenanzeige:
    unternehmen = (roh.get("company") or {}).get("display_name")
    standort = roh.get("location") or {}
    standort_anzeige = standort.get("display_name")
    standort_segmente = list(standort.get("area") or [])
    region = standort_segmente[1] if len(standort_segmente) > 1 else None
    kategorie = roh.get("category") or {}
    gehalt_min = roh.get("salary_min")
    gehalt_max = roh.get("salary_max")

    return RohStellenanzeige(
        adzuna_id=str(roh["id"]),
        titel=str(roh.get("title") or "").strip() or "Unbekannt",
        beschreibung=str(roh.get("description") or ""),
        unternehmen=unternehmen,
        standort_anzeige=standort_anzeige,
        standort_segmente=standort_segmente,
        region=region,
        breitengrad=roh.get("latitude"),
        laengengrad=roh.get("longitude"),
        gehalt_min=gehalt_min if isinstance(gehalt_min, (int, float)) else None,
        gehalt_max=gehalt_max if isinstance(gehalt_max, (int, float)) else None,
        gehalt_ist_vorhanden=bool(gehalt_min) or bool(gehalt_max),
        waehrung=roh.get("salary_currency") or "EUR",
        vertragstyp=roh.get("contract_type"),
        vertragszeit=roh.get("contract_time"),
        kategorie_kennung=kategorie.get("tag"),
        kategorie_bezeichnung=kategorie.get("label"),
        veroeffentlicht_am=_datum_parsen(roh.get("created")),
        angebots_url=roh.get("redirect_url"),
        quell_kategorie=quell_kategorie,
        abruf_zeitpunkt=aktueller_zeitpunkt_utc(),
        rohdaten_pfad=None,
    )


def validiere_adzuna_treffer(
    treffer: Iterable[dict[str, Any]],
    *,
    quell_kategorie: str,
) -> ValidierungsErgebnis:
    """Validiert eine Liste roher Adzuna-Treffer.

    Datensaetze, die das Schema verletzen, werden quarantaeniert statt
    stillschweigend verworfen. Die Funktion ist seiteneffektfrei.
    """
    ergebnis = ValidierungsErgebnis()

    for roh in treffer:
        if not isinstance(roh, dict) or "id" not in roh:
            ergebnis.quarantaene.append(
                {"grund": "id_fehlt", "datensatz": roh}
            )
            continue
        try:
            ergebnis.gueltig.append(
                _treffer_in_rohanzeige(roh, quell_kategorie=quell_kategorie)
            )
        except ValidationError as fehler:
            ergebnis.quarantaene.append(
                {
                    "grund": "schema_verletzung",
                    "datensatz": roh,
                    "fehler": fehler.errors(),
                }
            )

    return ergebnis
