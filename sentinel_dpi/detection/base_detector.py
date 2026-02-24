"""
Abstract base class for all detection plugins.

Every detector must subclass :class:`BaseDetector` and implement the
:meth:`analyze` method.  The detection manager iterates through
registered detectors and delegates feature analysis to each one.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sentinel_dpi.dpi.feature_schema import PacketFeatures


class BaseDetector(ABC):
    """Contract that every detection plugin must satisfy.

    Implementations may maintain internal state (e.g. sliding-window
    counters) but must **not** perform logging or produce side effects
    beyond returning alerts.
    """

    @abstractmethod
    def analyze(self, features: PacketFeatures) -> list[dict] | None:
        """Inspect *features* and return alerts, if any.

        Returns:
            A list of alert dictionaries when suspicious activity is
            detected, or ``None`` (/ empty list) otherwise.
        """
