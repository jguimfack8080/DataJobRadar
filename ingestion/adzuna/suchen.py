"""Suchstrategien fuer den deutschen Data-Engineering-Markt."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class Suchanfrage:
    """Repraesentiert eine konkrete Suchanfrage an Adzuna."""

    kategorie: str
    query: str
    beschreibung: str


class StandardSuchstrategie:
    """Liefert eine kuratierte Liste relevanter Suchanfragen.

    Die Strategie ist erweiterbar. Neue Kategorien koennen ohne Codeaenderung
    durch Hinzufuegen weiterer Eintraege ergaenzt werden.
    """

    _ANFRAGEN: tuple[Suchanfrage, ...] = (
        Suchanfrage("data_engineer", "data engineer", "Data Engineer Stellen"),
        Suchanfrage("data_scientist", "data scientist", "Data Scientist Stellen"),
        Suchanfrage("data_analyst", "data analyst", "Data Analyst Stellen"),
        Suchanfrage("ml_engineer", "machine learning engineer", "ML Engineer Stellen"),
        Suchanfrage("analytics_engineer", "analytics engineer", "Analytics Engineer Stellen"),
        Suchanfrage("bi_developer", "business intelligence", "BI Developer Stellen"),
        Suchanfrage("data_architect", "data architect", "Data Architect Stellen"),
        Suchanfrage("cloud_data_engineer", "cloud data engineer", "Cloud Data Engineer Stellen"),
    )

    def anfragen(self) -> List[Suchanfrage]:
        return list(self._ANFRAGEN)

    @classmethod
    def aus_kategorien(cls, kategorien: Iterable[str]) -> List[Suchanfrage]:
        zugeordnet = {anfrage.kategorie: anfrage for anfrage in cls._ANFRAGEN}
        return [zugeordnet[kategorie] for kategorie in kategorien if kategorie in zugeordnet]
