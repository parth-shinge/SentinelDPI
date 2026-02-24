"""
FastAPI application factory.

Creates a :class:`FastAPI` instance with read-only endpoints that
expose :meth:`MetricsService.snapshot` and
:meth:`AlertManager.snapshot`.  Services are captured through the
factory closure — no globals or ``app.state`` mutation.
"""

from __future__ import annotations

from fastapi import FastAPI

from sentinel_dpi.services.alert_manager import AlertManager
from sentinel_dpi.services.metrics_service import MetricsService


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

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics() -> dict:
        return metrics_service.snapshot()

    @app.get("/alerts")
    def alerts() -> dict:
        return alert_manager.snapshot()

    return app
