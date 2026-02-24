"""Unit tests for :class:`sentinel_dpi.core.capture_engine.CaptureEngine`."""

from __future__ import annotations

import queue
from unittest.mock import MagicMock, patch

import pytest

from sentinel_dpi.config.settings import Settings
from sentinel_dpi.core.capture_engine import CaptureEngine
from sentinel_dpi.core.packet_queue import PacketQueue


def _make_fake_packet() -> MagicMock:
    pkt = MagicMock()
    pkt.summary.return_value = "IP / TCP 10.0.0.1:12345 > 10.0.0.2:80"
    return pkt


class TestCaptureEngineCallback:
    """Tests for the ``_on_packet`` callback in isolation."""

    def test_on_packet_enqueues(self) -> None:
        settings = Settings()
        pq = PacketQueue(maxsize=10)
        engine = CaptureEngine(packet_queue=pq, settings=settings)

        pkt = _make_fake_packet()
        engine._on_packet(pkt)

        assert pq.qsize() == 1
        assert pq.get(block=False) is pkt

    def test_on_packet_drops_when_queue_full(self) -> None:
        settings = Settings()
        pq = PacketQueue(maxsize=1)
        engine = CaptureEngine(packet_queue=pq, settings=settings)

        pkt1 = _make_fake_packet()
        pkt2 = _make_fake_packet()
        engine._on_packet(pkt1)
        engine._on_packet(pkt2)  # should be silently dropped

        assert pq.qsize() == 1  # only the first packet remains


class TestCaptureEngineLifecycle:
    """Tests for start / stop / is_alive using a mocked AsyncSniffer."""

    @patch("sentinel_dpi.core.capture_engine.AsyncSniffer")
    def test_start_creates_sniffer(self, mock_sniffer_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_sniffer_cls.return_value = mock_instance

        settings = Settings()
        pq = PacketQueue()
        engine = CaptureEngine(packet_queue=pq, settings=settings)
        engine.start()

        mock_sniffer_cls.assert_called_once()
        mock_instance.start.assert_called_once()

    @patch("sentinel_dpi.core.capture_engine.AsyncSniffer")
    def test_stop_stops_sniffer(self, mock_sniffer_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_sniffer_cls.return_value = mock_instance

        settings = Settings()
        pq = PacketQueue()
        engine = CaptureEngine(packet_queue=pq, settings=settings)
        engine.start()
        engine.stop()

        mock_instance.stop.assert_called_once()

    @patch("sentinel_dpi.core.capture_engine.AsyncSniffer")
    def test_is_alive_true_when_running(self, mock_sniffer_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.running = True
        mock_sniffer_cls.return_value = mock_instance

        settings = Settings()
        pq = PacketQueue()
        engine = CaptureEngine(packet_queue=pq, settings=settings)
        engine.start()

        assert engine.is_alive() is True

    @patch("sentinel_dpi.core.capture_engine.AsyncSniffer")
    def test_is_alive_false_when_stopped(self, mock_sniffer_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_instance.running = False
        mock_sniffer_cls.return_value = mock_instance

        settings = Settings()
        pq = PacketQueue()
        engine = CaptureEngine(packet_queue=pq, settings=settings)
        engine.start()

        assert engine.is_alive() is False

    def test_is_alive_false_when_not_started(self) -> None:
        settings = Settings()
        pq = PacketQueue()
        engine = CaptureEngine(packet_queue=pq, settings=settings)
        assert engine.is_alive() is False

    @patch("sentinel_dpi.core.capture_engine.AsyncSniffer")
    def test_double_start_is_safe(self, mock_sniffer_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_sniffer_cls.return_value = mock_instance

        settings = Settings()
        pq = PacketQueue()
        engine = CaptureEngine(packet_queue=pq, settings=settings)
        engine.start()
        engine.start()  # should log warning, not create a second sniffer

        # AsyncSniffer constructor called only once
        assert mock_sniffer_cls.call_count == 1
