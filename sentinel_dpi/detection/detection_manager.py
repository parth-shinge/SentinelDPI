"""
Detection manager — orchestrates all registered detectors.

Receives a list of :class:`BaseDetector` instances via dependency
injection and delegates :meth:`analyze` to each one, aggregating the
results into a flat list of alert dictionaries.
"""

from __future__ import annotations

from sentinel_dpi.detection.base_detector import BaseDetector
from sentinel_dpi.dpi.feature_schema import PacketFeatures


class DetectionManager:
    """Fan-out analyser that delegates to pluggable detectors.

    Parameters:
        detectors: Ordered sequence of detector plugins to invoke on
                   every packet's feature set.
    """

    def __init__(self, detectors: list[BaseDetector]) -> None:
        self._detectors = list(detectors)

    def analyze(self, features: PacketFeatures) -> list[dict]:
        """Run *features* through every registered detector.

        Returns:
            Aggregated list of alert dicts from all detectors.
            Empty list when nothing is detected.
        """
        alerts: list[dict] = []
        for detector in self._detectors:
            result = detector.analyze(features)
            if result:
                alerts.extend(result)
        return alerts
