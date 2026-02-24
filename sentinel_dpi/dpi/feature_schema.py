"""
Normalized feature schema for parsed packets.

Defines the typed contract between the DPI parser and all downstream
consumers (processors, detectors, loggers).
"""

from __future__ import annotations

from typing import TypedDict


class PacketFeatures(TypedDict):
    """Structured metadata extracted from a single packet.

    Fields set to ``None`` indicate that the corresponding protocol
    layer was not present in the packet.
    """

    timestamp: float
    src_ip: str | None
    dst_ip: str | None
    protocol: str  # "TCP" | "UDP" | "ICMP" | "Other"
    src_port: int | None
    dst_port: int | None
    packet_length: int
