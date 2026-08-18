"""
Configuration module for the OA Assistant.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.
    """
    # Application
    APP_NAME: str = "OA Assistant"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    # AI Provider
    AI_PROVIDER: str = "gemini"  # or "gemini", "nemotron"
    AI_MODEL: str = "gemini-1.5-flash"
    GEMINI_API_KEY: Optional[str] = None
    NEMOTRON_API_KEY: Optional[str] = None
    NEMOTRON_MODEL: str = "nemotron-3-8b-chat"
    NEMOTRON_API_URL: str = "https://ai.api.nvidia.com/v1/nemotron"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # OCR Provider
    OCR_PROVIDER: str = "tesseract"  # or "easyocr", etc.
    TESSERACT_CMD: Optional[str] = None  # Path to tesseract executable

    # Screen Capture
    SCREEN_CAPTURE_PROVIDER: str = "mss"
    CAPTURE_MODE: str = "current_monitor"  # or "all_monitors"

    # Hotkeys
    HOTKEY_TOGGLE_OVERLAY: str = "ctrl+space"
    HOTKEY_CAPTURE_REGION: str = "ctrl+shift+c"

    # Overlay settings
    OVERLAY_OPACITY: float = 0.9
    OVERLAY_WIDTH: int = 400
    OVERLAY_HEIGHT: int = 500
    OVERLAY_ALWAYS_ON_TOP: bool = True
    OVERLAY_MIN_WIDTH: int = 200
    OVERLAY_MIN_HEIGHT: int = 150

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables
    )


# Global settings instance
settings = Settings()