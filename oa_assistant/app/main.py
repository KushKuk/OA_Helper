"""
Main entry point for the OA Assistant application.
"""
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from oa_assistant.core.config import settings
from oa_assistant.core.logging import logger
from oa_assistant.ui.overlay import OverlayWindow


def main() -> None:
    """
    Initialize and run the application.
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")

    app = QApplication(sys.argv)
    app.setApplicationName(settings.APP_NAME)
    app.setApplicationVersion(settings.VERSION)

    # Create and show the overlay window
    overlay = OverlayWindow()
    overlay.show()
    logger.info("Overlay window displayed")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()