"""
AI provider interface definition.
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


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
    token_usage: Optional[dict] = None


class AIProviderInterface(ABC):
    """
    Abstract interface for AI providers.
    """

    @abstractmethod
    def analyze(self, context: AnalysisContext) -> AIResponse:
        """
        Perform AI analysis on the provided context.

        Args:
            context: AnalysisContext containing text and metadata

        Returns:
            AIResponse: AI analysis result
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the AI provider is available and ready to use.

        Returns:
            bool: True if provider is available
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of the AI provider.

        Returns:
            str: Provider name
        """
        pass

    @abstractmethod
    def get_model(self) -> str:
        """
        Get the model name used by the AI provider.

        Returns:
            str: Model name
        """
        pass