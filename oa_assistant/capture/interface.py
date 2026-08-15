"""
Screen capture interface definition.
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple


class CaptureResult:
    """
    Result of a screen capture operation.
    """

    def __init__(self, image, x: int, y: int, width: int, height: int, monitor_info: dict = None):
        """
        Initialize capture result.

        Args:
            image: Captured image (PIL.Image)
            x: Left coordinate of captured region
            y: Top coordinate of captured region
            width: Width of captured region
            height: Height of captured region
            monitor_info: Information about the monitor that was captured
        """
        self.image = image
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.monitor_info = monitor_info or {}

    def is_valid(self) -> bool:
        """
        Check if the capture result is valid.

        Returns:
            bool: True if result contains valid image data
        """
        return self.image is not None and self.width > 0 and self.height > 0


class ScreenCaptureInterface(ABC):
    """
    Abstract interface for screen capture operations.
    """

    @abstractmethod
    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[CaptureResult]:
        """
        Capture a specific region of the screen.

        Args:
            x: Left coordinate
            y: Top coordinate
            width: Width of region
            height: Height of region

        Returns:
            CaptureResult: Captured image and metadata, or None if failed
        """
        pass

    @abstractmethod
    def capture_monitor(self, monitor_index: int = 0) -> Optional[CaptureResult]:
        """
        Capture an entire monitor.

        Args:
            monitor_index: Index of monitor to capture (0 = primary)

        Returns:
            CaptureResult: Captured image and metadata, or None if failed
        """
        pass

    @abstractmethod
    def get_monitor_count(self) -> int:
        """
        Get the number of available monitors.

        Returns:
            int: Number of monitors
        """
        pass

    @abstractmethod
    def get_monitor_info(self, monitor_index: int) -> dict:
        """
        Get information about a specific monitor.

        Args:
            monitor_index: Index of monitor

        Returns:
            dict: Monitor information (width, height, x, y, etc.)
        """
        pass