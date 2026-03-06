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

    def _resolve_interface(self) -> str:
        """Determine which network interface to capture on.

        Priority:
            1. ``settings.interface`` if explicitly set.
            2. Scapy's ``conf.iface`` (auto-detected default).
        """
        from scapy.config import conf as scapy_conf

        if self._settings.interface:
            logger.info(
                "Using manually configured interface: %s",
                self._settings.interface,
            )
            return self._settings.interface

        default_iface = str(scapy_conf.iface)
        logger.info("Auto-detected network interface: %s", default_iface)
        return default_iface

    def start(self) -> None:
        """Begin capturing packets.

        Creates and starts a :class:`AsyncSniffer`.  Call :meth:`stop`
        to shut it down explicitly.
        """
        if self._sniffer is not None:
            logger.warning("CaptureEngine.start() called while already running")
            return

        iface = self._resolve_interface()

        sniffer_kwargs: dict = {
            "prn": self._on_packet,
            "store": False,
            "iface": iface,
        }
        if self._settings.bpf_filter:
            sniffer_kwargs["filter"] = self._settings.bpf_filter

        try:
            self._sniffer = AsyncSniffer(**sniffer_kwargs)
            self._sniffer.start()
            logger.info("CaptureEngine started on interface=%s", iface)
        except Exception:
            logger.warning(
                "Failed to capture on '%s', falling back to default interface",
                iface,
                exc_info=True,
            )
            # Fall back to scapy default.
            from scapy.config import conf as scapy_conf
            fallback = str(scapy_conf.iface)
            sniffer_kwargs["iface"] = fallback
            self._sniffer = AsyncSniffer(**sniffer_kwargs)
            self._sniffer.start()
            logger.info("CaptureEngine started on fallback interface=%s", fallback)

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
