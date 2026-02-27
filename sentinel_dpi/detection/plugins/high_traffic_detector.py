"""
High-traffic detection plugin.

Monitors packets-per-second (PPS) via :class:`MetricsService` and raises
an alert when PPS exceeds a configurable threshold for a sustained number
of consecutive invocations (the *window*).

No coupling to ``CaptureEngine`` — all data comes from ``MetricsService``.
"""

from __future__ import annotations

from sentinel_dpi.detection.base_detector import BaseDetector
from sentinel_dpi.dpi.feature_schema import PacketFeatures
from sentinel_dpi.services.metrics_service import MetricsService


class HighTrafficDetector(BaseDetector):
    """Detect sustained high traffic using a consecutive-count window.

    Parameters:
        metrics_service: Injected service providing live PPS snapshots.
        threshold: PPS value above which traffic is considered "high".
        window: Number of consecutive ``analyze`` invocations where PPS
                must exceed *threshold* before an alert is emitted.
    """

    def __init__(
        self,
        metrics_service: MetricsService,
        threshold: float = 50.0,
        window: int = 5,
    ) -> None:
        self._metrics_service = metrics_service
        self._threshold = threshold
        self._window = window
        self._consecutive_count: int = 0

    # ------------------------------------------------------------------
    # BaseDetector interface
    # ------------------------------------------------------------------

    def analyze(self, features: PacketFeatures) -> list[dict] | None:
        """Check whether sustained high traffic warrants an alert."""
        snapshot = self._metrics_service.snapshot()
        current_pps: float = snapshot["packets_per_second"]

        if current_pps > self._threshold:
            self._consecutive_count += 1
        else:
            self._consecutive_count = 0
            return None

        if self._consecutive_count >= self._window:
            self._consecutive_count = 0  # reset after firing
            return [
                {
                    "type": "HIGH_TRAFFIC",
                    "timestamp": features["timestamp"],
                    "current_pps": current_pps,
                }
            ]

        return None
