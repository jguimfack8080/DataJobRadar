"""Nutzer-Aktivitaet-Endpunkte (username-basiert, ohne Authentifizierung)."""
from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["nutzer"])

_USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")
_USER_DB = Path(os.getenv("USER_DATA_PATH", "/data/userdata/nutzer.db"))
_STATUS_VALIDE = {"gesehen", "gespeichert", "beworben"}


@contextmanager
def _verbindung() -> Generator[sqlite3.Connection, None, None]:
    _USER_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(_USER_DB), timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS job_aktivitaet (
            username        TEXT NOT NULL,
            job_kennung     TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT '[]',
            snapshot        TEXT,
            aktualisiert_am TEXT NOT NULL,
            PRIMARY KEY (username, job_kennung)
        )
    """)
    try:
        yield con
    finally:
        con.close()


def _validieren(username: str) -> None:
    if not _USERNAME_RE.match(username):
        raise HTTPException(
            status_code=400,
            detail="Ungültiger Username: nur Kleinbuchstaben, Ziffern und _ erlaubt (3-30 Zeichen).",
        )


def _zeile(row: tuple) -> dict:
    return {
        "kennung": row[0],
        "status": json.loads(row[1]),
        "snapshot": json.loads(row[2]) if row[2] else None,
    }


class AktivitaetEintrag(BaseModel):
    kennung: str = Field(..., max_length=64)
    status: List[str] = Field(default_factory=list)
    snapshot: Optional[dict] = None


class AktivitaetNutzlast(BaseModel):
    eintraege: List[AktivitaetEintrag] = Field(default_factory=list, max_length=2000)


@router.get("/nutzer/{username}/aktivitaet", summary="Aktivitaet eines Nutzers laden")
def aktivitaet_laden(username: str) -> dict:
    _validieren(username)
    with _verbindung() as con:
        rows = con.execute(
            "SELECT job_kennung, status, snapshot FROM job_aktivitaet WHERE username = ?",
            (username,),
        ).fetchall()
    return {"eintraege": [_zeile(r) for r in rows]}


@router.put("/nutzer/{username}/aktivitaet", summary="Aktivitaet synchronisieren")
def aktivitaet_synchronisieren(username: str, nutzlast: AktivitaetNutzlast) -> dict:
    _validieren(username)
    jetzt = datetime.now(timezone.utc).isoformat()
    with _verbindung() as con:
        for e in nutzlast.eintraege:
            status_valide = [s for s in e.status if s in _STATUS_VALIDE]
            con.execute(
                """
                INSERT INTO job_aktivitaet
                    (username, job_kennung, status, snapshot, aktualisiert_am)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(username, job_kennung) DO UPDATE SET
                    status          = excluded.status,
                    snapshot        = COALESCE(excluded.snapshot, snapshot),
                    aktualisiert_am = excluded.aktualisiert_am
                """,
                (
                    username,
                    e.kennung,
                    json.dumps(status_valide),
                    json.dumps(e.snapshot) if e.snapshot else None,
                    jetzt,
                ),
            )
        con.commit()
        rows = con.execute(
            "SELECT job_kennung, status, snapshot FROM job_aktivitaet WHERE username = ?",
            (username,),
        ).fetchall()
    return {"eintraege": [_zeile(r) for r in rows]}
