"""
FastAPI application factory.

Creates a :class:`FastAPI` instance with read-only REST endpoints and
a ``/ws`` WebSocket endpoint that streams real-time metrics and alerts.
Services are captured through the factory closure — no globals or
``app.state`` mutation.
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from sentinel_dpi.services.alert_manager import AlertManager
from sentinel_dpi.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)


def create_app(
    *,
    metrics_service: MetricsService,
    alert_manager: AlertManager,
) -> FastAPI:
    """Build and return a configured FastAPI application.

    Parameters:
        metrics_service: Shared metrics collector (read-only access).
        alert_manager: Shared alert store (read-only access).
    """
    app = FastAPI(title="SentinelDPI", docs_url="/docs")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # REST endpoints (unchanged)
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

    # ------------------------------------------------------------------
    # WebSocket endpoint
    # ------------------------------------------------------------------

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket) -> None:
        await ws.accept()

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
            """Send a metrics snapshot every 1 second."""
            try:
                while True:
                    snapshot = metrics_service.snapshot()
                    await ws.send_text(json.dumps({
                        "event": "metrics",
                        "data": snapshot,
                    }))
                    await asyncio.sleep(1)
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
            logger.debug("WebSocket client disconnected")

    return app
