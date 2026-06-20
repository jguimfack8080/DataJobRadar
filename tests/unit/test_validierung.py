"""Tests fuer die Schemavalidierung der Adzuna-Treffer."""
from ingestion.validation.schemata import validiere_adzuna_treffer


def test_gueltige_und_ungueltige_eintraege_werden_getrennt(beispiel_treffer) -> None:
    ergebnis = validiere_adzuna_treffer(beispiel_treffer, quell_kategorie="data_engineer")
    assert ergebnis.anzahl_gueltig == 2
    assert ergebnis.anzahl_quarantaene == 1
    assert ergebnis.gueltig[0].adzuna_id == "1001"
    assert ergebnis.gueltig[0].quell_kategorie == "data_engineer"
    assert ergebnis.gueltig[0].region == "Berlin"
    assert ergebnis.gueltig[0].gehalt_ist_vorhanden is True
    assert ergebnis.quarantaene[0]["grund"] == "id_fehlt"


def test_datum_wird_geparst(beispiel_treffer) -> None:
    ergebnis = validiere_adzuna_treffer(beispiel_treffer, quell_kategorie="data_engineer")
    erste = ergebnis.gueltig[0]
    assert erste.veroeffentlicht_am is not None
    assert erste.veroeffentlicht_am.year == 2025
    assert erste.veroeffentlicht_am.month == 6
