"""
OCR service for orchestrating OCR operations.
"""
import time
from typing import Optional
from PIL import Image

from oa_assistant.core.config import settings
from oa_assistant.core.logging import logger
from oa_assistant.ocr.interface import OCRProviderInterface
from oa_assistant.ocr.models import OCRResult, OCRMode

# Try to import pytesseract, but handle gracefully if not available
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None


class TesseractOCRProvider(OCRProviderInterface):
    """
    Tesseract OCR provider using pytesseract.
    """

    def __init__(self):
        """Initialize the Tesseract OCR provider."""
        self._available = False
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Tesseract is available and configured."""
        if not TESSERACT_AVAILABLE:
            logger.warning("pytesseract package not installed")
            self._available = False
            return

        # Get Tesseract command path from settings
        tesseract_cmd = settings.TESSERACT_CMD
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            logger.info(f"Using Tesseract at: {tesseract_cmd}")
        else:
            logger.info("Using Tesseract from system PATH")

        # Test if Tesseract is available
        try:
            # This will raise an exception if Tesseract is not found
            pytesseract.get_tesseract_version()
            self._available = True
            logger.info("Tesseract OCR provider is available")
        except Exception as e:
            logger.error(f"Tesseract not available: {e}")
            self._available = False

    def recognize(self, image: Image.Image, lang: str = 'eng') -> OCRResult:
        """
        Perform OCR on an image using Tesseract.

        Args:
            image: PIL Image to process
            lang: Language code(s) for OCR (default: 'eng')

        Returns:
            OCRResult: Extracted text and metadata
        """
        start_time = time.time()

        if not self._available:
            return OCRResult(
                text="",
                provider="tesseract",
                processing_time=time.time() - start_time
            )

        try:
            # Configure Tesseract options for preserving text layout
            # We'll use --psm 3 (fully automatic page segmentation) but can adjust
            # For code mode, we might want different settings, but we'll handle that via config later
            custom_config = r'--oem 3 --psm 3'

            # Extract text
            text = pytesseract.image_to_string(image, lang=lang, config=custom_config)

            # Try to get confidence data
            try:
                # Get detailed data including confidence
                data = pytesseract.image_to_data(image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)
                # Calculate average confidence (excluding -1 entries)
                confidences = [int(conf) for conf in data['conf'] if int(conf) != -1]
                confidence = sum(confidences) / len(confidences) if confidences else None
            except Exception:
                confidence = None

            processing_time = time.time() - start_time

            logger.debug(f"OCR completed in {processing_time:.2f}s, confidence: {confidence}")

            return OCRResult(
                text=text,
                confidence=confidence,
                provider="tesseract",
                processing_time=processing_time
            )
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return OCRResult(
                text="",
                provider="tesseract",
                processing_time=time.time() - start_time
            )

    def is_available(self) -> bool:
        """
        Check if the Tesseract OCR provider is available.

        Returns:
            bool: True if provider is available
        """
        return self._available

    def get_name(self) -> str:
        """
        Get the name of the OCR provider.

        Returns:
            str: Provider name
        """
        return "tesseract"


class OCRService:
    """
    Service for performing OCR operations.
    """

    def __init__(self):
        """Initialize the OCR service."""
        self._provider: Optional[OCRProviderInterface] = None
        self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Initialize the OCR provider based on configuration."""
        provider_name = settings.OCR_PROVIDER.lower()

        if provider_name == "tesseract":
            self._provider = TesseractOCRProvider()
        else:
            logger.warning(f"Unknown OCR provider: {provider_name}")
            self._provider = None

        if self._provider:
            logger.info(f"OCR service initialized with provider: {self._provider.get_name()}")
        else:
            logger.warning("OCR service initialized without a provider")

    def recognize(self, image: Image.Image, lang: str = 'eng', mode: OCRMode = OCRMode.GENERAL_TEXT) -> OCRResult:
        """
        Perform OCR on an image.

        Args:
            image: PIL Image to process
            lang: Language code(s) for OCR (default: 'eng')
            mode: OCR mode (general_text or code)

        Returns:
            OCRResult: Extracted text and metadata
        """
        if not self._provider or not self._provider.is_available():
            logger.warning("OCR provider not available")
            return OCRResult(
                text="",
                provider="none",
                processing_time=0.0,
                mode=mode
            )

        # For now, we use the same recognition for both modes
        # In the future, we could adjust Tesseract config based on mode
        result = self._provider.recognize(image, lang)
        result.mode = mode
        return result

    def is_available(self) -> bool:
        """
        Check if OCR service is available (has a working provider).

        Returns:
            bool: True if service is available
        """
        return self._provider is not None and self._provider.is_available()

    def get_provider_name(self) -> str:
        """
        Get the name of the current OCR provider.

        Returns:
            str: Provider name or "none"
        """
        if self._provider:
            return self._provider.get_name()
        return "none"


# Global OCR service instance
ocr_service = OCRService()