"""Skill-Extraktion aus Jobbeschreibungen.

Die Erkennung basiert auf vorab kompilierten regulaeren Ausdruecken mit
Wortgrenzenpruefung. Dadurch werden Fehltreffer in zusammengesetzten
Woertern vermieden (z.B. `rsync` bei der Suche nach `R`).
"""
from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence

from skills.taxonomie import SkillEintrag, lade_standard_taxonomie


class SkillExtraktor:
    """Extrahiert kanonische Skill-Bezeichnungen aus einem Text."""

    def __init__(self, taxonomie: Optional[Sequence[SkillEintrag]] = None) -> None:
        self._eintraege: List[SkillEintrag] = list(taxonomie or lade_standard_taxonomie())
        self._muster: list[tuple[SkillEintrag, re.Pattern[str]]] = []
        for eintrag in self._eintraege:
            varianten = [re.escape(eintrag.kanonisch), *map(re.escape, eintrag.synonyme)]
            ausdruck = r"(?<![A-Za-z0-9_\+\#])(?:" + "|".join(varianten) + r")(?![A-Za-z0-9_\+\#])"
            self._muster.append((eintrag, re.compile(ausdruck, re.IGNORECASE)))

    def extrahieren(self, text: str | None) -> List[str]:
        if not text:
            return []
        gefunden: List[str] = []
        bereits = set()
        for eintrag, muster in self._muster:
            if muster.search(text) and eintrag.kanonisch not in bereits:
                gefunden.append(eintrag.kanonisch)
                bereits.add(eintrag.kanonisch)
        return gefunden

    def viele_extrahieren(self, texte: Iterable[str]) -> List[List[str]]:
        return [self.extrahieren(text) for text in texte]

    def kategorisieren(self, skill: str) -> Optional[str]:
        for eintrag in self._eintraege:
            if eintrag.kanonisch.lower() == skill.lower():
                return eintrag.kategorie
        return None

    def kanonische_skills(self) -> List[str]:
        return [eintrag.kanonisch for eintrag in self._eintraege]
