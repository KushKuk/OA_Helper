"""
Application controller for coordinating overlay, window manager, and hotkeys.
"""
import sys
import time

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QThread, QObject, Signal

from oa_assistant.core.config import settings
from oa_assistant.core.logging import logger
from oa_assistant.ui.overlay import OverlayWindow
from oa_assistant.windows.hotkeys import hotkey_manager
from oa_assistant.windows.window_manager import WindowManager
from oa_assistant.capture.screen_capture import ScreenCapture
from oa_assistant.capture.region_selector import RegionSelector
from oa_assistant.ocr.service import ocr_service
from oa_assistant.ocr.models import OCRMode
from oa_assistant.ai.service import ai_service
from oa_assistant.ai.models import AnalysisContext


class OCRWorker(QObject):
    """
    Worker object for performing OCR in a separate thread.
    """
    finished = Signal(object)

    def __init__(self, image, ocr_service, mode):
        super().__init__()
        self.image = image
        self.ocr_service = ocr_service
        self.mode = mode

    def process(self):
        """
        Process the OCR operation.
        """
        try:
            result = self.ocr_service.recognize(self.image, mode=self.mode)
            self.finished.emit(result)
        except Exception as e:
            # Log the error and emit an empty result
            logger.error(f"OCR processing failed: {e}")
            from oa_assistant.ocr.models import OCRResult
            empty_result = OCRResult(text="", provider="error", processing_time=0.0, mode=self.mode)
            self.finished.emit(empty_result)


class AIWorker(QObject):
    """
    Worker object for performing AI analysis in a separate thread.
    """
    finished = Signal(object)

    def __init__(self, context, ai_service):
        super().__init__()
        self.context = context
        self.ai_service = ai_service

    def process(self):
        """
        Process the AI analysis operation.
        """
        try:
            result = self.ai_service.analyze(self.context)
            self.finished.emit(result)
        except Exception as e:
            # Log the error and emit an error result
            logger.error(f"AI processing failed: {e}")
            from oa_assistant.ai.models import AIResponse
            error_result = AIResponse(
                text=f"AI analysis failed: {str(e)}",
                provider="error",
                model="error",
                latency=0.0
            )
            self.finished.emit(error_result)


