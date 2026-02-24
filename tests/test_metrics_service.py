"""Unit tests for :class:`sentinel_dpi.services.metrics_service.MetricsService`."""

from __future__ import annotations

from sentinel_dpi.dpi.feature_schema import PacketFeatures
from sentinel_dpi.services.metrics_service import MetricsService


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _make_features(
    src_ip: str | None = "10.0.0.1",
    dst_ip: str | None = "10.0.0.2",
    protocol: str = "TCP",
    timestamp: float = 1_000_000.0,
) -> PacketFeatures:
    return PacketFeatures(
        timestamp=timestamp,
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol=protocol,
        src_port=12345,
        dst_port=80,
        packet_length=64,
    )


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

class TestMetricsServiceInitial:
    """Fresh service should return zeroed-out snapshot."""

    def test_initial_snapshot_zeroes(self) -> None:
        snap = MetricsService().snapshot()
        assert snap["total_packets"] == 0
        assert snap["packets_per_protocol"] == {}
        assert snap["packets_per_source_ip"] == {}
        assert snap["packets_per_destination_ip"] == {}
        assert snap["packets_per_second"] == 0.0


class TestMetricsServiceCounting:
    """Counter increments after update() calls."""

    def test_total_packets_increments(self) -> None:
        svc = MetricsService()
        svc.update(_make_features())
        svc.update(_make_features())
        assert svc.snapshot()["total_packets"] == 2

    def test_per_protocol_counts(self) -> None:
        svc = MetricsService()
        svc.update(_make_features(protocol="TCP"))
        svc.update(_make_features(protocol="TCP"))
        svc.update(_make_features(protocol="UDP"))
        snap = svc.snapshot()
        assert snap["packets_per_protocol"] == {"TCP": 2, "UDP": 1}

    def test_per_source_ip_counts(self) -> None:
        svc = MetricsService()
        svc.update(_make_features(src_ip="1.1.1.1"))
        svc.update(_make_features(src_ip="1.1.1.1"))
        svc.update(_make_features(src_ip="2.2.2.2"))
        snap = svc.snapshot()
        assert snap["packets_per_source_ip"] == {"1.1.1.1": 2, "2.2.2.2": 1}

    def test_per_destination_ip_counts(self) -> None:
        svc = MetricsService()
        svc.update(_make_features(dst_ip="8.8.8.8"))
        svc.update(_make_features(dst_ip="8.8.4.4"))
        snap = svc.snapshot()
        assert snap["packets_per_destination_ip"] == {"8.8.8.8": 1, "8.8.4.4": 1}


class TestMetricsServicePPS:
    """Rolling packets-per-second calculation."""

    def test_pps_calculation(self) -> None:
        svc = MetricsService(pps_window=10.0)
        # 5 packets all at t=100.0, within 10s window
        for _ in range(5):
            svc.update(_make_features(timestamp=100.0))
        snap = svc.snapshot()
        assert snap["packets_per_second"] == 5 / 10.0

    def test_pps_prunes_old_timestamps(self) -> None:
        svc = MetricsService(pps_window=5.0)
        # 3 packets at t=100
        for _ in range(3):
            svc.update(_make_features(timestamp=100.0))
        # 2 packets at t=106 (the first 3 are now stale: 100 <= 106-5)
        for _ in range(2):
            svc.update(_make_features(timestamp=106.0))

        snap = svc.snapshot()
        # Only the 2 recent packets survive pruning.
        assert snap["packets_per_second"] == 2 / 5.0
        # Total is still cumulative.
        assert snap["total_packets"] == 5


class TestMetricsServiceNoneFields:
    """None IP fields are handled gracefully."""

    def test_none_src_ip_tracked_as_unknown(self) -> None:
        svc = MetricsService()
        svc.update(_make_features(src_ip=None))
        assert svc.snapshot()["packets_per_source_ip"] == {"unknown": 1}

    def test_none_dst_ip_tracked_as_unknown(self) -> None:
        svc = MetricsService()
        svc.update(_make_features(dst_ip=None))
        assert svc.snapshot()["packets_per_destination_ip"] == {"unknown": 1}
