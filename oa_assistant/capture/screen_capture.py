"""
Screen capture implementation using mss.
"""
import mss
import mss.tools
from PIL import Image
from typing import Optional, Dict, List

from oa_assistant.capture.interface import ScreenCaptureInterface, CaptureResult
from oa_assistant.core.logging import logger


class ScreenCapture(ScreenCaptureInterface):
    """
    Screen capture implementation using mss library.
    """

    def __init__(self):
        """Initialize the screen capture."""
        self._sct = mss.mss()
        logger.debug("ScreenCapture initialized")

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
        try:
            if width <= 0 or height <= 0:
                logger.warning(f"Invalid capture dimensions: {width}x{height}")
                return None

            # Define the monitor region to capture
            monitor = {
                "left": x,
                "top": y,
                "width": width,
                "height": height
            }

            # Capture the screen
            sct_img = self._sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes(
                "RGB",
                (sct_img.size.width, sct_img.size.height),
                sct_img.rgb
            )

            # Get monitor information for the captured region
            monitor_info = self._get_monitor_at_point(x, y)

            logger.debug(f"Captured region: {x},{y},{width},{height}")
            return CaptureResult(img, x, y, width, height, monitor_info)

        except Exception as e:
            logger.error(f"Failed to capture region {x},{y},{width},{height}: {e}")
            return None

    def capture_monitor(self, monitor_index: int = 0) -> Optional[CaptureResult]:
        """
        Capture an entire monitor.

        Args:
            monitor_index: Index of monitor to capture (0 = primary)

        Returns:
            CaptureResult: Captured image and metadata, or None if failed
        """
        try:
            # Get monitor information
            if monitor_index >= len(self._sct.monitors):
                logger.warning(f"Monitor index {monitor_index} out of range")
                return None

            monitor = self._sct.monitors[monitor_index + 1]  # +1 because index 0 is all monitors

            # Capture the monitor
            sct_img = self._sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes(
                "RGB",
                (sct_img.size.width, sct_img.size.height),
                sct_img.rgb
            )

            logger.debug(f"Captured monitor {monitor_index}: {monitor}")
            return CaptureResult(
                img,
                monitor["left"],
                monitor["top"],
                monitor["width"],
                monitor["height"],
                {"index": monitor_index, **monitor}
            )

        except Exception as e:
            logger.error(f"Failed to capture monitor {monitor_index}: {e}")
            return None

    def get_monitor_count(self) -> int:
        """
        Get the number of available monitors.

        Returns:
            int: Number of monitors (excluding the "all monitors" entry)
        """
        # mss.monitors[0] represents all monitors combined
        # Actual monitors start from index 1
        return len(self._sct.monitors) - 1

    def get_monitor_info(self, monitor_index: int) -> dict:
        """
        Get information about a specific monitor.

        Args:
            monitor_index: Index of monitor

        Returns:
            dict: Monitor information (width, height, x, y, etc.)
        """
        try:
            if monitor_index >= len(self._sct.monitors) - 1:
                return {}

            # +1 because index 0 is all monitors
            monitor = self._sct.monitors[monitor_index + 1]
            return {
                "index": monitor_index,
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"]
            }
        except Exception as e:
            logger.error(f"Failed to get monitor info for index {monitor_index}: {e}")
            return {}

    def _get_monitor_at_point(self, x: int, y: int) -> dict:
        """
        Get information about the monitor containing a specific point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            dict: Monitor information
        """
        try:
            # Skip index 0 as it's the combined monitor
            for i in range(1, len(self._sct.monitors)):
                monitor = self._sct.monitors[i]
                if (monitor["left"] <= x < monitor["left"] + monitor["width"] and
                    monitor["top"] <= y < monitor["top"] + monitor["height"]):
                    return {
                        "index": i - 1,  # Adjust for 0-based indexing in our API
                        "left": monitor["left"],
                        "top": monitor["top"],
                        "width": monitor["width"],
                        "height": monitor["height"]
                    }

            # If not found, return primary monitor info
            if len(self._sct.monitors) > 1:
                primary = self._sct.monitors[1]
                return {
                    "index": 0,
                    "left": primary["left"],
                    "top": primary["top"],
                    "width": primary["width"],
                    "height": primary["height"]
                }

            return {}
        except Exception as e:
            logger.error(f"Failed to get monitor at point ({x},{y}): {e}")
            return {}

    def __del__(self):
        """Clean up resources."""
        if hasattr(self, '_sct'):
            self._sct.close()