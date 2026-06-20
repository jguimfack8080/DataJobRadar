"""Integrationstests gegen einen gemockten Adzuna-Endpunkt."""
import json

import httpx
import pytest

from djr_core.config import AdzunaSettings
from djr_core.exceptions import ExterneApiFehler, QuotaErschoepftFehler
from ingestion.adzuna.client import AdzunaClient


def _client_mit_transport(transport: httpx.MockTransport) -> AdzunaClient:
    einstellungen = AdzunaSettings(
        app_id="x",
        app_key="y",
        country="de",
        base_url="https://api.adzuna.example/v1/api",
        results_per_page=5,
        timeout_seconds=2,
        max_retries=1,
    )
    http = httpx.Client(transport=transport)
    return AdzunaClient(einstellungen=einstellungen, http_client=http)


def test_seiten_abrufen_liefert_seiten() -> None:
    aufrufe = {"zaehler": 0}

    def handler(anfrage: httpx.Request) -> httpx.Response:
        aufrufe["zaehler"] += 1
        if aufrufe["zaehler"] == 1:
            payload = {"count": 6, "results": [{"id": "1"}, {"id": "2"}, {"id": "3"}, {"id": "4"}, {"id": "5"}]}
        else:
            payload = {"count": 6, "results": [{"id": "6"}]}
        return httpx.Response(200, json=payload)

    client = _client_mit_transport(httpx.MockTransport(handler))
    try:
        seiten = list(client.seiten_abrufen("data engineer", kategorie="data_engineer", max_seiten=3))
    finally:
        client.schliessen()

    assert len(seiten) == 2
    assert seiten[0].gesamt == 6
    assert seiten[1].treffer[0]["id"] == "6"


def test_quota_fehler_wird_propagiert() -> None:
    def handler(anfrage: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"message": "forbidden"})

    client = _client_mit_transport(httpx.MockTransport(handler))
    try:
        with pytest.raises(QuotaErschoepftFehler):
            list(client.seiten_abrufen("data engineer", kategorie="data_engineer", max_seiten=1))
    finally:
        client.schliessen()


def test_unerwarteter_status_fuehrt_zu_fehler() -> None:
    def handler(anfrage: httpx.Request) -> httpx.Response:
        return httpx.Response(418, text=json.dumps({"detail": "teapot"}))

    client = _client_mit_transport(httpx.MockTransport(handler))
    try:
        with pytest.raises(ExterneApiFehler):
            list(client.seiten_abrufen("data engineer", kategorie="data_engineer", max_seiten=1))
    finally:
        client.schliessen()
