"""Quotenverfolgung fuer APIs mit Anfrage-Limits.

Speichert Zaehler in SQLite (QUOTA_DB_PATH). Sendet Warn-E-Mail wenn
Warnschwelle erreicht. Kein monatlicher Reset fuer Jooble (Lifetime-Limit),
monatlicher Reset fuer JSearch.
"""
from __future__ import annotations

import os
import smtplib
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from djr_core.logging import get_logger

_logger = get_logger("ingestion.quota.tracker")

_QUOTA_DB = Path(os.getenv("QUOTA_DB_PATH", "/data/warehouse/quota.db"))
_ALERT_EMAIL = os.getenv("QUOTA_ALERT_EMAIL", "jeunaj3@gmail.com")


@contextmanager
def _verbindung():
    _QUOTA_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(_QUOTA_DB), timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS quota (
            api_name        TEXT    NOT NULL PRIMARY KEY,
            verbraucht      INTEGER NOT NULL DEFAULT 0,
            reset_datum     TEXT,
            alert_gesendet  INTEGER NOT NULL DEFAULT 0,
            aktualisiert_am TEXT    NOT NULL
        )
    """)
    try:
        yield con
        con.commit()
    finally:
        con.close()


class QuotaTracker:
    """Verfolgt Anfrage-Verbrauch einer einzelnen API."""

    def __init__(
        self,
        api_name: str,
        grenze: int,
        warnschwelle: float = 0.80,
        monatlich: bool = False,
    ) -> None:
        self.api_name = api_name
        self.grenze = grenze
        self.warnschwelle = warnschwelle
        self.monatlich = monatlich

    # ------------------------------------------------------------------
    def ist_erschoepft(self) -> bool:
        self._monats_reset_falls_noetig()
        with _verbindung() as con:
            row = con.execute(
                "SELECT verbraucht FROM quota WHERE api_name = ?", (self.api_name,)
            ).fetchone()
        return row is not None and row[0] >= self.grenze

    def hinzufuegen(self, anzahl: int = 1) -> int:
        """Erhoeht Zaehler, prueft Warnschwelle. Gibt neuen Stand zurueck."""
        self._monats_reset_falls_noetig()
        jetzt = datetime.now(timezone.utc).isoformat()
        with _verbindung() as con:
            con.execute(
                """
                INSERT INTO quota (api_name, verbraucht, reset_datum, alert_gesendet, aktualisiert_am)
                VALUES (?, ?, ?, 0, ?)
                ON CONFLICT(api_name) DO UPDATE SET
                    verbraucht      = verbraucht + excluded.verbraucht,
                    aktualisiert_am = excluded.aktualisiert_am
                """,
                (self.api_name, anzahl, self._reset_datum_str(), jetzt),
            )
            row = con.execute(
                "SELECT verbraucht, alert_gesendet FROM quota WHERE api_name = ?",
                (self.api_name,),
            ).fetchone()
        verbraucht, alert_gesendet = row
        self._warnung_pruefen(verbraucht, alert_gesendet)
        return verbraucht

    def stand(self) -> dict:
        """Aktueller Quotenstand als Dict (fuer Status-JSON)."""
        self._monats_reset_falls_noetig()
        with _verbindung() as con:
            row = con.execute(
                "SELECT verbraucht, reset_datum FROM quota WHERE api_name = ?",
                (self.api_name,),
            ).fetchone()
        verbraucht = row[0] if row else 0
        return {
            "verbraucht": verbraucht,
            "grenze": self.grenze,
            "prozent": round(verbraucht / self.grenze * 100, 1),
            "monatlich": self.monatlich,
            "reset_datum": self._reset_datum_str(),
        }

    # ------------------------------------------------------------------
    def _reset_datum_str(self) -> Optional[str]:
        if not self.monatlich:
            return None
        heute = date.today()
        return date(heute.year, heute.month, 1).isoformat()

    def _monats_reset_falls_noetig(self) -> None:
        if not self.monatlich:
            return
        aktuell = self._reset_datum_str()
        with _verbindung() as con:
            row = con.execute(
                "SELECT reset_datum FROM quota WHERE api_name = ?", (self.api_name,)
            ).fetchone()
            if row and row[0] and row[0] < aktuell:
                con.execute(
                    "UPDATE quota SET verbraucht = 0, alert_gesendet = 0, reset_datum = ? WHERE api_name = ?",
                    (aktuell, self.api_name),
                )
                _logger.info("quota_monats_reset", api=self.api_name, neues_datum=aktuell)

    def _warnung_pruefen(self, verbraucht: int, alert_gesendet: int) -> None:
        if alert_gesendet or verbraucht < self.grenze * self.warnschwelle:
            return
        prozent = round(verbraucht / self.grenze * 100)
        try:
            _email_senden(
                an=_ALERT_EMAIL,
                betreff=f"[Data Job Radar] Quota-Warnung: {self.api_name} bei {prozent}%",
                inhalt=(
                    f"Die API '{self.api_name}' hat {verbraucht} von {self.grenze} "
                    f"verfuegbaren Anfragen verbraucht ({prozent}%).\n\n"
                    + (
                        "Bitte eine neue API-Key beantragen und an jeunaj3@gmail.com schicken."
                        if not self.monatlich
                        else f"Das monatliche Kontingent wird am naechsten Monatsersten zurueckgesetzt."
                    )
                ),
            )
            with _verbindung() as con:
                con.execute(
                    "UPDATE quota SET alert_gesendet = 1 WHERE api_name = ?",
                    (self.api_name,),
                )
            _logger.info("quota_warnung_gesendet", api=self.api_name, verbraucht=verbraucht)
        except Exception as exc:
            _logger.warning("quota_warnung_email_fehler", api=self.api_name, fehler=str(exc))


def quelle_unavailable_benachrichtigen(api_name: str, grund: str) -> None:
    """Sendet einmalige Benachrichtigung wenn eine Quelle abgebrochen wurde."""
    try:
        _email_senden(
            an=_ALERT_EMAIL,
            betreff=f"[Data Job Radar] Quelle nicht verfuegbar: {api_name}",
            inhalt=(
                f"Die Datenquelle '{api_name}' konnte beim letzten Pipeline-Lauf keine Daten liefern.\n\n"
                f"Grund: {grund}\n\n"
                "Die Pipeline hat normal weitergelaufen. Bitte den Status pruefen."
            ),
        )
    except Exception as exc:
        _logger.warning("unavailable_email_fehler", api=api_name, fehler=str(exc))


def _email_senden(*, an: str, betreff: str, inhalt: str) -> None:
    host = os.getenv("AIRFLOW__SMTP__SMTP_HOST") or os.getenv("SMTP_HOST", "")
    port = int(os.getenv("AIRFLOW__SMTP__SMTP_PORT") or os.getenv("SMTP_PORT", "587") or 587)
    user = os.getenv("AIRFLOW__SMTP__SMTP_USER") or os.getenv("SMTP_USER", "")
    passwort = os.getenv("AIRFLOW__SMTP__SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD", "")
    absender = os.getenv("AIRFLOW__SMTP__SMTP_MAIL_FROM") or os.getenv("SMTP_MAIL_FROM") or user

    if not host or not user:
        _logger.warning("smtp_nicht_konfiguriert_quota_alert")
        return

    msg = MIMEText(inhalt, "plain", "utf-8")
    msg["Subject"] = betreff
    msg["From"] = absender
    msg["To"] = an

    with smtplib.SMTP(host, port) as server:
        server.ehlo()
        server.starttls()
        server.login(user, passwort)
        server.sendmail(absender, [an], msg.as_string())
