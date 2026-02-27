"""Unit tests for the FastAPI HTTP API and WebSocket endpoint."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from sentinel_dpi.api.app import create_app
from sentinel_dpi.services.alert_manager import AlertManager
from sentinel_dpi.services.metrics_service import MetricsService


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _make_app() -> tuple[TestClient, MetricsService, AlertManager]:
    """Build a TestClient backed by real (empty) service instances."""
    metrics = MetricsService()
    alerts = AlertManager()
    app = create_app(metrics_service=metrics, alert_manager=alerts)
    return TestClient(app), metrics, alerts


def _make_client() -> TestClient:
    """Legacy helper — returns only the client."""
    client, _, _ = _make_app()
    return client


# --------------------------------------------------------------------------- #
# REST Tests
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


# --------------------------------------------------------------------------- #
# WebSocket Tests
# --------------------------------------------------------------------------- #

class TestWebSocketMetrics:
    """WS /ws — metrics streaming."""

    def test_ws_receives_metrics(self) -> None:
        client, _metrics, _alerts = _make_app()
        with client.websocket_connect("/ws") as ws:
            raw = ws.receive_text()
            msg = json.loads(raw)
            assert msg["event"] == "metrics"
            assert "total_packets" in msg["data"]
            assert "packets_per_second" in msg["data"]


class TestWebSocketAlerts:
    """WS /ws — alert push."""

    def test_ws_receives_alert(self) -> None:
        client, _metrics, alert_manager = _make_app()
        with client.websocket_connect("/ws") as ws:
            # Consume the initial metrics tick.
            ws.receive_text()

            # Inject an alert synchronously.
            alert_manager.process([{
                "type": "PORT_SCAN",
                "source_ip": "10.0.0.1",
                "timestamp": 1_000_000.0,
            }])

            # The alert should arrive before the next metrics tick.
            raw = ws.receive_text()
            msg = json.loads(raw)
            assert msg["event"] == "alert"
            assert msg["data"]["type"] == "PORT_SCAN"
            assert msg["data"]["severity"] == "HIGH"


class TestWebSocketDisconnect:
    """WS /ws — graceful disconnect."""

    def test_ws_disconnect_clean(self) -> None:
        client, _, _ = _make_app()
        with client.websocket_connect("/ws") as ws:
            ws.receive_text()  # get at least one message
        # No exception ⇒ disconnect handled cleanly.
