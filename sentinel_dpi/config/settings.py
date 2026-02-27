"""
Application-wide configuration for SentinelDPI.

All tunables are centralised in a single frozen dataclass.
Inject ``Settings`` into components that need configuration —
never import individual values at module level.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable runtime configuration.

    Core Capture Settings:
        interface: Network interface for scapy to sniff on.
                   ``None`` lets scapy choose the default interface.
        queue_maxsize: Upper bound on the packet queue.
        processor_timeout: Seconds the processor blocks on a ``get()``
                           before re-checking the stop event.
        bpf_filter: Optional Berkeley Packet Filter expression.
        snapshot_length: Maximum bytes captured per packet.

    Detection Settings:
        port_scan_threshold: Number of unique destination ports that
                             triggers a port scan alert.
        port_scan_window: Sliding window duration (seconds).

    Alert Settings:
        alert_cooldown: Suppression window for duplicate alerts.
        alert_max_history: Maximum alerts stored in memory.

    API Settings:
        api_enabled: Whether to start the HTTP API server.
        api_host: Host address for the API server.
        api_port: Port for the API server.
    """

    # --- Capture Layer ---
    interface: str | None = r"\Device\NPF_{51E74BDD-4380-4517-925D-DCC87B9EB92D}"
    queue_maxsize: int = 10_000
    processor_timeout: float = 1.0
    bpf_filter: str = ""
    snapshot_length: int = 65_535

    # --- Detection Layer ---
    port_scan_threshold: int = 20
    port_scan_window: float = 10.0

    # --- High-Traffic Detection ---
    high_traffic_threshold: float = 50.0
    high_traffic_window: int = 5

    # --- Alert Layer ---
    alert_cooldown: float = 10.0
    alert_max_history: int = 1000

    # --- API Layer ---
    api_enabled: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8000