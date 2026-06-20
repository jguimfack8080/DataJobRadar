"""Erweiterbare Skill-Taxonomie.

Jede Faehigkeit wird ueber kanonische Bezeichnung und Synonyme abgebildet. Die
Taxonomie ist datengetrieben und kann ohne Codeaenderung um neue Eintraege
ergaenzt werden, indem das YAML-Profil ersetzt wird.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class SkillEintrag:
    kanonisch: str
    kategorie: str
    synonyme: tuple[str, ...]


_STANDARD: tuple[SkillEintrag, ...] = (
    SkillEintrag("Python", "sprache", ("python", "python3", "py")),
    SkillEintrag("SQL", "sprache", ("sql", "ansi sql", "t-sql", "pl/sql", "ansi-sql")),
    SkillEintrag("Java", "sprache", ("java", "jvm")),
    SkillEintrag("Scala", "sprache", ("scala",)),
    SkillEintrag("Go", "sprache", ("golang", "go")),
    SkillEintrag("R", "sprache", ("r-programmierung",)),
    SkillEintrag("TypeScript", "sprache", ("typescript", "ts")),
    SkillEintrag("Airflow", "orchestrierung", ("airflow", "apache airflow", "mwaa")),
    SkillEintrag("Dagster", "orchestrierung", ("dagster",)),
    SkillEintrag("Prefect", "orchestrierung", ("prefect",)),
    SkillEintrag("dbt", "transformation", ("dbt", "dbt core", "dbt cloud")),
    SkillEintrag("Spark", "verarbeitung", ("spark", "apache spark", "pyspark", "spark sql")),
    SkillEintrag("Flink", "verarbeitung", ("flink", "apache flink")),
    SkillEintrag("Kafka", "streaming", ("kafka", "apache kafka", "ksql")),
    SkillEintrag("Kinesis", "streaming", ("kinesis", "aws kinesis")),
    SkillEintrag("Snowflake", "warehouse", ("snowflake",)),
    SkillEintrag("BigQuery", "warehouse", ("bigquery", "big query", "gcp bigquery")),
    SkillEintrag("Redshift", "warehouse", ("redshift", "aws redshift")),
    SkillEintrag("Databricks", "plattform", ("databricks",)),
    SkillEintrag("DuckDB", "warehouse", ("duckdb",)),
    SkillEintrag("PostgreSQL", "datenbank", ("postgres", "postgresql", "pgsql")),
    SkillEintrag("MySQL", "datenbank", ("mysql", "mariadb")),
    SkillEintrag("MongoDB", "datenbank", ("mongodb", "mongo")),
    SkillEintrag("Cassandra", "datenbank", ("cassandra",)),
    SkillEintrag("ClickHouse", "datenbank", ("clickhouse",)),
    SkillEintrag("AWS", "cloud", ("aws", "amazon web services", "amazon aws")),
    SkillEintrag("Azure", "cloud", ("azure", "microsoft azure")),
    SkillEintrag("GCP", "cloud", ("gcp", "google cloud", "google cloud platform")),
    SkillEintrag("Docker", "infrastruktur", ("docker", "docker compose")),
    SkillEintrag("Kubernetes", "infrastruktur", ("kubernetes", "k8s", "kube")),
    SkillEintrag("Terraform", "infrastruktur", ("terraform", "hcl")),
    SkillEintrag("Ansible", "infrastruktur", ("ansible",)),
    SkillEintrag("Looker", "visualisierung", ("looker", "looker studio")),
    SkillEintrag("Tableau", "visualisierung", ("tableau",)),
    SkillEintrag("PowerBI", "visualisierung", ("power bi", "powerbi")),
    SkillEintrag("Superset", "visualisierung", ("superset", "apache superset")),
    SkillEintrag("Metabase", "visualisierung", ("metabase",)),
    SkillEintrag("Pandas", "bibliothek", ("pandas",)),
    SkillEintrag("Polars", "bibliothek", ("polars",)),
    SkillEintrag("NumPy", "bibliothek", ("numpy",)),
    SkillEintrag("PyTorch", "bibliothek", ("pytorch", "torch")),
    SkillEintrag("TensorFlow", "bibliothek", ("tensorflow", "tf2")),
    SkillEintrag("Scikit-Learn", "bibliothek", ("scikit-learn", "sklearn")),
    SkillEintrag("MLflow", "ml_ops", ("mlflow",)),
    SkillEintrag("Kubeflow", "ml_ops", ("kubeflow",)),
    SkillEintrag("Git", "tools", ("git", "github", "gitlab", "bitbucket")),
    SkillEintrag("Linux", "tools", ("linux", "unix", "bash")),
)


def lade_standard_taxonomie() -> List[SkillEintrag]:
    return list(_STANDARD)


def lade_taxonomie_aus_yaml(pfad: Path) -> List[SkillEintrag]:
    """Laedt eine Taxonomie aus einer YAML-Datei.

    Das Format ist eine Liste von Mappings mit den Schluesseln
    `kanonisch`, `kategorie` und `synonyme`.
    """
    try:
        import yaml
    except ImportError as fehler:
        raise RuntimeError("PyYAML wird zum Laden externer Taxonomien benoetigt") from fehler

    inhalt = yaml.safe_load(pfad.read_text(encoding="utf-8")) or []
    eintraege: List[SkillEintrag] = []
    for eintrag in inhalt:
        eintraege.append(
            SkillEintrag(
                kanonisch=str(eintrag["kanonisch"]),
                kategorie=str(eintrag.get("kategorie") or "sonstige"),
                synonyme=tuple(str(s) for s in eintrag.get("synonyme") or ()),
            )
        )
    return eintraege


def vereinige(
    primaer: Sequence[SkillEintrag],
    sekundaer: Optional[Sequence[SkillEintrag]] = None,
) -> List[SkillEintrag]:
    """Vereinigt zwei Taxonomien, primaer hat Vorrang bei Konflikten."""
    bekannt = {eintrag.kanonisch.lower() for eintrag in primaer}
    ergebnis = list(primaer)
    if sekundaer:
        for eintrag in sekundaer:
            if eintrag.kanonisch.lower() not in bekannt:
                ergebnis.append(eintrag)
                bekannt.add(eintrag.kanonisch.lower())
    return ergebnis
