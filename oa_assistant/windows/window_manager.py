"""
Window management utilities for Windows desktop integration.
"""
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QRect, QSize
from PySide6.QtGui import QGuiApplication

from oa_assistant.core.config import settings
from oa_assistant.core.logging import logger


class WindowManager:
    """
    Manages window behavior and Windows-specific functionality.
    Separates window management logic from UI logic.
    """

    def __init__(self, window):
        """
        Initialize the window manager.

        Args:
            window: The QWindow or QWidget to manage
        """
        self.window = window
        self.logger = logger

        # Window state tracking
        self._is_visible = False
        self._is_minimized = False

        # Geometry persistence (session-based)
        self._saved_geometry = None

        self.logger.debug("WindowManager initialized")

    def show(self) -> None:
        """Show the window."""
        if not self.window.isVisible():
            self.window.show()
            self._is_visible = True
            self.logger.debug("Window shown")

    def hide(self) -> None:
        """Hide the window."""
        if self.window.isVisible():
            self.window.hide()
            self._is_visible = False
            self.logger.debug("Window hidden")

    def toggle_visibility(self) -> None:
        """Toggle window visibility."""
        if self.window.isVisible():
            self.hide()
        else:
            self.show()

    def minimize(self) -> None:
        """Minimize the window."""
        if self.window.isVisible() and not self._is_minimized:
            self.window.showMinimized()
            self._is_minimized = True
            self.logger.debug("Window minimized")

    def restore(self) -> None:
        """Restore the window from minimized state."""
        if self._is_minimized:
            self.window.showNormal()
            self._is_minimized = False
            self.logger.debug("Window restored")

    def is_visible(self) -> bool:
        """Check if window is currently visible."""
        return self.window.isVisible() and not self._is_minimized

    def set_always_on_top(self, always_on_top: bool) -> None:
        """
        Set the always-on-top property.

        Args:
            always_on_top: Whether window should stay on top
        """
        self.window.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint,
            always_on_top
        )
        # Need to re-show for flag change to take effect
        was_visible = self.window.isVisible()
        if was_visible:
            self.window.hide()
            self.window.show()
        self.logger.debug(f"Always-on-top set to: {always_on_top}")

    def get_available_monitors(self):
        """Get list of available monitors."""
        return QGuiApplication.screens()

    def get_primary_monitor(self):
        """Get the primary monitor."""
        return QGuiApplication.primaryScreen()

    def get_current_monitor(self):
        """
        Get the monitor that currently contains the window.

        Returns:
            QScreen: The monitor containing the window, or primary monitor if not found
        """
        window_center = self.window.frameGeometry().center()

        for screen in self.get_available_monitors():
            if screen.geometry().contains(window_center):
                return screen

        # Fallback to primary monitor
        return self.get_primary_monitor()

    def get_monitor_geometry(self, monitor=None):
        """
        Get the geometry of a monitor.

        Args:
            monitor: QScreen object, or None for current monitor

        Returns:
            QRect: Monitor geometry
        """
        if monitor is None:
            monitor = self.get_current_monitor()
        return monitor.geometry()

    def position_on_primary_monitor(self, margin_percent: float = 0.05) -> None:
        """
        Position window on primary monitor with optional margin.

        Args:
            margin_percent: Margin as percentage of monitor size (0.0 to 0.5)
        """
        primary = self.get_primary_monitor()
        monitor_geom = primary.geometry()

        # Calculate position with margin
        margin_x = int(monitor_geom.width() * margin_percent)
        margin_y = int(monitor_geom.height() * margin_percent)

        x = monitor_geom.x() + margin_x
        y = monitor_geom.y() + margin_y

        self.window.move(x, y)
        self.logger.debug(f"Positioned on primary monitor at ({x}, {y})")

    def position_on_current_monitor(self, margin_percent: float = 0.05) -> None:
        """
        Position window on current monitor with optional margin.

        Args:
            margin_percent: Margin as percentage of monitor size (0.0 to 0.5)
        """
        monitor = self.get_current_monitor()
        monitor_geom = monitor.geometry()

        # Calculate position with margin
        margin_x = int(monitor_geom.width() * margin_percent)
        margin_y = int(monitor_geom.height() * margin_percent)

        x = monitor_geom.x() + margin_x
        y = monitor_geom.y() + margin_y

        self.window.move(x, y)
        self.logger.debug(f"Positioned on current monitor at ({x}, {y})")

    def center_on_current_monitor(self) -> None:
        """Center window on the current monitor."""
        monitor = self.get_current_monitor()
        monitor_geom = monitor.geometry()
        window_geom = self.window.frameGeometry()

        x = monitor_geom.x() + (monitor_geom.width() - window_geom.width()) // 2
        y = monitor_geom.y() + (monitor_geom.height() - window_geom.height()) // 2

        self.window.move(x, y)
        self.logger.debug(f"Centered on current monitor at ({x}, {y})")

    def ensure_on_screen(self) -> None:
        """
        Ensure window is fully visible on screen.
        If window is off-screen, move it to primary monitor.
        """
        window_geom = self.window.frameGeometry()

        # Check if window is completely off-screen on all monitors
        on_any_screen = False
        for screen in self.get_available_monitors():
            if screen.geometry().intersects(window_geom):
                on_any_screen = True
                break

        if not on_any_screen:
            # Window is completely off-screen, move to primary monitor
            self.position_on_primary_monitor()
            self.logger.warning("Window was off-screen, moved to primary monitor")
        else:
            # Window is at least partially visible, adjust to fit if needed
            current_screen = self.get_current_monitor()
            screen_geom = current_screen.geometry()

            # Adjust x if needed
            if window_geom.x() < screen_geom.x():
                self.window.move(screen_geom.x(), window_geom.y())
            elif window_geom.x() + window_geom.width() > screen_geom.x() + screen_geom.width():
                self.window.move(
                    screen_geom.x() + screen_geom.width() - window_geom.width(),
                    window_geom.y()
                )

            # Adjust y if needed
            if window_geom.y() < screen_geom.y():
                self.window.move(window_geom.x(), screen_geom.y())
            elif window_geom.y() + window_geom.height() > screen_geom.y() + screen_geom.height():
                self.window.move(
                    window_geom.x(),
                    screen_geom.y() + screen_geom.height() - window_geom.height()
                )

            self.logger.debug("Ensured window is on screen")

    def save_geometry(self) -> None:
        """Save current window geometry for later restoration."""
        if self.window.isVisible():
            self._saved_geometry = self.window.frameGeometry()
            self.logger.debug(f"Saved window geometry: {self._saved_geometry}")

    def restore_geometry(self) -> None:
        """Restore window geometry from saved state."""
        if self._saved_geometry is not None:
            self.window.setGeometry(self._saved_geometry)
            self.logger.debug(f"Restored window geometry: {self._saved_geometry}")

    def get_window_geometry(self) -> QRect:
        """Get current window geometry."""
        return self.window.frameGeometry()

    def set_window_geometry(self, rect: QRect) -> None:
        """Set window geometry."""
        self.window.setGeometry(rect)
        self.logger.debug(f"Set window geometry: {rect}")

    def get_window_size(self) -> QSize:
        """Get current window size."""
        return self.window.size()

    def set_window_size(self, size: QSize) -> None:
        """Set window size."""
        self.window.resize(size)
        self.logger.debug(f"Set window size: {size}")

    def get_window_position(self) -> QPoint:
        """Get current window position."""
        return self.window.pos()

    def set_window_position(self, pos: QPoint) -> None:
        """Set window position."""
        self.window.move(pos)
        self.logger.debug(f"Set window position: {pos}")


# Import Qt at module level to avoid circular imports
from PySide6.QtCore import Qt