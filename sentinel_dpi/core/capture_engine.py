"""
Capture engine — live packet acquisition.

Uses :class:`scapy.sendrecv.AsyncSniffer` for non-blocking capture with
proper shutdown semantics on Windows.  The engine owns **no parsing
logic**; it only places raw packets into the shared
:class:`~sentinel_dpi.core.packet_queue.PacketQueue`.
"""

from __future__ import annotations

import logging
import queue
from typing import TYPE_CHECKING

from scapy.sendrecv import AsyncSniffer

from sentinel_dpi.core.packet_queue import PacketQueue

if TYPE_CHECKING:
    from scapy.packet import Packet

from sentinel_dpi.config.settings import Settings

logger = logging.getLogger(__name__)


class CaptureEngine:
    """Acquire packets from a network interface and enqueue them.

    Parameters:
        packet_queue: Shared queue to push captured packets into.
        settings: Application configuration.
    """

    def __init__(self, packet_queue: PacketQueue, settings: Settings) -> None:
        self._packet_queue = packet_queue
        self._settings = settings
        self._sniffer: AsyncSniffer | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Begin capturing packets.

        Creates and starts a :class:`AsyncSniffer`.  Call :meth:`stop`
        to shut it down explicitly.
        """
        if self._sniffer is not None:
            logger.warning("CaptureEngine.start() called while already running")
            return

        sniffer_kwargs: dict = {
            "prn": self._on_packet,
            "store": False,
        }
        if self._settings.interface is not None:
            sniffer_kwargs["iface"] = self._settings.interface
        if self._settings.bpf_filter:
            sniffer_kwargs["filter"] = self._settings.bpf_filter

        self._sniffer = AsyncSniffer(**sniffer_kwargs)
        self._sniffer.start()
        logger.info(
            "CaptureEngine started on interface=%s",
            self._settings.interface or "default",
        )

    def stop(self) -> None:
        """Stop capturing and wait for the sniffer thread to finish."""
        if self._sniffer is None:
            return

        logger.info("CaptureEngine stopping …")
        try:
            self._sniffer.stop()
        except Exception:
            # AsyncSniffer.stop() can raise if the sniffer was already
            # stopped or never fully started.  We log and move on.
            logger.debug("AsyncSniffer.stop() raised during shutdown", exc_info=True)
        finally:
            self._sniffer = None
        logger.info("CaptureEngine stopped")

    def is_alive(self) -> bool:
        """Return ``True`` if the sniffer is currently running."""
        if self._sniffer is None:
            return False
        return self._sniffer.running

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_packet(self, packet: Packet) -> None:
        """Callback invoked by scapy for every captured packet."""
        try:
            self._packet_queue.put(packet, block=False)
        except queue.Full:
            logger.warning("PacketQueue full — dropping packet")
