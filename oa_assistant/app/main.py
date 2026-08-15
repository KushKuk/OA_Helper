"""
Main entry point for the OA Assistant application.
"""
import sys

from oa_assistant.app.application import OAAssistantApplication


def main() -> None:
    """
    Initialize and run the application.
    """
    app = OAAssistantApplication()
    sys.exit(app.start())


if __name__ == "__main__":
    main()