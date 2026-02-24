"""Unit tests for :class:`sentinel_dpi.core.packet_queue.PacketQueue`."""

from __future__ import annotations

import queue
import pytest
from unittest.mock import MagicMock

from sentinel_dpi.core.packet_queue import PacketQueue


def _make_fake_packet() -> MagicMock:
    """Create a lightweight stand-in for a scapy Packet."""
    pkt = MagicMock()
    pkt.summary.return_value = "IP / TCP 10.0.0.1:12345 > 10.0.0.2:80"
    return pkt


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


class TestPacketQueue:
    """Suite covering the public API of PacketQueue."""

    def test_empty_on_new_queue(self) -> None:
        pq = PacketQueue()
        assert pq.empty() is True

    def test_qsize_on_new_queue(self) -> None:
        pq = PacketQueue()
        assert pq.qsize() == 0

    def test_put_and_get_roundtrip(self) -> None:
        pq = PacketQueue()
        pkt = _make_fake_packet()
        pq.put(pkt)
        result = pq.get(block=False)
        assert result is pkt

    def test_empty_after_put(self) -> None:
        pq = PacketQueue()
        pq.put(_make_fake_packet())
        assert pq.empty() is False

    def test_empty_after_put_and_get(self) -> None:
        pq = PacketQueue()
        pq.put(_make_fake_packet())
        pq.get(block=False)
        assert pq.empty() is True

    def test_get_timeout_raises_empty(self) -> None:
        pq = PacketQueue()
        with pytest.raises(queue.Empty):
            pq.get(block=True, timeout=0.05)

    def test_put_nonblocking_full_raises(self) -> None:
        pq = PacketQueue(maxsize=1)
        pq.put(_make_fake_packet())
        with pytest.raises(queue.Full):
            pq.put(_make_fake_packet(), block=False)

    def test_qsize_reflects_items(self) -> None:
        pq = PacketQueue()
        for _ in range(5):
            pq.put(_make_fake_packet())
        assert pq.qsize() == 5

    def test_fifo_order(self) -> None:
        pq = PacketQueue()
        packets = [_make_fake_packet() for _ in range(3)]
        for p in packets:
            pq.put(p)
        for p in packets:
            assert pq.get(block=False) is p
