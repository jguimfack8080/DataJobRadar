"""Tests fuer den Skill-Extraktor."""
from skills.extraktor import SkillExtraktor


def test_extrahiert_bekannte_skills() -> None:
    extraktor = SkillExtraktor()
    text = "Wir suchen einen Engineer mit Python, SQL, Apache Spark und Kenntnissen in AWS."
    ergebnis = extraktor.extrahieren(text)
    for erwartet in ("Python", "SQL", "Spark", "AWS"):
        assert erwartet in ergebnis


def test_keine_falschtreffer_bei_woertern() -> None:
    extraktor = SkillExtraktor()
    # `R` darf nicht in `Bachelor` oder `rsync` erkannt werden
    text = "Bachelorabschluss und rsync-Erfahrung sind willkommen."
    ergebnis = extraktor.extrahieren(text)
    assert "R" not in ergebnis


def test_synonyme_werden_erkannt() -> None:
    extraktor = SkillExtraktor()
    text = "Erfahrung mit Power BI und Tableau."
    ergebnis = extraktor.extrahieren(text)
    assert "PowerBI" in ergebnis
    assert "Tableau" in ergebnis


def test_leerer_text_liefert_leere_liste() -> None:
    extraktor = SkillExtraktor()
    assert extraktor.extrahieren("") == []
    assert extraktor.extrahieren(None) == []


def test_kanonische_skills_enthalten_kernset() -> None:
    extraktor = SkillExtraktor()
    kanonisch = extraktor.kanonische_skills()
    for erwartet in (
        "Python",
        "SQL",
        "Airflow",
        "Spark",
        "Kafka",
        "AWS",
        "Azure",
        "GCP",
        "Docker",
        "Kubernetes",
        "Terraform",
    ):
        assert erwartet in kanonisch
