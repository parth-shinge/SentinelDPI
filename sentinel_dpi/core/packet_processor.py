"""
Packet processor — consumer side of the capture pipeline.

Runs in its own thread, pulls raw packets from the shared
:class:`~sentinel_dpi.core.packet_queue.PacketQueue`, and delegates
parsing to the injected :class:`~sentinel_dpi.dpi.parser.PacketParser`.

When a :class:`~sentinel_dpi.detection.DetectionManager` is provided,
parsed features are forwarded to the detection layer after parsing.
When a :class:`~sentinel_dpi.services.MetricsService` is provided,
parsed features are recorded for real-time statistics.
When a :class:`~sentinel_dpi.services.AlertManager` is provided,
detection alerts are forwarded for storage and deduplication.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import TYPE_CHECKING

from sentinel_dpi.config.settings import Settings
from sentinel_dpi.core.packet_queue import PacketQueue

if TYPE_CHECKING:
    from scapy.packet import Packet
    from sentinel_dpi.detection.detection_manager import DetectionManager
    from sentinel_dpi.dpi.parser import PacketParser
    from sentinel_dpi.services.alert_manager import AlertManager
    from sentinel_dpi.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)


class PacketProcessor:
    """Consume packets from the queue and run them through the DPI parser.

    Parameters:
        packet_queue: Shared queue to pull packets from.
        settings: Application configuration.
        parser: Parser instance used to extract features from packets.
        detection_manager: Optional detection layer to forward features to.
        metrics_service: Optional metrics collector for traffic statistics.
        alert_manager: Optional alert handler for storage and deduplication.
    """

    def __init__(
        self,
        packet_queue: PacketQueue,
        settings: Settings,
        parser: PacketParser,
        detection_manager: DetectionManager | None = None,
        metrics_service: MetricsService | None = None,
        alert_manager: AlertManager | None = None,
    ) -> None:
        self._packet_queue = packet_queue
        self._settings = settings
        self._parser = parser
        self._detection_manager = detection_manager
        self._metrics_service = metrics_service
        self._alert_manager = alert_manager
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Spawn the processor thread (non-daemon)."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("PacketProcessor.start() called while already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="PacketProcessor",
            daemon=False,
        )
        self._thread.start()
        logger.info("PacketProcessor started")

    def stop(self) -> None:
        """Signal the processor to stop and wait for the thread to exit."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        logger.info("PacketProcessor stopped")

    def is_alive(self) -> bool:
        """Return ``True`` if the processor thread is currently running."""
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _run(self) -> None:
        """Main loop — runs inside a dedicated thread."""
        logger.info("PacketProcessor thread running")

        while not self._stop_event.is_set():
            try:
                packet: Packet = self._packet_queue.get(
                    block=True,
                    timeout=self._settings.processor_timeout,
                )
            except queue.Empty:
                continue

            try:
                features = self._parser.parse(packet)
                if self._metrics_service is not None:
                    self._metrics_service.update(features)
                if self._detection_manager is not None:
                    alerts = self._detection_manager.analyze(features)
                    if alerts and self._alert_manager is not None:
                        self._alert_manager.process(alerts)
            except Exception:
                logger.exception("Error processing packet")
