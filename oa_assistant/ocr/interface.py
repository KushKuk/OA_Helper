"""
OCR provider interface definition.
"""
from abc import ABC, abstractmethod
from typing import Optional
from PIL import Image


class OCRResult:
    """
    Result of an OCR operation.
    """

    def __init__(self, text: str, confidence: Optional[float] = None,
                 provider: str = "", processing_time: Optional[float] = None):
        """
        Initialize OCR result.

        Args:
            text: Extracted text
            confidence: Confidence score (0-100) if available
            provider: Name of the OCR provider used
            processing_time: Time taken for OCR in seconds
        """
        self.text = text
        self.confidence = confidence
        self.provider = provider
        self.processing_time = processing_time

    def is_empty(self) -> bool:
        """
        Check if the OCR result contains any text.

        Returns:
            bool: True if text is empty or only whitespace
        """
        return not self.text or self.text.strip() == ""

    def __str__(self) -> str:
        return f"OCRResult(text='{self.text[:50]}...', confidence={self.confidence}, provider='{self.provider}')"


class OCRProviderInterface(ABC):
    """
    Abstract interface for OCR providers.
    """

    @abstractmethod
    def recognize(self, image: Image.Image, lang: str = 'eng') -> OCRResult:
        """
        Perform OCR on an image.

        Args:
            image: PIL Image to process
            lang: Language code(s) for OCR (default: 'eng')

        Returns:
            OCRResult: Extracted text and metadata
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the OCR provider is available and ready to use.

        Returns:
            bool: True if provider is available
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of the OCR provider.

        Returns:
            str: Provider name
        """
        pass