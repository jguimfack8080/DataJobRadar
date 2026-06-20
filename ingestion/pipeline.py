"""Orchestrierter Ingestion-Lauf von Adzuna in die Bronze-Schicht."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, List, Optional

from djr_core.config import get_settings
from djr_core.exceptions import QuotaErschoepftFehler
from djr_core.logging import get_logger
from djr_core.utils import aktueller_zeitpunkt_utc, neue_korrelationskennung

from data_lake.bronze.schreiber import BronzeSchreiber
from ingestion.adzuna.client import AdzunaClient
from ingestion.adzuna.suchen import StandardSuchstrategie, Suchanfrage
from ingestion.validation.schemata import validiere_adzuna_treffer

_logger = get_logger("ingestion.pipeline")


@dataclass
class LaufBericht:
    """Berichtskennzahlen eines Ingestion-Laufs."""

    korrelationskennung: str
    geladene_seiten: int = 0
    geladene_treffer: int = 0
    gueltige_treffer: int = 0
    quarantaenierte_treffer: int = 0
    kategorien: List[str] = field(default_factory=list)
    abgebrochen: bool = False
    abbruchgrund: Optional[str] = None

    def datenqualitaetsquote(self) -> float:
        if self.geladene_treffer == 0:
            return 0.0
        return round(self.gueltige_treffer / self.geladene_treffer, 4)


class IngestionPipeline:
    """Steuert den Adzuna-Ingestion-Lauf bis zur Bronze-Schicht."""

    def __init__(
        self,
        *,
        client: Optional[AdzunaClient] = None,
        schreiber: Optional[BronzeSchreiber] = None,
        suchstrategie: Optional[StandardSuchstrategie] = None,
    ) -> None:
        self._einstellungen = get_settings()
        self._client = client or AdzunaClient()
        self._schreiber = schreiber or BronzeSchreiber()
        self._suchstrategie = suchstrategie or StandardSuchstrategie()

    def ausfuehren(
        self,
        *,
        ausfuehrungsdatum: Optional[date] = None,
        max_seiten_pro_kategorie: int = 5,
        kategorien: Optional[Iterable[str]] = None,
    ) -> LaufBericht:
        """Fuehrt einen kompletten Lauf aus.

        Idempotenz wird durch Partitionierung nach Ausfuehrungsdatum und
        Kategorie sowie durch Deduplizierung anhand der Adzuna-ID erreicht.
        """
        kennung = neue_korrelationskennung()
        ausfuehrungsdatum = ausfuehrungsdatum or aktueller_zeitpunkt_utc().date()
        bericht = LaufBericht(korrelationskennung=kennung)

        anfragen = (
            self._suchstrategie.aus_kategorien(kategorien)
            if kategorien
            else self._suchstrategie.anfragen()
        )

        _logger.info(
            "ingestion_lauf_start",
            korrelationskennung=kennung,
            ausfuehrungsdatum=str(ausfuehrungsdatum),
            anzahl_kategorien=len(anfragen),
        )

        for anfrage in anfragen:
            bericht.kategorien.append(anfrage.kategorie)
            try:
                self._kategorie_laden(
                    anfrage=anfrage,
                    ausfuehrungsdatum=ausfuehrungsdatum,
                    max_seiten=max_seiten_pro_kategorie,
                    kennung=kennung,
                    bericht=bericht,
                )
            except QuotaErschoepftFehler as fehler:
                bericht.abgebrochen = True
                bericht.abbruchgrund = fehler.meldung
                _logger.error(
                    "ingestion_lauf_abgebrochen",
                    korrelationskennung=kennung,
                    grund=fehler.meldung,
                    kontext=fehler.kontext,
                )
                break

        _logger.info(
            "ingestion_lauf_ende",
            korrelationskennung=kennung,
            geladen=bericht.geladene_treffer,
            gueltig=bericht.gueltige_treffer,
            quarantaene=bericht.quarantaenierte_treffer,
            abgebrochen=bericht.abgebrochen,
        )
        return bericht

    def _kategorie_laden(
        self,
        *,
        anfrage: Suchanfrage,
        ausfuehrungsdatum: date,
        max_seiten: int,
        kennung: str,
        bericht: LaufBericht,
    ) -> None:
        for seite in self._client.seiten_abrufen(
            anfrage.query,
            kategorie=anfrage.kategorie,
            max_seiten=max_seiten,
        ):
            bericht.geladene_seiten += 1
            bericht.geladene_treffer += len(seite.treffer)

            ergebnis = validiere_adzuna_treffer(
                seite.treffer, quell_kategorie=anfrage.kategorie
            )
            bericht.gueltige_treffer += ergebnis.anzahl_gueltig
            bericht.quarantaenierte_treffer += ergebnis.anzahl_quarantaene

            if ergebnis.gueltig:
                self._schreiber.schreiben(
                    anzeigen=ergebnis.gueltig,
                    ausfuehrungsdatum=ausfuehrungsdatum,
                    kategorie=anfrage.kategorie,
                    seite=seite.seite,
                    korrelationskennung=kennung,
                )

            if ergebnis.quarantaene:
                self._schreiber.quarantaene_schreiben(
                    rohdaten=ergebnis.quarantaene,
                    ausfuehrungsdatum=ausfuehrungsdatum,
                    kategorie=anfrage.kategorie,
                    seite=seite.seite,
                    korrelationskennung=kennung,
                )
