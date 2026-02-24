"""
Port-scan detection plugin.

Tracks per-source-IP destination ports within a configurable sliding
time window. When a single source IP contacts more than *threshold*
distinct destination ports within *window_seconds*, an alert is raised.

Includes cooldown logic to prevent alert flooding.
"""

from __future__ import annotations

from collections import defaultdict

from sentinel_dpi.detection.base_detector import BaseDetector
from sentinel_dpi.dpi.feature_schema import PacketFeatures


class PortScanDetector(BaseDetector):
    """Detect horizontal port scans using a sliding time window.

    Parameters:
        threshold: Number of distinct destination ports that triggers
                   an alert.
        window_seconds: Length of the sliding window in seconds.
    """

    def __init__(self, threshold: int = 20, window_seconds: float = 10.0) -> None:
        self._threshold = threshold
        self._window_seconds = window_seconds

        # {src_ip: [(dst_port, timestamp), ...]}
        self._tracking: dict[str, list[tuple[int, float]]] = defaultdict(list)

        # Cooldown tracking to prevent repeated alerts
        # {src_ip: last_alert_timestamp}
        self._last_alert: dict[str, float] = {}

    # ------------------------------------------------------------------
    # BaseDetector interface
    # ------------------------------------------------------------------

    def analyze(self, features: PacketFeatures) -> list[dict] | None:
        """Check whether *features* contributes to a port-scan pattern."""
        src_ip = features["src_ip"]
        dst_port = features["dst_port"]
        timestamp = features["timestamp"]

        if src_ip is None or dst_port is None:
            return None

        entries = self._tracking[src_ip]

        # Append the new observation
        entries.append((dst_port, timestamp))

        # Prune entries outside the sliding window
        cutoff = timestamp - self._window_seconds
        entries[:] = [(p, t) for p, t in entries if t > cutoff]

        # Count distinct destination ports in the window
        unique_ports = {p for p, _ in entries}

        # Check threshold (>= for intuitive behavior)
        if len(unique_ports) >= self._threshold:

            # Cooldown check — prevent alert spam
            last_alert_time = self._last_alert.get(src_ip)
            if last_alert_time is not None:
                if (timestamp - last_alert_time) < self._window_seconds:
                    return None

            # Record alert time
            self._last_alert[src_ip] = timestamp

            return [
                {
                    "type": "PORT_SCAN",
                    "source_ip": src_ip,
                    "unique_ports": len(unique_ports),
                    "window_seconds": self._window_seconds,
                    "timestamp": timestamp,
                }
            ]

        return None