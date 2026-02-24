"""
Alert manager — centralised alert handling, deduplication, and storage.

Receives raw alert dicts from the detection layer, enriches them with
a unique ID and severity, deduplicates within a configurable cooldown
window, and stores them in a bounded in-memory history.
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

# Extensible severity mapping — keyed by alert ``type``.
_SEVERITY_MAP: dict[str, str] = {
    "PORT_SCAN": "HIGH",
}
_DEFAULT_SEVERITY = "MEDIUM"


class AlertManager:
    """Store, deduplicate, and summarise detection alerts.

    Parameters:
        cooldown: Seconds within which a duplicate ``(type, source_ip)``
                  alert is suppressed.
        max_history: Maximum number of alerts retained in memory.
    """

    def __init__(
        self,
        cooldown: float = 10.0,
        max_history: int = 1000,
    ) -> None:
        self._cooldown = cooldown
        self._alerts: deque[dict] = deque(maxlen=max_history)
        self._total_alerts: int = 0
        self._alerts_by_type: dict[str, int] = defaultdict(int)

        # Dedup tracking: {(type, source_ip): last_timestamp}
        self._recent_keys: dict[tuple[str, str | None], float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, alerts: list[dict]) -> None:
        """Ingest alerts from the detection layer.

        Each alert dict is expected to contain at least ``"type"`` and
        ``"timestamp"`` keys. Duplicates (same type + source_ip within
        the cooldown window) are silently discarded.
        """
        for raw_alert in alerts:
            alert_type = raw_alert.get("type", "UNKNOWN")
            source_ip = raw_alert.get("source_ip")
            timestamp = raw_alert.get("timestamp", 0.0)

            # --- Prune expired dedup keys -------------------------------
            cutoff = timestamp - self._cooldown
            expired_keys = [
                key for key, last_ts in self._recent_keys.items()
                if last_ts < cutoff
            ]
            for key in expired_keys:
                del self._recent_keys[key]

            # --- Deduplication ------------------------------------------
            key = (alert_type, source_ip)
            last_seen = self._recent_keys.get(key)
            if last_seen is not None and (timestamp - last_seen) < self._cooldown:
                continue

            self._recent_keys[key] = timestamp

            # --- Enrich -------------------------------------------------
            enriched: dict = {
                "id": str(uuid.uuid4()),
                "type": alert_type,
                "source_ip": source_ip,
                "severity": _SEVERITY_MAP.get(alert_type, _DEFAULT_SEVERITY),
                "timestamp": timestamp,
            }

            # --- Store --------------------------------------------------
            self._alerts.append(enriched)
            self._total_alerts += 1
            self._alerts_by_type[alert_type] += 1

            logger.info("ALERT stored: %s", enriched)

    def snapshot(self) -> dict:
        """Return a point-in-time summary of alert history."""
        return {
            "total_alerts": self._total_alerts,
            "recent_alerts": list(self._alerts),
            "alerts_by_type": dict(self._alerts_by_type),
        }