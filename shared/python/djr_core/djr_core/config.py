"""Typisierte Konfiguration fuer alle Dienste der Plattform.

Alle Werte werden ausschliesslich ueber Umgebungsvariablen geladen. Es duerfen
keine Geheimnisse hartcodiert werden.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _csv_in_liste(wert: str | None) -> List[str]:
    if not wert:
        return []
    return [eintrag.strip() for eintrag in wert.split(",") if eintrag.strip()]


class AdzunaSettings(BaseSettings):
    """Adzuna API-spezifische Konfiguration."""

    model_config = SettingsConfigDict(env_prefix="ADZUNA_", extra="ignore")

    app_id: str = Field(..., min_length=1, description="Adzuna Anwendungs-Kennung")
    app_key: str = Field(..., min_length=1, description="Adzuna Anwendungs-Schluessel")
    country: str = Field(default="de", min_length=2, max_length=2)
    base_url: str = Field(default="https://api.adzuna.com/v1/api")
    results_per_page: int = Field(default=50, ge=1, le=50)
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    max_retries: int = Field(default=5, ge=0, le=10)


class BackendSettings(BaseSettings):
    """Backend Konfiguration."""

    model_config = SettingsConfigDict(env_prefix="BACKEND_", extra="ignore")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8081, ge=1, le=65535)
    log_level: str = Field(default="INFO")
    cors_origins_csv: str = Field(
        default="http://localhost:3000",
        alias="cors_origins",
        description="Komma-separierte Liste erlaubter CORS-Origins",
    )
    cache_ttl_seconds: int = Field(default=300, ge=0, le=3600)
    rate_limit_per_minute: int = Field(default=120, ge=1, le=10000)

    @property
    def cors_origins(self) -> List[str]:
        return _csv_in_liste(self.cors_origins_csv)


class DataLakeSettings(BaseSettings):
    """Konfiguration fuer Data Lake und DuckDB Warehouse."""

    model_config = SettingsConfigDict(extra="ignore")

    data_lake_root: Path = Field(default=Path("/data/lake"))
    duckdb_path: Path = Field(default=Path("/data/warehouse/djr.duckdb"))

    def bronze_path(self) -> Path:
        return self.data_lake_root / "bronze"

    def silver_path(self) -> Path:
        return self.data_lake_root / "silver"

    def gold_path(self) -> Path:
        return self.data_lake_root / "gold"


class Settings(BaseSettings):
    """Aggregierte Konfiguration fuer alle Subsysteme."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    adzuna: AdzunaSettings = Field(default_factory=AdzunaSettings)
    backend: BackendSettings = Field(default_factory=BackendSettings)
    data_lake: DataLakeSettings = Field(default_factory=DataLakeSettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton-Zugriff auf die Konfiguration."""
    return Settings()
