"""
AI result models and enums.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from PIL import Image


@dataclass
class AnalysisContext:
    """
    Context for AI analysis containing extracted text and metadata.
    """
    text: str
    source: str = "ocr"
    capture_width: Optional[int] = None
    capture_height: Optional[int] = None
    ocr_mode: Optional[str] = None


@dataclass
class ScreenContext:
    """
    Context for screen analysis containing screenshot, OCR text, and metadata.
    """
    screenshot: Image.Image
    ocr_text: str
    capture_width: int
    capture_height: int
    monitor_info: dict = None
    capture_mode: str = "current_monitor"

    def __post_init__(self):
        if self.monitor_info is None:
            self.monitor_info = {}


@dataclass
class AIResponse:
    """
    Result of an AI analysis operation.
    """
    text: str
    provider: str
    model: str
    latency: Optional[float] = None
    token_usage: Optional[Dict[str, Any]] = None

    def is_empty(self) -> bool:
        """
        Check if the AI response contains any text.

        Returns:
            bool: True if text is empty or only whitespace
        """
        return not self.text or self.text.strip() == ""