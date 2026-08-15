"""
Floating overlay window for the OA Assistant.
"""
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
)
from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import QEnterEvent, QMouseEvent

from oa_assistant.core.config import settings
from oa_assistant.core.logging import logger
from oa_assistant.windows.window_manager import WindowManager


class OverlayWindow(QWidget):
    """
    A frameless, always-on-top overlay window with draggable header and resizable borders.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Window state
        self._is_dragging = False
        self._drag_position = QPoint()
        self._is_resizing = False
        self._resize_direction = None
        self._resize_rect = QRect()

        # Configuration
        self.opacity = settings.OVERLAY_OPACITY
        self.always_on_top = settings.OVERLAY_ALWAYS_ON_TOP
        self.width = settings.OVERLAY_WIDTH
        self.height = settings.OVERLAY_HEIGHT
        self.min_width = settings.OVERLAY_MIN_WIDTH
        self.min_height = settings.OVERLAY_MIN_HEIGHT

        self.setWindowOpacity(self.opacity)
        if self.always_on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        self.setMinimumSize(self.min_width, self.min_height)
        self.resize(self.width, self.height)

        # Window manager for Windows-specific behavior
        self.window_manager = WindowManager(self)
        # Set always-on-top based on configuration
        self.window_manager.set_always_on_top(self.always_on_top)

        self._setup_ui()
        logger.info("Overlay window initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Content area
        content = QLabel("Ready\n\nSelect a region to analyze.")
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.setStyleSheet(
            """
            background-color: rgba(30, 30, 30, 0.8);
            color: white;
            font-size: 14px;
            """
        )
        main_layout.addWidget(content, stretch=1)

        self.setLayout(main_layout)

        # Apply styles
        self.setStyleSheet(
            """
            OverlayWindow {
                background-color: rgba(30, 30, 30, 0.9);
                border: 1px solid rgba(80, 80, 80, 0.5);
                border-radius: 5px;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 80, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(80, 80, 80, 0.5);
            }
            """
        )

    def _create_header(self) -> QWidget:
        """Create the custom header with title and buttons."""
        header = QWidget()
        header.setFixedHeight(30)
        header.setStyleSheet(
            """
            QWidget {
                background-color: rgba(20, 20, 20, 0.9);
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            """
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(0)

        # Title
        title = QLabel(settings.APP_NAME)
        title.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # Minimize/Hide button
        hide_button = QWidget()
        hide_button.setFixedSize(30, 30)
        hide_button_layout = QHBoxLayout()
        hide_button_layout.setContentsMargins(0, 0, 0, 0)
        hide_icon = QLabel("−")
        hide_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hide_button_layout.addWidget(hide_icon)
        hide_button.setLayout(hide_button_layout)
        hide_button.mousePressEvent = lambda event: self.hide_overlay()
        layout.addWidget(hide_button)

        # Close button
        close_button = QWidget()
        close_button.setFixedSize(30, 30)
        close_button_layout = QHBoxLayout()
        close_button_layout.setContentsMargins(0, 0, 0, 0)
        close_icon = QLabel("×")
        close_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        close_button_layout.addWidget(close_icon)
        close_button.setLayout(close_button_layout)
        close_button.mousePressEvent = lambda event: self.close()
        layout.addWidget(close_button)

        header.setLayout(layout)
        return header

    def show_overlay(self) -> None:
        """Show the overlay window."""
        self.window_manager.show()
        logger.info("Overlay window shown")

    def hide_overlay(self) -> None:
        """Hide the overlay window."""
        self.window_manager.hide()
        logger.info("Overlay window hidden")

    def toggle_overlay(self) -> None:
        """Toggle the overlay window visibility."""
        self.window_manager.toggle_visibility()

    # Mouse event handling for dragging and resizing
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events for dragging and resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we are near the edge for resizing
            self._resize_direction = self._get_resize_direction(event.position().toPoint())
            if self._resize_direction:
                self._is_resizing = True
                self._resize_rect = self.geometry()
                self.setCursor(self._get_cursor_for_direction(self._resize_direction))
            else:
                # Start dragging
                self._is_dragging = True
                self._drag_position = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move events for dragging and resizing."""
        if self._is_resizing:
            self._handle_resize(event.globalPosition().toPoint())
        elif self._is_dragging:
            self.move(
                event.globalPosition().toPoint() - self._drag_position
            )
            event.accept()
        else:
            # Update cursor based on position
            direction = self._get_resize_direction(event.position().toPoint())
            self.setCursor(self._get_cursor_for_direction(direction))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release events."""
        self._is_dragging = False
        self._is_resizing = False
        self._resize_direction = None
        self.setCursor(Qt.ArrowCursor)

    def _get_resize_direction(self, pos: QPoint) -> str:
        """Determine which resize direction based on position."""
        # Define the resize border width
        border_width = 5
        rect = self.rect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()

        # Determine if we are on each edge
        left = pos.x() <= border_width
        right = pos.x() >= w - border_width
        top = pos.y() <= border_width
        bottom = pos.y() >= h - border_width

        if left and top:
            return "top-left"
        elif right and top:
            return "top-right"
        elif left and bottom:
            return "bottom-left"
        elif right and bottom:
            return "bottom-right"
        elif left:
            return "left"
        elif right:
            return "right"
        elif top:
            return "top"
        elif bottom:
            return "bottom"
        else:
            return ""

    def _get_cursor_for_direction(self, direction: str) -> Qt.CursorShape:
        """Get the appropriate cursor shape for the resize direction."""
        cursors = {
            "left": Qt.SizeHorCursor,
            "right": Qt.SizeHorCursor,
            "top": Qt.SizeVerCursor,
            "bottom": Qt.SizeVerCursor,
            "top-left": Qt.SizeFDiagCursor,
            "top-right": Qt.SizeBDiagCursor,
            "bottom-left": Qt.SizeBDiagCursor,
            "bottom-right": Qt.SizeFDiagCursor,
        }
        return cursors.get(direction, Qt.ArrowCursor)

    def _handle_resize(self, global_pos: QPoint) -> None:
        """Handle the resize operation."""
        rect = QRect(self._resize_rect)
        delta = global_pos - self._resize_rect.topLeft()

        if "left" in self._resize_direction:
            rect.setLeft(rect.left() + delta.x())
        if "right" in self._resize_direction:
            rect.setRight(rect.right() + delta.x())
        if "top" in self._resize_direction:
            rect.setTop(rect.top() + delta.y())
        if "bottom" in self._resize_direction:
            rect.setBottom(rect.bottom() + delta.y())

        # Enforce minimum size
        if rect.width() < self.min_width:
            if "left" in self._resize_direction:
                rect.setLeft(rect.right() - self.min_width)
            else:
                rect.setRight(rect.left() + self.min_width)
        if rect.height() < self.min_height:
            if "top" in self._resize_direction:
                rect.setTop(rect.bottom() - self.min_height)
            else:
                rect.setBottom(rect.top() + self.min_height)

        self.setGeometry(rect)

    def enterEvent(self, event: QEnterEvent) -> None:
        """Handle mouse enter events."""
        # Reset cursor when leaving and re-entering
        self.setCursor(Qt.ArrowCursor)
        super().enterEvent(event)

    def closeEvent(self, event) -> None:
        """Handle window close events."""
        logger.info("Overlay window closed")
        super().closeEvent(event)