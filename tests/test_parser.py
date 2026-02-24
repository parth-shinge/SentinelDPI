"""Unit tests for :class:`sentinel_dpi.dpi.parser.PacketParser`."""

from __future__ import annotations

from unittest.mock import MagicMock, patch, PropertyMock

from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.packet import Packet as ScapyPacket
from scapy.layers.l2 import Ether

from sentinel_dpi.dpi.feature_schema import PacketFeatures
from sentinel_dpi.dpi.parser import PacketParser


class TestPacketParserTCP:
    """TCP packet extraction."""

    def test_parse_tcp_packet(self) -> None:
        pkt = Ether() / IP(src="10.0.0.1", dst="10.0.0.2") / TCP(sport=12345, dport=80)
        parser = PacketParser()
        result = parser.parse(pkt)

        assert result["src_ip"] == "10.0.0.1"
        assert result["dst_ip"] == "10.0.0.2"
        assert result["protocol"] == "TCP"
        assert result["src_port"] == 12345
        assert result["dst_port"] == 80
        assert result["packet_length"] == len(pkt)
        assert isinstance(result["timestamp"], float)


class TestPacketParserUDP:
    """UDP packet extraction."""

    def test_parse_udp_packet(self) -> None:
        pkt = Ether() / IP(src="192.168.1.1", dst="192.168.1.2") / UDP(sport=5353, dport=53)
        parser = PacketParser()
        result = parser.parse(pkt)

        assert result["protocol"] == "UDP"
        assert result["src_port"] == 5353
        assert result["dst_port"] == 53
        assert result["src_ip"] == "192.168.1.1"
        assert result["dst_ip"] == "192.168.1.2"


class TestPacketParserICMP:
    """ICMP packet extraction."""

    def test_parse_icmp_packet(self) -> None:
        pkt = Ether() / IP(src="10.1.1.1", dst="10.1.1.2") / ICMP()
        parser = PacketParser()
        result = parser.parse(pkt)

        assert result["protocol"] == "ICMP"
        assert result["src_ip"] == "10.1.1.1"
        assert result["dst_ip"] == "10.1.1.2"
        assert result["src_port"] is None
        assert result["dst_port"] is None


class TestPacketParserRaw:
    """Packet with no IP layer."""

    def test_parse_raw_packet(self) -> None:
        pkt = Ether()
        parser = PacketParser()
        result = parser.parse(pkt)

        assert result["src_ip"] is None
        assert result["dst_ip"] is None
        assert result["protocol"] == "Other"
        assert result["src_port"] is None
        assert result["dst_port"] is None
        assert result["packet_length"] == len(pkt)


class TestPacketParserSchema:
    """Verify return value conforms to PacketFeatures schema."""

    def test_all_keys_present(self) -> None:
        pkt = Ether() / IP() / TCP()
        parser = PacketParser()
        result = parser.parse(pkt)

        expected_keys = set(PacketFeatures.__annotations__.keys())
        assert set(result.keys()) == expected_keys
