"""Unit tests for the FastAPI HTTP API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sentinel_dpi.api.app import create_app
from sentinel_dpi.services.alert_manager import AlertManager
from sentinel_dpi.services.metrics_service import MetricsService


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _make_client() -> TestClient:
    """Build a TestClient backed by real (empty) service instances."""
    metrics = MetricsService()
    alerts = AlertManager()
    app = create_app(metrics_service=metrics, alert_manager=alerts)
    return TestClient(app)


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

class TestHealthEndpoint:
    """GET /health."""

    def test_health_returns_ok(self) -> None:
        client = _make_client()
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestMetricsEndpoint:
    """GET /metrics."""

    def test_metrics_returns_snapshot(self) -> None:
        client = _make_client()
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_packets" in data
        assert "packets_per_protocol" in data
        assert "packets_per_source_ip" in data
        assert "packets_per_destination_ip" in data
        assert "packets_per_second" in data


class TestAlertsEndpoint:
    """GET /alerts."""

    def test_alerts_returns_snapshot(self) -> None:
        client = _make_client()
        resp = client.get("/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_alerts" in data
        assert "recent_alerts" in data
        assert "alerts_by_type" in data
