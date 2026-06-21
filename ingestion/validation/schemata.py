"""Schema-Validierung fuer normalisierte Roh-Anzeigen."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List

from pydantic import ValidationError

from djr_core.models import RohStellenanzeige


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


def validiere_anzeigen(
    kandidaten: Iterable[RohStellenanzeige | dict[str, Any]],
) -> ValidierungsErgebnis:
    """Filtert Anzeigen, die ungueltig sind, in eine Quarantaene.

    Akzeptiert sowohl bereits gemappte `RohStellenanzeige` als auch Roh-Dicts
    (falls jemand direkt vom HTTP-Layer kommt).
    """
    ergebnis = ValidierungsErgebnis()
    for kandidat in kandidaten:
        if isinstance(kandidat, RohStellenanzeige):
            ergebnis.gueltig.append(kandidat)
            continue
        if not isinstance(kandidat, dict):
            ergebnis.quarantaene.append({"grund": "kein_dict", "datensatz": kandidat})
            continue
        try:
            anzeige = RohStellenanzeige.model_validate(kandidat)
        except ValidationError as fehler:
            ergebnis.quarantaene.append(
                {"grund": "schema_verletzung", "datensatz": kandidat, "fehler": fehler.errors()}
            )
            continue
        ergebnis.gueltig.append(anzeige)
    return ergebnis
