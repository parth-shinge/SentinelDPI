"""Unit tests for :class:`sentinel_dpi.detection.detection_manager.DetectionManager`."""

from __future__ import annotations

from sentinel_dpi.detection.base_detector import BaseDetector
from sentinel_dpi.detection.detection_manager import DetectionManager
from sentinel_dpi.dpi.feature_schema import PacketFeatures


# --------------------------------------------------------------------------- #
# Helpers — lightweight concrete detectors for testing
# --------------------------------------------------------------------------- #

def _make_features(**overrides: object) -> PacketFeatures:
    """Return a minimal ``PacketFeatures`` dict with sensible defaults."""
    base: dict = {
        "timestamp": 1_000_000.0,
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "protocol": "TCP",
        "src_port": 12345,
        "dst_port": 80,
        "packet_length": 64,
    }
    base.update(overrides)
    return PacketFeatures(**base)


class _AlwaysAlertDetector(BaseDetector):
    """Returns a fixed alert on every call."""

    def analyze(self, features: PacketFeatures) -> list[dict] | None:
        return [{"type": "TEST_ALERT", "detail": "always"}]


class _NeverAlertDetector(BaseDetector):
    """Always returns ``None``."""

    def analyze(self, features: PacketFeatures) -> list[dict] | None:
        return None


class _ConditionalDetector(BaseDetector):
    """Alerts only when protocol is UDP."""

    def analyze(self, features: PacketFeatures) -> list[dict] | None:
        if features["protocol"] == "UDP":
            return [{"type": "UDP_DETECTED"}]
        return None


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

class TestDetectionManagerEmpty:
    """Manager with no detectors."""

    def test_no_detectors_returns_empty(self) -> None:
        manager = DetectionManager(detectors=[])
        assert manager.analyze(_make_features()) == []


class TestDetectionManagerSingle:
    """Manager with a single detector."""

    def test_single_detector_returns_alerts(self) -> None:
        manager = DetectionManager(detectors=[_AlwaysAlertDetector()])
        alerts = manager.analyze(_make_features())
        assert len(alerts) == 1
        assert alerts[0]["type"] == "TEST_ALERT"

    def test_detector_returning_none_skipped(self) -> None:
        manager = DetectionManager(detectors=[_NeverAlertDetector()])
        assert manager.analyze(_make_features()) == []


class TestDetectionManagerMultiple:
    """Manager aggregates alerts from multiple detectors."""

    def test_multiple_detectors_aggregated(self) -> None:
        manager = DetectionManager(
            detectors=[_AlwaysAlertDetector(), _ConditionalDetector()],
        )
        # TCP packet — only AlwaysAlert fires.
        alerts = manager.analyze(_make_features(protocol="TCP"))
        assert len(alerts) == 1

        # UDP packet — both fire.
        alerts = manager.analyze(_make_features(protocol="UDP"))
        assert len(alerts) == 2
        types = {a["type"] for a in alerts}
        assert types == {"TEST_ALERT", "UDP_DETECTED"}
