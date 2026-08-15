"""
AI result models and enums.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


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