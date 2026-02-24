"""Unit tests for :class:`sentinel_dpi.detection.plugins.port_scan_detector.PortScanDetector`."""

from __future__ import annotations

from sentinel_dpi.detection.plugins.port_scan_detector import PortScanDetector
from sentinel_dpi.dpi.feature_schema import PacketFeatures


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _make_features(
    src_ip: str | None = "10.0.0.1",
    dst_port: int | None = 80,
    timestamp: float = 1_000_000.0,
) -> PacketFeatures:
    """Return a ``PacketFeatures`` dict with the given overrides."""
    return PacketFeatures(
        timestamp=timestamp,
        src_ip=src_ip,
        dst_ip="10.0.0.2",
        protocol="TCP",
        src_port=12345,
        dst_port=dst_port,
        packet_length=64,
    )


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

class TestPortScanBelowThreshold:
    """No alert should be raised when port count stays at or below threshold."""

    def test_below_threshold_no_alert(self) -> None:
        detector = PortScanDetector(threshold=20, window_seconds=10.0)
        for port in range(1, 20):  # 19 distinct ports
            result = detector.analyze(_make_features(dst_port=port, timestamp=100.0 + port))
        # 19 < threshold (20) → no alert on any call
        assert result is None


class TestPortScanAtThreshold:
    """Alert when unique ports exceed threshold."""

    def test_exceeding_threshold_triggers_alert(self) -> None:
        detector = PortScanDetector(threshold=5, window_seconds=10.0)
        base_ts = 1_000_000.0

        for port in range(1, 5):  # ports 1–4 (4 ports, below threshold)
            result = detector.analyze(
                _make_features(dst_port=port, timestamp=base_ts + port),
            )
        assert result is None  # 4 < threshold (5)

        # Port 5 hits the threshold (>= 5).
        result = detector.analyze(
            _make_features(dst_port=5, timestamp=base_ts + 5),
        )
        assert result is not None
        assert len(result) == 1
        alert = result[0]
        assert alert["type"] == "PORT_SCAN"
        assert alert["source_ip"] == "10.0.0.1"
        assert alert["unique_ports"] == 5
        assert alert["window_seconds"] == 10.0


class TestPortScanDifferentSources:
    """Traffic from different source IPs is tracked independently."""

    def test_different_sources_independent(self) -> None:
        detector = PortScanDetector(threshold=3, window_seconds=10.0)
        ts = 1_000_000.0

        # Source A: 3 ports (>= threshold, alerts for A).
        for port in range(1, 4):
            detector.analyze(_make_features(src_ip="1.1.1.1", dst_port=port, timestamp=ts))

        # Source B: 2 ports — below threshold, no alert.
        for port in range(1, 3):
            result = detector.analyze(
                _make_features(src_ip="2.2.2.2", dst_port=port, timestamp=ts),
            )
        assert result is None  # B has only 2 ports


class TestPortScanPruning:
    """Old entries outside the window must not count toward the threshold."""

    def test_old_entries_pruned(self) -> None:
        detector = PortScanDetector(threshold=5, window_seconds=5.0)

        # t=100: ports 1–4, below threshold (4 < 5).
        for port in range(1, 5):
            detector.analyze(_make_features(dst_port=port, timestamp=100.0))

        # t=106: first four entries are now stale (100 <= 106 - 5).
        # Only port 10 is in the window → 1 port, no alert.
        result = detector.analyze(_make_features(dst_port=10, timestamp=106.0))
        assert result is None


class TestPortScanMissingFields:
    """Packets with None src_ip or dst_port must be safely skipped."""

    def test_none_src_ip_skipped(self) -> None:
        detector = PortScanDetector(threshold=1, window_seconds=10.0)
        result = detector.analyze(_make_features(src_ip=None))
        assert result is None

    def test_none_dst_port_skipped(self) -> None:
        detector = PortScanDetector(threshold=1, window_seconds=10.0)
        result = detector.analyze(_make_features(dst_port=None))
        assert result is None
