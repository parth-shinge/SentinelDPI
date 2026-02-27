"""Unit tests for :class:`sentinel_dpi.detection.plugins.high_traffic_detector.HighTrafficDetector`."""

from __future__ import annotations

from unittest.mock import MagicMock

from sentinel_dpi.detection.plugins.high_traffic_detector import HighTrafficDetector
from sentinel_dpi.dpi.feature_schema import PacketFeatures


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _make_features(timestamp: float = 1_000_000.0) -> PacketFeatures:
    """Return a minimal ``PacketFeatures`` dict."""
    return PacketFeatures(
        timestamp=timestamp,
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
        protocol="TCP",
        src_port=12345,
        dst_port=80,
        packet_length=64,
    )


def _make_metrics_service(pps: float) -> MagicMock:
    """Return a mock ``MetricsService`` whose snapshot reports a fixed PPS."""
    mock = MagicMock()
    mock.snapshot.return_value = {"packets_per_second": pps}
    return mock


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

class TestHighTrafficBelowThreshold:
    """No alert when PPS stays at or below the threshold."""

    def test_below_threshold_no_alert(self) -> None:
        ms = _make_metrics_service(pps=30.0)
        detector = HighTrafficDetector(metrics_service=ms, threshold=50.0, window=3)

        for _ in range(10):
            result = detector.analyze(_make_features())

        assert result is None

    def test_exactly_at_threshold_no_alert(self) -> None:
        ms = _make_metrics_service(pps=50.0)
        detector = HighTrafficDetector(metrics_service=ms, threshold=50.0, window=3)

        for _ in range(10):
            result = detector.analyze(_make_features())

        assert result is None


class TestHighTrafficAboveThreshold:
    """Alert when PPS exceeds threshold for the full window."""

    def test_sustained_high_pps_triggers_alert(self) -> None:
        ms = _make_metrics_service(pps=100.0)
        detector = HighTrafficDetector(metrics_service=ms, threshold=50.0, window=5)

        # First 4 calls should not alert (count < window).
        for _ in range(4):
            result = detector.analyze(_make_features())
            assert result is None

        # 5th call hits the window → alert.
        result = detector.analyze(_make_features())
        assert result is not None
        assert len(result) == 1
        assert result[0]["type"] == "HIGH_TRAFFIC"


class TestHighTrafficResetOnDrop:
    """Counter resets when PPS drops below threshold."""

    def test_drop_resets_counter(self) -> None:
        ms = MagicMock()
        detector = HighTrafficDetector(metrics_service=ms, threshold=50.0, window=5)

        # 3 calls above threshold.
        ms.snapshot.return_value = {"packets_per_second": 80.0}
        for _ in range(3):
            detector.analyze(_make_features())

        # PPS drops below threshold → counter resets.
        ms.snapshot.return_value = {"packets_per_second": 20.0}
        detector.analyze(_make_features())

        # 4 more calls above threshold (not enough to reach window=5 again).
        ms.snapshot.return_value = {"packets_per_second": 80.0}
        for _ in range(4):
            result = detector.analyze(_make_features())

        assert result is None  # only 4 consecutive, not 5


class TestHighTrafficAlertPayload:
    """Alert dict matches the documented schema."""

    def test_alert_shape(self) -> None:
        ms = _make_metrics_service(pps=120.5)
        detector = HighTrafficDetector(metrics_service=ms, threshold=50.0, window=3)

        ts = 1_700_000.0
        for _ in range(2):
            detector.analyze(_make_features(timestamp=ts))

        result = detector.analyze(_make_features(timestamp=ts))
        assert result is not None

        alert = result[0]
        assert alert == {
            "type": "HIGH_TRAFFIC",
            "timestamp": ts,
            "current_pps": 120.5,
        }


class TestHighTrafficCounterResetsAfterAlert:
    """After an alert fires, the counter resets for a fresh window."""

    def test_counter_resets_after_alert(self) -> None:
        ms = _make_metrics_service(pps=80.0)
        detector = HighTrafficDetector(metrics_service=ms, threshold=50.0, window=3)

        # Trigger first alert (calls 1-3).
        for _ in range(3):
            result = detector.analyze(_make_features())
        assert result is not None  # first alert fired

        # Next 2 calls should NOT alert (counter was reset, need 3 again).
        for _ in range(2):
            result = detector.analyze(_make_features())
        assert result is None

        # 3rd call after reset → second alert.
        result = detector.analyze(_make_features())
        assert result is not None
        assert result[0]["type"] == "HIGH_TRAFFIC"


class TestHighTrafficPartialWindow:
    """PPS exceeds threshold for fewer than window calls → no alert."""

    def test_partial_window_no_alert(self) -> None:
        ms = _make_metrics_service(pps=80.0)
        detector = HighTrafficDetector(metrics_service=ms, threshold=50.0, window=10)

        for _ in range(9):
            result = detector.analyze(_make_features())

        assert result is None
