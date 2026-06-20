"""Vorgefertigte analytische Abfragen fuer das Backend."""
from analytics.queries.kennzahlen import (
    abfrage_jobs_seite,
    abfrage_kennzahlen_gesamt,
    abfrage_top_skills,
    abfrage_top_unternehmen,
    abfrage_top_staedte,
    abfrage_zeitreihe_neue_jobs,
    abfrage_gehaltsverteilung,
)

__all__ = [
    "abfrage_jobs_seite",
    "abfrage_kennzahlen_gesamt",
    "abfrage_top_skills",
    "abfrage_top_unternehmen",
    "abfrage_top_staedte",
    "abfrage_zeitreihe_neue_jobs",
    "abfrage_gehaltsverteilung",
]
