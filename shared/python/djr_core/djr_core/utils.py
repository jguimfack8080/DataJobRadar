"""Allgemein nutzbare Hilfsfunktionen."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Iterable, Iterator, TypeVar
from uuid import uuid4

T = TypeVar("T")

_WHITESPACE_PATTERN = re.compile(r"\s+")


def aktueller_zeitpunkt_utc() -> datetime:
    return datetime.now(timezone.utc)


def neue_korrelationskennung() -> str:
    return uuid4().hex


def text_normalisieren(text: str | None) -> str:
    """Normalisiert Text fuer Vergleiche und Suche."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFKD", text)
    norm = "".join(ch for ch in norm if not unicodedata.combining(ch))
    norm = norm.lower().strip()
    norm = _WHITESPACE_PATTERN.sub(" ", norm)
    return norm


def in_bloecken(iterable: Iterable[T], blockgroesse: int) -> Iterator[list[T]]:
    """Teilt ein Iterable in Bloecke fester Groesse."""
    if blockgroesse <= 0:
        raise ValueError("blockgroesse muss positiv sein")
    block: list[T] = []
    for element in iterable:
        block.append(element)
        if len(block) >= blockgroesse:
            yield block
            block = []
    if block:
        yield block
