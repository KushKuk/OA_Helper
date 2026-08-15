"""
OCR result models and enums.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class OCRMode(Enum):
    """
    OCR processing modes.
    """
    GENERAL_TEXT = "general_text"
    CODE = "code"


@dataclass
class OCRResult:
    """
    Result of an OCR operation.
    """
    text: str
    confidence: Optional[float] = None
    provider: str = ""
    processing_time: Optional[float] = None
    mode: Optional[OCRMode] = None

    def is_empty(self) -> bool:
        """
        Check if the OCR result contains any text.

        Returns:
            bool: True if text is empty or only whitespace
        """
        return not self.text or self.text.strip() == ""

    def __str__(self) -> str:
        return f"OCRResult(text='{self.text[:50]}...', confidence={self.confidence}, provider='{self.provider}', mode={self.mode})"