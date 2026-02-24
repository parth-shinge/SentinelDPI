"""
Thread-safe packet queue.

Thin wrapper around :class:`queue.Queue` that type-hints its contents
as scapy packets and exposes only the methods the rest of the system
needs.  No business logic lives here.
"""

from __future__ import annotations

import logging
import queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scapy.packet import Packet

logger = logging.getLogger(__name__)


class PacketQueue:
    """Thread-safe FIFO queue for raw scapy packets.

    Parameters:
        maxsize: Upper bound on the number of items in the queue.
                 ``0`` means unlimited.
    """

    def __init__(self, maxsize: int = 0) -> None:
        self._queue: queue.Queue[Packet] = queue.Queue(maxsize=maxsize)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def put(
        self,
        packet: Packet,
        block: bool = True,
        timeout: float | None = None,
    ) -> None:
        """Enqueue a packet.

        Raises:
            queue.Full: If the queue is full and *block* is ``False``
                        (or *timeout* expires).
        """
        self._queue.put(packet, block=block, timeout=timeout)

    def get(
        self,
        block: bool = True,
        timeout: float | None = None,
    ) -> Packet:
        """Dequeue a packet.

        Raises:
            queue.Empty: If the queue is empty and *block* is ``False``
                         (or *timeout* expires).
        """
        return self._queue.get(block=block, timeout=timeout)

    def empty(self) -> bool:
        """Return ``True`` if the queue is empty at the time of the call.

        .. note:: This is only a snapshot — the result may be stale by
           the time you act on it.
        """
        return self._queue.empty()

    def qsize(self) -> int:
        """Return the approximate number of items in the queue."""
        return self._queue.qsize()
