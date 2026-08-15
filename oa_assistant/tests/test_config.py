"""
Test configuration module.
"""
import sys
import os
# Add the project root directory to sys.path so that oa_assistant can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from oa_assistant.core.config import settings


def test_settings_loaded():
    """Test that settings are loaded correctly."""
    assert settings.APP_NAME == "OA Assistant"
    assert settings.VERSION == "0.1.0"
    assert settings.DEBUG is False
    assert settings.LOG_LEVEL == "INFO"
    assert settings.AI_PROVIDER == "openai"
    assert settings.OCR_PROVIDER == "tesseract"
    assert settings.SCREEN_CAPTURE_PROVIDER == "mss"
    assert settings.HOTKEY_TOGGLE_OVERLAY == "ctrl+alt+o"
    assert settings.HOTKEY_CAPTURE_REGION == "ctrl+alt+c"
    assert settings.OVERLAY_OPACITY == 0.9
    assert settings.OVERLAY_WIDTH == 400
    assert settings.OVERLAY_HEIGHT == 500


def test_settings_from_env(monkeypatch):
    """Test that settings can be overridden by environment variables."""
    monkeypatch.setenv("APP_NAME", "Test Assistant")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # Reload settings to pick up environment changes
    from importlib import reload
    from oa_assistant.core import config
    reload(config)

    assert config.settings.APP_NAME == "Test Assistant"
    assert config.settings.DEBUG is True
    assert config.settings.LOG_LEVEL == "DEBUG"