"""
DPI protocol parser.

Extracts structured metadata from raw scapy packets and returns a
:class:`~sentinel_dpi.dpi.feature_schema.PacketFeatures` dictionary.
All layer access is defensive — missing layers produce ``None`` values
instead of exceptions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from scapy.layers.inet import IP, TCP, UDP, ICMP

from sentinel_dpi.dpi.feature_schema import PacketFeatures

if TYPE_CHECKING:
    from scapy.packet import Packet

logger = logging.getLogger(__name__)


class PacketParser:
    """Stateless parser that converts raw packets into normalised features.

    Usage::

        parser = PacketParser()
        features = parser.parse(packet)
    """

    def parse(self, packet: Packet) -> PacketFeatures:
        """Extract structured metadata from *packet*.

        Returns:
            A :class:`PacketFeatures` dictionary with all fields
            populated.  Fields whose protocol layer is absent are set
            to ``None``.
        """
        # ----- IP layer -------------------------------------------------
        src_ip: str | None = None
        dst_ip: str | None = None

        if packet.haslayer(IP):
            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst

        # ----- Transport / protocol -------------------------------------
        protocol: str = "Other"
        src_port: int | None = None
        dst_port: int | None = None

        if packet.haslayer(TCP):
            protocol = "TCP"
            tcp_layer = packet[TCP]
            src_port = tcp_layer.sport
            dst_port = tcp_layer.dport
        elif packet.haslayer(UDP):
            protocol = "UDP"
            udp_layer = packet[UDP]
            src_port = udp_layer.sport
            dst_port = udp_layer.dport
        elif packet.haslayer(ICMP):
            protocol = "ICMP"

        # ----- Assemble -------------------------------------------------
        return PacketFeatures(
            timestamp=float(packet.time),
            src_ip=src_ip,
            dst_ip=dst_ip,
            protocol=protocol,
            src_port=src_port,
            dst_port=dst_port,
            packet_length=len(packet),
        )
