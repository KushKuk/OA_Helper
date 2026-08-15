"""
Region selection widget for screen capture.
"""
from PySide6.QtWidgets import (
    QApplication, QWidget, QRubberBand,
    QLabel, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QGuiApplication
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RegionSelector(QWidget):
    """
    Full-screen widget for selecting a screen region.
    Displays a dimmed overlay with a rubber band selection tool.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # Make it cover the entire virtual desktop
        self.setGeometry(QGuiApplication.primaryScreen().virtualGeometry())

        # Selection state
        self.origin: Optional[QPoint] = None
        self.selection_rect: Optional[QRect] = None
        self.is_selecting = False
        self.rubber_band: Optional[QRubberBand] = None

        # Preview label for dimensions
        self.dim_label = QLabel(self)
        self.dim_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
        """)
        self.dim_label.hide()

        logger.debug("RegionSelector initialized")

    def showEvent(self, event):
        """Ensure widget covers full virtual desktop when shown."""
        self.setGeometry(QGuiApplication.primaryScreen().virtualGeometry())
        super().showEvent(event)

    def paintEvent(self, event):
        """Paint the dimmed overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Semi-transparent black overlay
        overlay_color = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), overlay_color)

        # If we have a selection, make that area clear
        if self.selection_rect and not self.selection_rect.isEmpty():
            # Clear the selection area
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.selection_rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # Draw selection border
            pen = QPen(QColor(0, 120, 215, 255), 2)
            painter.setPen(pen)
            painter.drawRect(self.selection_rect)

    def mousePressEvent(self, event):
        """Handle mouse press - start selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.position().toPoint()
            self.is_selecting = True

            if not self.rubber_band:
                self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)

            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
            self.dim_label.move(self.origin + QPoint(10, 10))
            self.dim_label.show()

            logger.debug(f"Selection started at {self.origin}")

    def mouseMoveEvent(self, event):
        """Handle mouse move - update selection."""
        if not self.is_selecting or not self.origin:
            return

        current_pos = event.position().toPoint()
        rect = QRect(self.origin, current_pos).normalized()

        # Update rubber band
        if self.rubber_band:
            self.rubber_band.setGeometry(rect)

        # Update dimension label
        width = rect.width()
        height = rect.height()
        self.dim_label.setText(f"{width} × {height}")
        self.dim_label.move(min(current_pos.x() + 10, self.width() - self.dim_label.width() - 10),
                           min(current_pos.y() + 10, self.height() - self.dim_label.height() - 10))

        # Store selection rect for painting
        self.selection_rect = rect
        self.update()  # Trigger repaint

        logger.debug(f"Selection updated: {rect}")

    def mouseReleaseEvent(self, event):
        """Handle mouse release - finish selection."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False

            if self.rubber_band:
                self.rubber_band.hide()

            # Finalize selection
            if self.origin:
                final_pos = event.position().toPoint()
                self.selection_rect = QRect(self.origin, final_pos).normalized()

                # Hide dimension label
                self.dim_label.hide()

                logger.debug(f"Selection completed: {self.selection_rect}")

                # Trigger completion - parent should handle this
                if hasattr(self, 'selection_complete') and self.selection_complete:
                    self.selection_complete(self.selection_rect)
            else:
                self.selection_rect = None
                self.update()

    def keyPressEvent(self, event):
        """Handle key presses - Escape to cancel."""
        if event.key() == Qt.Key.Key_Escape:
            logger.debug("Region selection cancelled via Escape")
            self.hide()
            if hasattr(self, 'selection_cancelled') and self.selection_cancelled:
                self.selection_cancelled()
        else:
            super().keyPressEvent(event)

    def get_selection(self) -> Optional[QRect]:
        """
        Get the current selection rectangle.

        Returns:
            QRect: The selected region, or None if no valid selection
        """
        if self.selection_rect and not self.selection_rect.isEmpty():
            return self.selection_rect
        return None

    def clear_selection(self):
        """Clear the current selection."""
        self.selection_rect = None
        if self.rubber_band:
            self.rubber_band.hide()
        self.dim_label.hide()
        self.update()