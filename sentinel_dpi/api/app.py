"""
FastAPI application factory.

Creates a :class:`FastAPI` instance with read-only REST endpoints and
a ``/ws`` WebSocket endpoint that streams real-time telemetry.
Services are captured through the factory closure — no globals or
``app.state`` mutation.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from sentinel_dpi.services.alert_manager import AlertManager
from sentinel_dpi.services.metrics_service import MetricsService

if TYPE_CHECKING:
    from sentinel_dpi.config.settings import Settings
    from sentinel_dpi.core.capture_engine import CaptureEngine
    from sentinel_dpi.core.packet_processor import PacketProcessor
    from sentinel_dpi.detection.detection_manager import DetectionManager

logger = logging.getLogger(__name__)


def create_app(
    *,
    metrics_service: MetricsService,
    alert_manager: AlertManager,
    packet_processor: PacketProcessor | None = None,
    capture_engine: CaptureEngine | None = None,
    detection_manager: DetectionManager | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    """Build and return a configured FastAPI application.

    Parameters:
        metrics_service: Shared metrics collector (read-only access).
        alert_manager: Shared alert store (read-only access).
        packet_processor: Optional processor for live traffic feed.
        capture_engine: Optional engine reference for system status.
        detection_manager: Optional manager for detector count.
        settings: Optional settings for telemetry configuration.
    """
    ws_interval = settings.ws_update_interval if settings else 1.0

    app = FastAPI(title="SentinelDPI", docs_url="/docs")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_system_status() -> dict:
        """Assemble system status from injected component references."""
        return {
            "capture_engine": (
                "running" if capture_engine and capture_engine.is_alive() else "stopped"
            ),
            "packet_processor": (
                "running" if packet_processor and packet_processor.is_alive() else "stopped"
            ),
            "websocket": "active",
            "detectors_loaded": (
                len(detection_manager._detectors)
                if detection_manager
                else 0
            ),
        }

    # ------------------------------------------------------------------
    # REST endpoints
    # ------------------------------------------------------------------

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics() -> dict:
        return metrics_service.snapshot()

    @app.get("/alerts")
    def alerts() -> dict:
        return alert_manager.snapshot()

    @app.get("/traffic-feed")
    def traffic_feed() -> dict:
        feed = packet_processor.get_traffic_feed() if packet_processor else []
        return {"traffic_feed": feed}

    @app.get("/system-status")
    def system_status() -> dict:
        return _build_system_status()

    # ------------------------------------------------------------------
    # WebSocket endpoint
    # ------------------------------------------------------------------

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        logger.info("WebSocket client connected")

        # Per-connection queue for alert push notifications.
        alert_queue: asyncio.Queue[dict] = asyncio.Queue()

        def _on_alert(alert: dict) -> None:
            """Bridge sync AlertManager callback → async queue."""
            try:
                alert_queue.put_nowait(alert)
            except asyncio.QueueFull:
                pass  # drop if overwhelmed

        alert_manager.add_listener(_on_alert)

        async def _send_metrics_tick() -> None:
            """Send a structured telemetry snapshot at a fixed interval."""
            try:
                while True:
                    metrics_snap = metrics_service.snapshot()
                    alerts_snap = alert_manager.snapshot()
                    feed = (
                        packet_processor.get_traffic_feed()
                        if packet_processor
                        else []
                    )

                    payload = {
                        "metrics": {
                            "total_packets": metrics_snap["total_packets"],
                            "packets_per_protocol": metrics_snap["packets_per_protocol"],
                            "packets_per_source_ip": metrics_snap["packets_per_source_ip"],
                            "packets_per_destination_ip": metrics_snap["packets_per_destination_ip"],
                            "packets_per_second": metrics_snap["packets_per_second"],
                        },
                        "top_talkers": metrics_snap.get("top_talkers", []),
                        "traffic_feed": feed,
                        "threat_level": alert_manager.get_threat_level(),
                        "system_status": _build_system_status(),
                        "alert_activity": alert_manager.get_alert_activity(),
                        "alerts": alerts_snap.get("recent_alerts", []),
                    }

                    await ws.send_text(json.dumps({
                        "event": "metrics",
                        "data": payload,
                    }))
                    await asyncio.sleep(ws_interval)
            except (WebSocketDisconnect, Exception):
                pass

        async def _forward_alerts() -> None:
            """Forward alerts from the queue to the WebSocket."""
            try:
                while True:
                    alert = await alert_queue.get()
                    await ws.send_text(json.dumps({
                        "event": "alert",
                        "data": alert,
                    }))
            except (WebSocketDisconnect, Exception):
                pass

        try:
            await asyncio.gather(_send_metrics_tick(), _forward_alerts())
        except WebSocketDisconnect:
            pass
        finally:
            alert_manager.remove_listener(_on_alert)
            logger.info("WebSocket client disconnected")

    return app
