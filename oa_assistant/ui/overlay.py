"""
Floating overlay window for the OA Assistant.
"""
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy
)
from PySide6.QtCore import Qt, QPoint, QRect, QSize, Signal
from PySide6.QtGui import QEnterEvent, QMouseEvent, QImage, QPixmap, QPainter, QColor, QFont, QPalette

from oa_assistant.core.config import settings
from oa_assistant.core.logging import logger
from oa_assistant.windows.window_manager import WindowManager


class OverlayWindow(QWidget):
    """
    A frameless, always-on-top overlay window with draggable header and resizable borders.
    """

    # Signals for preview interactions
    retake_requested = Signal()
    cancel_requested = Signal()
    # Signals for OCR interactions
    extract_text_requested = Signal()
    copy_text_requested = Signal()
    # Signals for AI interactions
    analyze_requested = Signal()
    copy_ai_response_requested = Signal()
    # Signals for capture interactions
    capture_processing_requested = Signal()
    # Signals for retry interactions
    retry_requested = Signal()

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

        # Content area - we use a container that we can swap content in
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_container.setLayout(self.content_layout)
        main_layout.addWidget(self.content_container, stretch=1)

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

        # Set up initial content
        self._show_normal_content()

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

    def _show_normal_content(self) -> None:
        """Show the normal ready state content."""
        # Clear current content
        self._clear_content_layout()

        # Create and add the normal message label
        normal_label = QLabel("Ready\n\nSelect a region to analyze.")
        normal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        normal_label.setStyleSheet(
            """
            background-color: rgba(30, 30, 30, 0.8);
            color: white;
            font-size: 14px;
            padding: 20px;
            border-radius: 5px;
            """
        )
        self.content_layout.addWidget(normal_label)

    def _clear_content_layout(self) -> None:
        """Remove all widgets from the content layout."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def show_capture_preview(self, capture_result) -> None:
        """
        Show a preview of the captured image.

        Args:
            capture_result: CaptureResult object containing the image and metadata
        """
        logger.debug("Showing capture preview")
        self._clear_content_layout()

        # Create preview content
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        preview_widget.setLayout(preview_layout)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.setSpacing(10)

        # Success message
        success_label = QLabel("Capture successful")
        success_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        preview_layout.addWidget(success_label)

        # Image preview
        if capture_result.image:
            image_label = QLabel()
            # Convert PIL image to QPixmap
            pixmap = self._pil_to_pixmap(capture_result.image)
            # Scale down to fit reasonably (max 200x200 while keeping aspect ratio)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            preview_layout.addWidget(image_label)

        # Dimensions info
        dim_label = QLabel(f"{capture_result.width} × {capture_result.height}")
        dim_label.setStyleSheet("font-size: 14px; color: white;")
        preview_layout.addWidget(dim_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        extract_button = QPushButton("Extract Text")
        extract_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 0.3);
                border: 1px solid rgba(120, 120, 120, 0.5);
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 0.5);
            }
        """)
        extract_button.clicked.connect(self.extract_text_requested.emit)
        button_layout.addWidget(extract_button)

        retake_button = QPushButton("Retake")
        retake_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 0.3);
                border: 1px solid rgba(120, 120, 120, 0.5);
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 0.5);
            }
        """)
        retake_button.clicked.connect(self.retake_requested.emit)
        button_layout.addWidget(retake_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 0.3);
                border: 1px solid rgba(120, 120, 120, 0.5);
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 0.5);
            }
        """)
        cancel_button.clicked.connect(self.cancel_requested.emit)
        button_layout.addWidget(cancel_button)

        preview_layout.addLayout(button_layout)

        # Add the preview widget to the content layout
        self.content_layout.addWidget(preview_widget)

    def _pil_to_pixmap(self, pil_image) -> QPixmap:
        """Convert a PIL Image to a QPixmap."""
        # Convert PIL image to RGBA if it isn't already
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")
        data = pil_image.tobytes("raw", "RGBA")
        qim = QImage(data, pil_image.width, pil_image.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qim)

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

    # Mouse event handling for dragging and resizing (unchanged from before)
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

    def show_capture_processing(self) -> None:
        """Show capture processing state in the overlay."""
        logger.debug("Showing capture processing state")
        self._clear_content_layout()

        # Create processing content
        processing_widget = QWidget()
        processing_layout = QVBoxLayout()
        processing_widget.setLayout(processing_layout)
        processing_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        processing_layout.setSpacing(10)

        # Processing message
        processing_label = QLabel("Capturing screen...")
        processing_label.setStyleSheet("font-size: 16px; color: white;")
        processing_layout.addWidget(processing_label)

        # Add the processing widget to the content layout
        self.content_layout.addWidget(processing_widget)

    def show_ocr_processing(self) -> None:
        """Show OCR processing state in the overlay."""
        logger.debug("Showing OCR processing state")
        self._clear_content_layout()

        # Create processing content
        processing_widget = QWidget()
        processing_layout = QVBoxLayout()
        processing_widget.setLayout(processing_layout)
        processing_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        processing_layout.setSpacing(10)

        # Processing message
        processing_label = QLabel("Reading screen...")
        processing_label.setStyleSheet("font-size: 16px; color: white;")
        processing_layout.addWidget(processing_label)

        # Add the processing widget to the content layout
        self.content_layout.addWidget(processing_widget)

    def show_ai_processing(self, provider_name: str = "AI") -> None:
        """Show AI processing state in the overlay.

        Args:
            provider_name: Name of the AI provider being used
        """
        logger.debug(f"Showing {provider_name} processing state")
        self._clear_content_layout()

        # Create processing content
        processing_widget = QWidget()
        processing_layout = QVBoxLayout()
        processing_widget.setLayout(processing_layout)
        processing_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        processing_layout.setSpacing(10)

        # Processing message
        processing_label = QLabel(f"Analyzing with {provider_name}...")
        processing_label.setStyleSheet("font-size: 16px; color: white;")
        processing_layout.addWidget(processing_label)

        # Add the processing widget to the content layout
        self.content_layout.addWidget(processing_widget)

    def show_capture_failed(self) -> None:
        """Show capture failed state in the overlay."""
        logger.debug("Showing capture failed state")
        self._clear_content_layout()

        # Create failed content
        failed_widget = QWidget()
        failed_layout = QVBoxLayout()
        failed_widget.setLayout(failed_layout)
        failed_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        failed_layout.setSpacing(10)

        # Failed message
        failed_label = QLabel("Screen capture failed")
        failed_label.setStyleSheet("font-size: 16px; color: #FF6B6B;")
        failed_layout.addWidget(failed_label)

        # Retry button
        retry_button = QPushButton("Retry")
        retry_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 0.3);
                border: 1px solid rgba(120, 120, 120, 0.5);
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 0.5);
            }
        """)
        retry_button.clicked.connect(lambda: self._on_retry_clicked.emit() if hasattr(self, '_on_retry_clicked') else None)
        failed_layout.addWidget(retry_button)

        # Add the failed widget to the content layout
        self.content_layout.addWidget(failed_widget)

    def show_ai_failed(self) -> None:
        """Show AI failed state in the overlay."""
        logger.debug("Showing AI failed state")
        self._clear_content_layout()

        # Create failed content
        failed_widget = QWidget()
        failed_layout = QVBoxLayout()
        failed_widget.setLayout(failed_layout)
        failed_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        failed_layout.setSpacing(10)

        # Failed message
        failed_label = QLabel("AI analysis failed")
        failed_label.setStyleSheet("font-size: 16px; color: #FF6B6B;")
        failed_layout.addWidget(failed_label)

        # Retry button
        retry_button = QPushButton("Retry")
        retry_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 0.3);
                border: 1px solid rgba(120, 120, 120, 0.5);
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 0.5);
            }
        """)
        retry_button.clicked.connect(lambda: self._on_retry_clicked.emit() if hasattr(self, '_on_retry_clicked') else None)
        failed_layout.addWidget(retry_button)

        # Add the failed widget to the content layout
        self.content_layout.addWidget(failed_widget)

    
    def show_ocr_results(self, result) -> None:
        """
        Show OCR results in the overlay.

        Args:
            result: OCRResult object containing extracted text and metadata
        """
        logger.debug("Showing OCR results")
        self._clear_content_layout()

        # Create results content
        results_widget = QWidget()
        results_layout = QVBoxLayout()
        results_widget.setLayout(results_layout)
        results_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_layout.setSpacing(10)

        # Results message
        if result.is_empty():
            results_label = QLabel("No text found")
        else:
            # Truncate text for display if too long
            display_text = result.text
            if len(display_text) > 100:
                display_text = display_text[:100] + "..."
            results_label = QLabel(display_text)
            results_label.setWordWrap(True)

        results_label.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 0.6);
                color: white;
                font-size: 14px;
                padding: 15px;
                border-radius: 3px;
                min-height: 40px;
            }
        """)
        results_layout.addWidget(results_label)

        # Confidence and metadata
        if result.confidence is not None:
            conf_label = QLabel(f"Confidence: {result.confidence:.1f}%")
            conf_label.setStyleSheet("font-size: 12px; color: #CCCCCC;")
            results_layout.addWidget(conf_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        extract_button = QPushButton("Extract Text")
        extract_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 0.3);
                border: 1px solid rgba(120, 120, 120, 0.5);
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 0.5);
            }
        """)
        extract_button.clicked.connect(self.extract_text_requested.emit)
        button_layout.addWidget(extract_button)

        analyze_button = QPushButton("Analyze")
        analyze_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 0.3);
                border: 1px solid rgba(120, 120, 120, 0.5);
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 0.5);
            }
        """)
        analyze_button.clicked.connect(self.analyze_requested.emit)
        button_layout.addWidget(analyze_button)

        copy_button = QPushButton("Copy Text")
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 0.3);
                border: 1px solid rgba(120, 120, 120, 0.5);
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 0.5);
            }
        """)
        copy_button.clicked.connect(self.copy_text_requested.emit)
        button_layout.addWidget(copy_button)

        results_layout.addLayout(button_layout)

        # Add the results widget to the content layout
        self.content_layout.addWidget(results_widget)

    def show_ai_results(self, result) -> None:
        """
        Show AI results in the overlay.

        Args:
            result: AIResponse object containing AI analysis and metadata
        """
        logger.debug("Showing AI results")
        self._clear_content_layout()

        # Create results content
        results_widget = QWidget()
        results_layout = QVBoxLayout()
        results_widget.setLayout(results_layout)
        results_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_layout.setSpacing(10)

        # Results message
        if result.is_empty():
            results_label = QLabel("No analysis available")
        else:
            # Truncate text for display if too long
            display_text = result.text
            if len(display_text) > 100:
                display_text = display_text[:100] + "..."
            results_label = QLabel(display_text)
            results_label.setWordWrap(True)

        results_label.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 0.6);
                color: white;
                font-size: 14px;
                padding: 15px;
                border-radius: 3px;
                min-height: 40px;
            }
        """)
        results_layout.addWidget(results_label)

        # Latency and metadata
        if result.latency is not None:
            latency_label = QLabel(f"Latency: {result.latency:.2f}s")
            latency_label.setStyleSheet("font-size: 12px; color: #CCCCCC;")
            results_layout.addWidget(latency_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        copy_button = QPushButton("Copy Response")
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 0.3);
                border: 1px solid rgba(120, 120, 120, 0.5);
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 0.5);
            }
        """)
        copy_button.clicked.connect(self.copy_ai_response_requested.emit)
        button_layout.addWidget(copy_button)

        retake_button = QPushButton("Retake")
        retake_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(80, 80, 80, 0.3);
                border: 1px solid rgba(120, 120, 120, 0.5);
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(60, 60, 60, 0.5);
            }
        """)
        retake_button.clicked.connect(self.retake_requested.emit)
        button_layout.addWidget(retake_button)

        results_layout.addLayout(button_layout)

        # Add the results widget to the content layout
        self.content_layout.addWidget(results_widget)

    def closeEvent(self, event) -> None:
        """Handle window close events."""
        logger.info("Overlay window closed")
        super().closeEvent(event)