"""
Alert manager — centralised alert handling, deduplication, and storage.

Receives raw alert dicts from the detection layer, enriches them with
a unique ID and severity, deduplicates within a configurable cooldown
window, and stores them in a bounded in-memory history.

Thread safety is guaranteed by an internal lock for all public methods.
"""

from __future__ import annotations

import logging
import time as _time
import threading
import uuid
from collections import defaultdict, deque
from typing import Callable

logger = logging.getLogger(__name__)

# Extensible severity mapping — keyed by alert ``type``.
_SEVERITY_MAP: dict[str, str] = {
    "PORT_SCAN": "HIGH",
    "HIGH_TRAFFIC": "HIGH",
}
_DEFAULT_SEVERITY = "MEDIUM"


class AlertManager:
    """Store, deduplicate, and summarise detection alerts.

    Parameters:
        cooldown: Seconds within which a duplicate ``(type, source_ip)``
                  alert is suppressed.
        max_history: Maximum number of alerts retained in memory.
        alert_window_seconds: Rolling window (seconds) for threat-level
                              computation.  Defaults to 60.
    """

    def __init__(
        self,
        cooldown: float = 10.0,
        max_history: int = 1000,
        alert_window_seconds: int = 60,
    ) -> None:
        self._cooldown = cooldown
        self._alert_window = alert_window_seconds
        self._alerts: deque[dict] = deque(maxlen=max_history)
        self._total_alerts: int = 0
        self._alerts_by_type: dict[str, int] = defaultdict(int)

        # Dedup tracking: {(type, source_ip): last_timestamp}
        self._recent_keys: dict[tuple[str, str | None], float] = {}

        # Listeners notified synchronously on each new stored alert.
        self._listeners: list[Callable[[dict], None]] = []

        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Listener API
    # ------------------------------------------------------------------

    def add_listener(self, callback: Callable[[dict], None]) -> None:
        """Register a callback invoked with each newly stored alert."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[dict], None]) -> None:
        """Unregister a previously registered callback."""
        try:
            self._listeners.remove(callback)
        except ValueError:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, alerts: list[dict]) -> None:
        """Ingest alerts from the detection layer (thread-safe).

        Each alert dict is expected to contain at least ``"type"`` and
        ``"timestamp"`` keys. Duplicates (same type + source_ip within
        the cooldown window) are silently discarded.
        """
        with self._lock:
            for raw_alert in alerts:
                alert_type = raw_alert.get("type", "UNKNOWN")
                source_ip = raw_alert.get("source_ip")
                timestamp = raw_alert.get("timestamp", 0.0)

                # --- Prune expired dedup keys ---------------------------
                cutoff = timestamp - self._cooldown
                expired_keys = [
                    key for key, last_ts in self._recent_keys.items()
                    if last_ts < cutoff
                ]
                for key in expired_keys:
                    del self._recent_keys[key]

                # --- Deduplication --------------------------------------
                key = (alert_type, source_ip)
                last_seen = self._recent_keys.get(key)
                if last_seen is not None and (timestamp - last_seen) < self._cooldown:
                    continue

                self._recent_keys[key] = timestamp

                # --- Enrich ---------------------------------------------
                enriched: dict = {
                    "id": str(uuid.uuid4()),
                    "type": alert_type,
                    "source_ip": source_ip,
                    "severity": _SEVERITY_MAP.get(alert_type, _DEFAULT_SEVERITY),
                    "timestamp": timestamp,
                }

                # --- Store ----------------------------------------------
                self._alerts.append(enriched)
                self._total_alerts += 1
                self._alerts_by_type[alert_type] += 1

                logger.info("ALERT stored: %s", enriched)

                # --- Notify listeners -----------------------------------
                for listener in self._listeners:
                    try:
                        listener(enriched)
                    except Exception:
                        logger.exception("Alert listener error")

    # ------------------------------------------------------------------
    # Internal (lock must already be held by caller)
    # ------------------------------------------------------------------

    def _get_recent_alert_count_unlocked(
        self, window_seconds: int | None = None,
    ) -> int:
        """Count recent alerts — caller must hold ``_lock``."""
        window = window_seconds if window_seconds is not None else self._alert_window
        cutoff = _time.time() - window
        return sum(1 for a in self._alerts if a["timestamp"] >= cutoff)

    def _get_threat_level_unlocked(self) -> str:
        """Compute threat level — caller must hold ``_lock``."""
        count = self._get_recent_alert_count_unlocked()
        if count == 0:
            return "LOW"
        if count <= 5:
            return "MEDIUM"
        return "HIGH"

    # ------------------------------------------------------------------
    # Public API (continued)
    # ------------------------------------------------------------------

    def get_recent_alert_count(self, window_seconds: int | None = None) -> int:
        """Count alerts within the last *window_seconds* seconds (thread-safe).

        Uses wall-clock time so the count reflects real recent activity.
        """
        with self._lock:
            return self._get_recent_alert_count_unlocked(window_seconds)

    def get_threat_level(self) -> str:
        """Compute system threat level based on recent alert volume.

        Rules:
            0 alerts in window   → ``"LOW"``
            1–5 alerts in window → ``"MEDIUM"``
            >5 alerts in window  → ``"HIGH"``
        """
        with self._lock:
            return self._get_threat_level_unlocked()

    def get_alert_activity(self, minutes: int = 5) -> list[dict]:
        """Return per-minute alert counts for the last *minutes* minutes.

        Returns a list of ``{"time": "HH:MM", "count": N}`` dicts,
        ordered chronologically (thread-safe).
        """
        now = _time.time()
        # Build minute buckets.
        buckets: dict[str, int] = {}
        for m in range(minutes - 1, -1, -1):
            t = now - m * 60
            label = _time.strftime("%H:%M", _time.localtime(t))
            buckets[label] = 0

        with self._lock:
            cutoff = now - minutes * 60
            for alert in self._alerts:
                if alert["timestamp"] >= cutoff:
                    label = _time.strftime(
                        "%H:%M", _time.localtime(alert["timestamp"]),
                    )
                    if label in buckets:
                        buckets[label] += 1

        return [{"time": t, "count": c} for t, c in buckets.items()]

    def snapshot(self) -> dict:
        """Return a point-in-time summary of alert history (thread-safe)."""
        with self._lock:
            return {
                "total_alerts": self._total_alerts,
                "recent_alerts": list(self._alerts),
                "alerts_by_type": dict(self._alerts_by_type),
                "threat_level": self._get_threat_level_unlocked(),
            }