class OAAssistantApplication:
    """
    Main application controller coordinating all components.
    """

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(settings.APP_NAME)
        self.app.setApplicationVersion(settings.VERSION)

        # Create overlay window
        self.overlay = OverlayWindow()
        self.window_manager = WindowManager(self.overlay)

        # Initialize screen capture
        self.screen_capture = ScreenCapture()

        # Set up hotkey callbacks
        hotkey_manager.hotkey_triggered.connect(self._handle_hotkey_action)

        # Set up overlay callbacks
        self.overlay.extract_text_requested.connect(self._on_extract_text)
        self.overlay.copy_text_requested.connect(self._on_copy_text)
        self.overlay.analyze_requested.connect(self._on_analyze)

        logger.info("OA Assistant application initialized")

        # Store last OCR result for text extraction/copy
        self._last_ocr_result = None
        # Store last AI result for copy functionality
        self._last_ai_result = None

    def _handle_hotkey_action(self, action_name: str) -> None:
        """
        Handle hotkey actions from the hotkey manager.

        Args:
            action_name: The action name triggered by the hotkey
        """
        logger.debug(f"Handling hotkey action: {action_name}")
        if action_name == "toggle_overlay":
            self.toggle_overlay()
        elif action_name == "capture_region":
            self._start_capture_region()
        # Future actions can be added here

    def toggle_overlay(self) -> None:
        """Toggle the overlay visibility."""
        if self.overlay.isVisible():
            self.overlay.hide_overlay()
        else:
            self.overlay.show_overlay()

    def _start_capture_region(self) -> None:
        """Start the region capture process."""
        logger.info("Starting region capture")

        # Hide the overlay during capture
        if self.overlay.isVisible():
            self.overlay.hide_overlay()
            self._overlay_was_visible = True
        else:
            self._overlay_was_visible = False

        # Create and show region selector
        self.region_selector = RegionSelector()
        self.region_selector.selection_complete = self._on_region_selected
        self.region_selector.selection_cancelled = self._on_capture_cancelled
        self.region_selector.show()

    def _on_region_selected(self, rect) -> None:
        """Handle region selection completion."""
        logger.debug(f"Region selected: {rect}")

        # Hide the selector
        self.region_selector.hide()

        # Capture the selected region
        capture_result = self.screen_capture.capture_region(
            rect.x(), rect.y(), rect.width(), rect.height()
        )

        if capture_result and capture_result.is_valid():
            self._show_capture_preview(capture_result)
        else:
            logger.warning("Capture failed or invalid selection")
            self._on_capture_cancelled()

    def _on_capture_cancelled(self) -> None:
        """Handle capture cancellation."""
        logger.debug("Capture cancelled")
        if hasattr(self, 'region_selector'):
            self.region_selector.hide()
        self._restore_overlay()

    def _show_capture_preview(self, capture_result: 'ScreenCaptureInterface.CaptureResult') -> None:
        """Show capture preview in the overlay."""
        logger.debug("Showing capture preview")

        # Store the capture result for potential retake
        self._last_capture_result = capture_result

        # Perform OCR on the captured image
        self._perform_ocr(capture_result.image)

        # Update overlay with preview
        self.overlay.show_capture_preview(capture_result)

        # Restore overlay visibility
        self._restore_overlay()

    def _restore_overlay(self) -> None:
        """Restore overlay visibility to its original state."""
        if getattr(self, '_overlay_was_visible', False):
            self.overlay.show_overlay()
        elif not self.overlay.isVisible():
            # Default to showing overlay if it was hidden
            self.overlay.show_overlay()

    def start(self) -> int:
        """
        Start the application.

        Returns:
            int: Application exit code
        """
        logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")

        # Show overlay initially
        self.overlay.show_overlay()

        # Set window handle for hotkey registration
        # Use NULL (0) to register as a global hotkey for the current user
        hotkey_manager.set_window_handle(0)

        # Use a timer to delay the start of the hotkey manager to allow the window to be fully created
        QTimer.singleShot(100, self._start_hotkey_manager)

        logger.info("OA Assistant application started")

        # Run the Qt event loop
        return self.app.exec()

    def _start_hotkey_manager(self):
        """
        Start the hotkey manager after a short delay.
        """
        if not hotkey_manager.start():
            logger.warning("Failed to start hotkey manager - hotkeys may not work")

    def _perform_ocr(self, image) -> None:
        """
        Perform OCR on the captured image and update the overlay with results.

        Args:
            image: PIL Image to perform OCR on
        """
        logger.info("Starting OCR processing")

        # Show processing state in overlay
        self.overlay.show_ocr_processing()

        # Perform OCR in a way that doesn't block the GUI
        # Use QThread to perform OCR in background
        self._ocr_thread = QThread()
        self._ocr_worker = OCRWorker(image, ocr_service, OCRMode.GENERAL_TEXT)
        self._ocr_worker.moveToThread(self._ocr_thread)
        self._ocr_thread.started.connect(self._ocr_worker.process)
        self._ocr_worker.finished.connect(self._on_ocr_finished)
        self._ocr_worker.finished.connect(self._ocr_thread.quit)
        self._ocr_worker.finished.connect(self._ocr_worker.deleteLater)
        self._ocr_thread.finished.connect(self._ocr_thread.deleteLater)
        self._ocr_thread.start()

    def _perform_ai(self, ocr_result) -> None:
        """
        Perform AI analysis on the OCR result and update the overlay with results.

        Args:
            ocr_result: OCRResult object containing extracted text and metadata
        """
        logger.info("Starting AI analysis")

        # Show processing state in overlay
        self.overlay.show_ocr_processing()

        # Prepare context for AI analysis
        context = AnalysisContext(
            text=ocr_result.text,
            source="ocr",
            capture_width=getattr(ocr_result, 'width', None),
            capture_height=getattr(ocr_result, 'height', None),
            ocr_mode=ocr_result.mode.value if ocr_result.mode else None
        )

        # Perform AI in a way that doesn't block the GUI
        # Use QThread to perform AI in background
        self._ai_thread = QThread()
        self._ai_worker = AIWorker(context, ai_service)
        self._ai_worker.moveToThread(self._ai_thread)
        self._ai_thread.started.connect(self._ai_worker.process)
        self._ai_worker.finished.connect(self._on_ai_finished)
        self._ai_worker.finished.connect(self._ai_thread.quit)
        self._ai_worker.finished.connect(self._ai_worker.deleteLater)
        self._ai_thread.finished.connect(self._ai_thread.deleteLater)
        self._ai_thread.start()

    def _on_extract_text(self) -> None:
        """
        Handle extract text request from overlay.
        """
        logger.info("Extract text requested")
        if self._last_ocr_result and not self._last_ocr_result.is_empty():
            # In a real implementation, we might show the full text in a dialog
            # For now, we'll just log it
            logger.info(f"Extracted text: {self._last_ocr_result.text}")
        else:
            logger.info("No text to extract")

    def _on_copy_text(self) -> None:
        """
        Handle copy text request from overlay.
        """
        logger.info("Copy text requested")
        if self._last_ocr_result and not self._last_ocr_result.is_empty():
            # Copy text to clipboard
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(self._last_ocr_result.text)
            logger.info("Text copied to clipboard")
        else:
            logger.info("No text to copy")

    def _on_copy_ai_response(self) -> None:
        """
        Handle copy AI response request from overlay.
        """
        logger.info("Copy AI response requested")
        if self._last_ai_result and not self._last_ai_result.is_empty():
            # Copy AI response to clipboard
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(self._last_ai_result.text)
            logger.info("AI response copied to clipboard")
        else:
            logger.info("No AI response to copy")

    def _on_ocr_finished(self, result) -> None:
        """
        Handle finished OCR operation from worker thread.

        Args:
            result: OCRResult object from the OCR worker
        """
        logger.info(f"OCR worker finished: '{result.text[:50]}{'...' if len(result.text) > 50 else ''}'")

        # Store result for extract/copy text functionality
        self._last_ocr_result = result

        # Update overlay with OCR results
        self.overlay.show_ocr_results(result)

        # Trigger AI analysis
        self._perform_ai(result)


def _on_ai_finished(self, result) -> None:
        """
        Handle finished AI operation from worker thread.

        Args:
            result: AIResponse object from the AI worker
        """
        logger.info(f"AI worker finished: '{result.text[:50]}{'...' if len(result.text) > 50 else ''}'")

        # Store result for copy functionality
        self._last_ai_result = result

        # Update overlay with AI results
        self.overlay.show_ai_results(result)

    def stop(self) -> None:
        """Stop the application and clean up resources."""
        logger.info("Stopping OA Assistant application")

        # Stop hotkey manager
        hotkey_manager.stop()

        logger.info("OA Assistant application stopped")


def main() -> int:
    """
    Main entry point for the OA Assistant application.

    Returns:
        int: Application exit code
    """
    app_controller = OAAssistantApplication()
    return app_controller.stop()


if __name__ == "__main__":
    sys.exit(main())