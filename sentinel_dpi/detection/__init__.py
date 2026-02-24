"""Detection framework — pluggable alert generation pipeline."""

from sentinel_dpi.detection.base_detector import BaseDetector
from sentinel_dpi.detection.detection_manager import DetectionManager

__all__ = ["BaseDetector", "DetectionManager"]
