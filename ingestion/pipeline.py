"""Orchestrierter Multi-Source-Ingestion-Lauf von allen Quellen in die Bronze-Schicht."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from djr_core.exceptions import QuotaErschoepftFehler
from djr_core.logging import get_logger
from djr_core.models import JobQuelle
from djr_core.utils import aktueller_zeitpunkt_utc, neue_korrelationskennung

from data_lake.bronze.schreiber import BronzeSchreiber
from ingestion.base.client import BasisQuelleClient, Suchanfrage
from ingestion.validation.schemata import validiere_anzeigen

_logger = get_logger("ingestion.pipeline")

_STATUS_DATEI = Path(os.getenv("QUELLEN_STATUS_PFAD", "/data/warehouse/quellen_status.json"))


@dataclass
class QuelleBericht:
    quelle: JobQuelle
    geladene_seiten: int = 0
    geladene_treffer: int = 0
    gueltige_treffer: int = 0
    quarantaenierte_treffer: int = 0
    kategorien: List[str] = field(default_factory=list)
    abgebrochen: bool = False
    abbruchgrund: Optional[str] = None


@dataclass
class LaufBericht:
    korrelationskennung: str
    je_quelle: dict[JobQuelle, QuelleBericht] = field(default_factory=dict)

    def gesamt_geladen(self) -> int:
        return sum(b.geladene_treffer for b in self.je_quelle.values())

    def gesamt_gueltig(self) -> int:
        return sum(b.gueltige_treffer for b in self.je_quelle.values())

    def gesamt_quarantaene(self) -> int:
        return sum(b.quarantaenierte_treffer for b in self.je_quelle.values())


def _aktive_quellen() -> set[JobQuelle]:
    """Liest die aktivierten Quellen aus der Umgebung.

    Default: alle bekannten Quellen aktiv.
    """
    roh = os.getenv(
        "INGESTION_QUELLEN",
        "adzuna,bundesagentur,muse,remotive,jobicy,arbeitnow,remoteok,jooble,jsearch",
    )
    aktiv = set()
    for teil in (s.strip().lower() for s in roh.split(",")):
        if not teil:
            continue
        try:
            aktiv.add(JobQuelle(teil))
        except ValueError:
            _logger.warning("unbekannte_quelle_in_konfig", wert=teil)
    return aktiv


def _client_fuer(quelle: JobQuelle) -> BasisQuelleClient:
    if quelle is JobQuelle.ADZUNA:
        from ingestion.adzuna.client import AdzunaClient

        return AdzunaClient()
    if quelle is JobQuelle.BUNDESAGENTUR:
        from ingestion.bundesagentur.client import BundesagenturClient

        return BundesagenturClient()
    if quelle is JobQuelle.MUSE:
        from ingestion.muse.client import MuseClient

        return MuseClient()
    if quelle is JobQuelle.REMOTIVE:
        from ingestion.remotive.client import RemotiveClient

        return RemotiveClient()
    if quelle is JobQuelle.JOBICY:
        from ingestion.jobicy.client import JobicyClient

        return JobicyClient()
    if quelle is JobQuelle.ARBEITNOW:
        from ingestion.arbeitnow.client import ArbeitnowClient

        return ArbeitnowClient()
    if quelle is JobQuelle.REMOTEOK:
        from ingestion.remoteok.client import RemoteokClient

        return RemoteokClient()
    if quelle is JobQuelle.JOOBLE:
        from ingestion.jooble.client import JoobleClient

        return JoobleClient()
    if quelle is JobQuelle.JSEARCH:
        from ingestion.jsearch.client import JsearchClient

        return JsearchClient()
    raise ValueError(f"Keine Client-Implementierung fuer {quelle}")


class IngestionPipeline:
    """Steuert den Multi-Source-Ingestion-Lauf bis zur Bronze-Schicht."""

    def __init__(self, schreiber: Optional[BronzeSchreiber] = None) -> None:
        self._schreiber = schreiber or BronzeSchreiber()
        self._aktive_quellen = _aktive_quellen()

    def ausfuehren(
        self,
        *,
        ausfuehrungsdatum: Optional[date] = None,
        max_seiten_pro_kategorie: int = 5,
        kategorien: Optional[Iterable[str]] = None,
        quellen: Optional[Iterable[JobQuelle]] = None,
    ) -> LaufBericht:
        kennung = neue_korrelationskennung()
        ausfuehrungsdatum = ausfuehrungsdatum or aktueller_zeitpunkt_utc().date()
        bericht = LaufBericht(korrelationskennung=kennung)

        gewuenschte_quellen = set(quellen) if quellen is not None else self._aktive_quellen

        _logger.info(
            "ingestion_lauf_start",
            korrelationskennung=kennung,
            ausfuehrungsdatum=str(ausfuehrungsdatum),
            quellen=[q.value for q in gewuenschte_quellen],
        )

        for quelle in gewuenschte_quellen:
            self._quelle_laden(
                quelle=quelle,
                ausfuehrungsdatum=ausfuehrungsdatum,
                max_seiten=max_seiten_pro_kategorie,
                kategorien=kategorien,
                kennung=kennung,
                bericht=bericht,
            )

        _logger.info(
            "ingestion_lauf_ende",
            korrelationskennung=kennung,
            gesamt_geladen=bericht.gesamt_geladen(),
            gesamt_gueltig=bericht.gesamt_gueltig(),
            gesamt_quarantaene=bericht.gesamt_quarantaene(),
        )
        self._status_speichern(bericht)
        self._abbruch_benachrichtigungen(bericht)
        return bericht

    def _status_speichern(self, bericht: LaufBericht) -> None:
        """Schreibt den Laufstatus als JSON fuer das Backend-Dashboard."""
        quellen_status: dict = {}
        for quelle, qb in bericht.je_quelle.items():
            quota = None
            try:
                client = _client_fuer(quelle)
                if hasattr(client, "quota_stand"):
                    quota = client.quota_stand()
            except Exception:
                pass
            quellen_status[quelle.value] = {
                "geladen": qb.geladene_treffer,
                "gueltig": qb.gueltige_treffer,
                "quarantaene": qb.quarantaenierte_treffer,
                "abgebrochen": qb.abgebrochen,
                "abbruchgrund": qb.abbruchgrund,
                "quota": quota,
            }
        inhalt = {
            "zeitstempel": aktueller_zeitpunkt_utc().isoformat(),
            "korrelationskennung": bericht.korrelationskennung,
            "quellen": quellen_status,
        }
        try:
            _STATUS_DATEI.parent.mkdir(parents=True, exist_ok=True)
            _STATUS_DATEI.write_text(json.dumps(inhalt, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            _logger.warning("status_datei_schreiben_fehler", fehler=str(exc))

    def _abbruch_benachrichtigungen(self, bericht: LaufBericht) -> None:
        """Sendet E-Mail fuer jede abgebrochene Quelle (ausser Quota-Erschoepfung)."""
        from ingestion.quota.tracker import quelle_unavailable_benachrichtigen

        for quelle, qb in bericht.je_quelle.items():
            if qb.abgebrochen and qb.abbruchgrund and "Quota" not in (qb.abbruchgrund or ""):
                quelle_unavailable_benachrichtigen(quelle.value, qb.abbruchgrund or "Unbekannter Fehler")

    def _quelle_laden(
        self,
        *,
        quelle: JobQuelle,
        ausfuehrungsdatum: date,
        max_seiten: int,
        kategorien: Optional[Iterable[str]],
        kennung: str,
        bericht: LaufBericht,
    ) -> None:
        quelle_bericht = QuelleBericht(quelle=quelle)
        bericht.je_quelle[quelle] = quelle_bericht
        try:
            client = _client_fuer(quelle)
        except Exception as fehler:
            _logger.error("quelle_init_fehler", quelle=quelle.value, fehler=str(fehler))
            quelle_bericht.abgebrochen = True
            quelle_bericht.abbruchgrund = str(fehler)
            return

        try:
            with client:
                anfragen = client.standard_suchanfragen()
                if kategorien:
                    erlaubt = set(kategorien)
                    anfragen = [a for a in anfragen if a.kategorie in erlaubt]

                for anfrage in anfragen:
                    quelle_bericht.kategorien.append(anfrage.kategorie)
                    try:
                        self._kategorie_laden(
                            client=client,
                            anfrage=anfrage,
                            ausfuehrungsdatum=ausfuehrungsdatum,
                            max_seiten=max_seiten,
                            kennung=kennung,
                            quelle_bericht=quelle_bericht,
                        )
                    except QuotaErschoepftFehler as fehler:
                        quelle_bericht.abgebrochen = True
                        quelle_bericht.abbruchgrund = fehler.meldung
                        _logger.error(
                            "quelle_abgebrochen",
                            quelle=quelle.value,
                            grund=fehler.meldung,
                            kontext=fehler.kontext,
                        )
                        break
                    except Exception as fehler:
                        _logger.error(
                            "kategorie_unerwarteter_fehler",
                            quelle=quelle.value,
                            kategorie=anfrage.kategorie,
                            fehler=str(fehler),
                        )
        except Exception as fehler:
            quelle_bericht.abgebrochen = True
            quelle_bericht.abbruchgrund = str(fehler)
            _logger.error("quelle_unerwarteter_fehler", quelle=quelle.value, fehler=str(fehler))

    def _kategorie_laden(
        self,
        *,
        client: BasisQuelleClient,
        anfrage: Suchanfrage,
        ausfuehrungsdatum: date,
        max_seiten: int,
        kennung: str,
        quelle_bericht: QuelleBericht,
    ) -> None:
        for seite in client.seiten_abrufen(anfrage, max_seiten=max_seiten):
            quelle_bericht.geladene_seiten += 1
            quelle_bericht.geladene_treffer += len(seite.anzeigen)

            ergebnis = validiere_anzeigen(seite.anzeigen)
            quelle_bericht.gueltige_treffer += ergebnis.anzahl_gueltig
            quelle_bericht.quarantaenierte_treffer += ergebnis.anzahl_quarantaene

            if ergebnis.gueltig:
                self._schreiber.schreiben(
                    anzeigen=ergebnis.gueltig,
                    quelle=client.quelle,
                    ausfuehrungsdatum=ausfuehrungsdatum,
                    kategorie=anfrage.kategorie,
                    seite=seite.seite,
                    korrelationskennung=kennung,
                )

            if ergebnis.quarantaene:
                self._schreiber.quarantaene_schreiben(
                    rohdaten=ergebnis.quarantaene,
                    quelle=client.quelle,
                    ausfuehrungsdatum=ausfuehrungsdatum,
                    kategorie=anfrage.kategorie,
                    seite=seite.seite,
                    korrelationskennung=kennung,
                )
