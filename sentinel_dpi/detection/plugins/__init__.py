"""Detection plugins — concrete detector implementations."""

from sentinel_dpi.detection.plugins.high_traffic_detector import HighTrafficDetector
from sentinel_dpi.detection.plugins.port_scan_detector import PortScanDetector

__all__ = ["HighTrafficDetector", "PortScanDetector"]
