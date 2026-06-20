"""Tests fuer typisierte Konfiguration."""
from djr_core.config import Settings


def test_settings_laden_aus_umgebung(monkeypatch) -> None:
    monkeypatch.setenv("ADZUNA_APP_ID", "abc")
    monkeypatch.setenv("ADZUNA_APP_KEY", "geheim")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "http://a,http://b")
    konfiguration = Settings()
    assert konfiguration.adzuna.app_id == "abc"
    assert konfiguration.backend.cors_origins == ["http://a", "http://b"]
