"""Unit tests for :class:`sentinel_dpi.services.alert_manager.AlertManager`."""

from __future__ import annotations

from sentinel_dpi.services.alert_manager import AlertManager


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _make_alert(
    alert_type: str = "PORT_SCAN",
    source_ip: str = "10.0.0.1",
    timestamp: float = 1_000_000.0,
    **extra: object,
) -> dict:
    alert: dict = {
        "type": alert_type,
        "source_ip": source_ip,
        "timestamp": timestamp,
    }
    alert.update(extra)
    return alert


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

class TestAlertManagerStorage:
    """Basic storage and enrichment."""

    def test_process_stores_alert(self) -> None:
        mgr = AlertManager()
        mgr.process([_make_alert()])

        snap = mgr.snapshot()
        assert snap["total_alerts"] == 1
        stored = snap["recent_alerts"][0]
        assert "id" in stored  # UUID assigned
        assert stored["type"] == "PORT_SCAN"
        assert stored["severity"] == "HIGH"
        assert stored["source_ip"] == "10.0.0.1"

    def test_empty_alerts_list_noop(self) -> None:
        mgr = AlertManager()
        mgr.process([])
        assert mgr.snapshot()["total_alerts"] == 0


class TestAlertManagerDedup:
    """Deduplication within the cooldown window."""

    def test_dedup_within_cooldown(self) -> None:
        mgr = AlertManager(cooldown=10.0)
        mgr.process([_make_alert(timestamp=100.0)])
        mgr.process([_make_alert(timestamp=105.0)])  # within cooldown
        assert mgr.snapshot()["total_alerts"] == 1

    def test_dedup_after_cooldown_expires(self) -> None:
        mgr = AlertManager(cooldown=5.0)
        mgr.process([_make_alert(timestamp=100.0)])
        mgr.process([_make_alert(timestamp=106.0)])  # cooldown expired
        assert mgr.snapshot()["total_alerts"] == 2

    def test_different_keys_not_deduped(self) -> None:
        mgr = AlertManager(cooldown=10.0)
        mgr.process([_make_alert(source_ip="1.1.1.1", timestamp=100.0)])
        mgr.process([_make_alert(source_ip="2.2.2.2", timestamp=100.0)])
        assert mgr.snapshot()["total_alerts"] == 2

    def test_different_types_not_deduped(self) -> None:
        mgr = AlertManager(cooldown=10.0)
        mgr.process([_make_alert(alert_type="PORT_SCAN", timestamp=100.0)])
        mgr.process([_make_alert(alert_type="BRUTE_FORCE", timestamp=100.0)])
        assert mgr.snapshot()["total_alerts"] == 2


class TestAlertManagerBounded:
    """Memory bounds enforcement."""

    def test_max_history_bounded(self) -> None:
        mgr = AlertManager(cooldown=0.0, max_history=5)
        for i in range(10):
            mgr.process([_make_alert(source_ip=f"10.0.0.{i}", timestamp=float(i))])

        snap = mgr.snapshot()
        assert len(snap["recent_alerts"]) == 5  # deque capped
        assert snap["total_alerts"] == 10  # cumulative count preserved


class TestAlertManagerSnapshot:
    """Snapshot structure and type breakdown."""

    def test_snapshot_structure(self) -> None:
        mgr = AlertManager()
        mgr.process([_make_alert()])
        snap = mgr.snapshot()
        assert "total_alerts" in snap
        assert "recent_alerts" in snap
        assert "alerts_by_type" in snap
        assert isinstance(snap["recent_alerts"], list)

    def test_alerts_by_type_counts(self) -> None:
        mgr = AlertManager(cooldown=0.0)
        mgr.process([
            _make_alert(alert_type="PORT_SCAN", source_ip="1.1.1.1"),
            _make_alert(alert_type="PORT_SCAN", source_ip="2.2.2.2"),
            _make_alert(alert_type="BRUTE_FORCE", source_ip="3.3.3.3"),
        ])
        snap = mgr.snapshot()
        assert snap["alerts_by_type"] == {"PORT_SCAN": 2, "BRUTE_FORCE": 1}
