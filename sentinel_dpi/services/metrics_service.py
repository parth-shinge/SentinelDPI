"""
In-memory traffic metrics collector.

Maintains lightweight, bounded statistics derived exclusively from
:class:`~sentinel_dpi.dpi.feature_schema.PacketFeatures`.  Has no
knowledge of scapy, detectors, or threading.
"""

from __future__ import annotations

from collections import defaultdict, deque

from sentinel_dpi.dpi.feature_schema import PacketFeatures


class MetricsService:
    """Collect real-time traffic statistics from parsed packet features.

    Parameters:
        pps_window: Length (in seconds) of the rolling window used to
                    compute packets-per-second.  Defaults to 10 s.
    """

    def __init__(self, pps_window: float = 10.0) -> None:
        self._pps_window = pps_window

        self._total_packets: int = 0
        self._per_protocol: dict[str, int] = defaultdict(int)
        self._per_src_ip: dict[str, int] = defaultdict(int)
        self._per_dst_ip: dict[str, int] = defaultdict(int)

        # Timestamps for the rolling PPS calculation (sorted by arrival).
        self._timestamps: deque[float] = deque()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, features: PacketFeatures) -> None:
        """Record one packet's features into all counters."""
        self._total_packets += 1
        self._per_protocol[features["protocol"]] += 1

        src_ip = features["src_ip"]
        dst_ip = features["dst_ip"]
        self._per_src_ip[src_ip if src_ip is not None else "unknown"] += 1
        self._per_dst_ip[dst_ip if dst_ip is not None else "unknown"] += 1

        self._timestamps.append(features["timestamp"])
        self._prune_timestamps(features["timestamp"])

    def snapshot(self) -> dict:
        """Return a point-in-time summary of collected metrics.

        Returns:
            A dictionary with the following keys:

            - ``total_packets`` (int)
            - ``packets_per_protocol`` (dict[str, int])
            - ``packets_per_source_ip`` (dict[str, int])
            - ``packets_per_destination_ip`` (dict[str, int])
            - ``packets_per_second`` (float)
        """
        # Prune based on the most recent timestamp (if any).
        if self._timestamps:
            self._prune_timestamps(self._timestamps[-1])

        pps = len(self._timestamps) / self._pps_window if self._timestamps else 0.0

        return {
            "total_packets": self._total_packets,
            "packets_per_protocol": dict(self._per_protocol),
            "packets_per_source_ip": dict(self._per_src_ip),
            "packets_per_destination_ip": dict(self._per_dst_ip),
            "packets_per_second": pps,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _prune_timestamps(self, now: float) -> None:
        """Remove timestamps older than the PPS window."""
        cutoff = now - self._pps_window
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()
