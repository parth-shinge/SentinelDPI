"""
SentinelDPI entry point.

Wires all components via dependency injection and manages the
application lifecycle. Handles ``KeyboardInterrupt`` for graceful
shutdown.
"""

from __future__ import annotations

import logging
import threading
import time

from sentinel_dpi.api.app import create_app
from sentinel_dpi.config.settings import Settings
from sentinel_dpi.core.capture_engine import CaptureEngine
from sentinel_dpi.core.packet_processor import PacketProcessor
from sentinel_dpi.core.packet_queue import PacketQueue
from sentinel_dpi.detection.detection_manager import DetectionManager
from sentinel_dpi.detection.plugins.port_scan_detector import PortScanDetector
from sentinel_dpi.dpi.parser import PacketParser
from sentinel_dpi.services.alert_manager import AlertManager
from sentinel_dpi.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Set up minimal root-level logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    """Bootstrap and run SentinelDPI."""
    _configure_logging()

    # --- Dependency injection -------------------------------------------
    settings = Settings()
    packet_queue = PacketQueue(maxsize=settings.queue_maxsize)
    parser = PacketParser()

    # Detection layer (Sprint 3)
    port_scan_detector = PortScanDetector(
        threshold=settings.port_scan_threshold,
        window_seconds=settings.port_scan_window,
    )
    detection_manager = DetectionManager(detectors=[port_scan_detector])

    # Metrics layer (Sprint 4)
    metrics_service = MetricsService()

    # Alert layer (Sprint 5)
    alert_manager = AlertManager(
        cooldown=settings.alert_cooldown,
        max_history=settings.alert_max_history,
    )

    engine = CaptureEngine(packet_queue=packet_queue, settings=settings)
    processor = PacketProcessor(
        packet_queue=packet_queue,
        settings=settings,
        parser=parser,
        detection_manager=detection_manager,
        metrics_service=metrics_service,
        alert_manager=alert_manager,
    )

    # --- Start core components ------------------------------------------
    logger.info("SentinelDPI starting …")
    engine.start()
    processor.start()
    logger.info("SentinelDPI running — press Ctrl+C to stop")

    # --- API layer (Sprint 6) -------------------------------------------
    if settings.api_enabled:
        app = create_app(
            metrics_service=metrics_service,
            alert_manager=alert_manager,
        )

        import uvicorn

        api_thread = threading.Thread(
            target=uvicorn.run,
            kwargs={
                "app": app,
                "host": settings.api_host,
                "port": settings.api_port,
                "log_level": "warning",
                "access_log": False,
            },
            name="APIServer",
            daemon=True,
        )
        api_thread.start()

        logger.info(
            "API server started on http://%s:%d",
            settings.api_host,
            settings.api_port,
        )

    # --- Block main thread until interrupted -----------------------------
    try:
        while engine.is_alive():
            time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received — shutting down …")

    # --- Graceful shutdown ----------------------------------------------
    engine.stop()
    processor.stop()
    logger.info("SentinelDPI shut down complete")


if __name__ == "__main__":
    main()