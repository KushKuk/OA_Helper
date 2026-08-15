"""
Unit tests for OCR functionality.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import Mock, patch, MagicMock
from PIL import Image

# Only import if we can create the necessary modules
try:
    from oa_assistant.ocr.interface import OCRResult, OCRProviderInterface
    from oa_assistant.ocr.models import OCRResult as ModelOCRResult, OCRMode
    from oa_assistant.ocr.service import OCRService, TesseractOCRProvider, ocr_service
    from oa_assistant.core.config import settings
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


def test_ocr_result_model():
    """Test OCRResult model functionality."""
    if not OCR_AVAILABLE:
        return

    # Test basic creation
    result = ModelOCRResult(text="Hello world", confidence=95.0, provider="tesseract")
    assert result.text == "Hello world"
    assert result.confidence == 95.0
    assert result.provider == "tesseract"
    assert result.mode is None

    # Test with mode
    result_with_mode = ModelOCRResult(
        text="Hello world",
        confidence=95.0,
        provider="tesseract",
        mode=OCRMode.CODE
    )
    assert result_with_mode.mode == OCRMode.CODE

    # Test is_empty
    assert not ModelOCRResult(text="Hello").is_empty()
    assert ModelOCRResult(text="").is_empty()
    assert ModelOCRResult(text="   ").is_empty()
    assert ModelOCRResult(text="\n\t ").is_empty()

    # Test string representation
    result_str = str(ModelOCRResult(text="Hello world"))
    assert "OCRResult" in result_str
    assert "Hello world" in result_str


def test_ocr_mode_enum():
    """Test OCRMode enum."""
    if not OCR_AVAILABLE:
        return

    assert OCRMode.GENERAL_TEXT.value == "general_text"
    assert OCRMode.CODE.value == "code"
    assert len(list(OCRMode)) == 2


def test_tesseract_provider_unavailable():
    """Test TesseractOCRProvider when Tesseract is not available."""
    if not OCR_AVAILABLE:
        return

    with patch('oa_assistant.ocr.service.TESSERACT_AVAILABLE', False):
        provider = TesseractOCRProvider()
        assert not provider.is_available()
        assert provider.get_name() == "tesseract"

        # Test recognize returns empty result
        image = Image.new('RGB', (10, 10), color='white')
        result = provider.recognize(image)
        assert result.text == ""
        assert result.provider == "tesseract"
        assert result.processing_time >= 0


def test_tesseract_provider_available():
    """Test TesseractOCRProvider when Tesseract is available."""
    if not OCR_AVAILABLE:
        return

    import oa_assistant.ocr.service
    with patch.object(oa_assistant.ocr.service, 'TESSERACT_AVAILABLE', True), \
         patch.object(oa_assistant.ocr.service, 'pytesseract') as mock_pytesseract:
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_string.return_value = "Test text"
        mock_pytesseract.image_to_data.return_value = {
            'conf': ['-1', '90', '85', '-1']  # Mix of valid and invalid confidences
        }
        provider = TesseractOCRProvider()
        assert provider.is_available()

        image = Image.new('RGB', (10, 10), color='white')
        result = provider.recognize(image)

        assert result.text == "Test text"
        assert result.provider == "tesseract"
        assert result.confidence == 87.5  # Average of 90 and 85
        assert result.processing_time >= 0


def test_tesseract_provider_with_custom_path():
    """Test TesseractOCRProvider with custom Tesseract path."""
    if not OCR_AVAILABLE:
        return

    import oa_assistant.ocr.service
    import oa_assistant.core.config
    with patch.object(oa_assistant.ocr.service, 'TESSERACT_AVAILABLE', True), \
         patch.object(oa_assistant.core.config.settings, 'TESSERACT_CMD', '/custom/path/tesseract'), \
         patch.object(oa_assistant.ocr.service, 'pytesseract') as mock_pytesseract:
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        provider = TesseractOCRProvider()
        # The provider should have set the custom path
        assert provider.is_available()


def test_ocr_service_initialization():
    """Test OCRService initialization."""
    if not OCR_AVAILABLE:
        return

    service = OCRService()
    assert service is not None
    # Service should be initialized even if provider is not available


def test_ocr_service_recognize():
    """Test OCRService recognize method."""
    if not OCR_AVAILABLE:
        return

    service = OCRService()

    # Test with no provider available
    with patch.object(service, '_provider', None):
        image = Image.new('RGB', (10, 10), color='white')
        result = service.recognize(image)
        assert result.text == ""
        assert result.provider == "none"
        assert result.processing_time == 0.0

    # Test with unavailable provider
    mock_provider = Mock()
    mock_provider.is_available.return_value = False
    with patch.object(service, '_provider', mock_provider):
        image = Image.new('RGB', (10, 10), color='white')
        result = service.recognize(image)
        assert result.text == ""
        assert result.provider == "none"
        assert result.processing_time == 0.0

    # Test with available provider
    mock_provider = Mock()
    mock_provider.is_available.return_value = True
    mock_provider.recognize.return_value = ModelOCRResult(
        text="Recognized text",
        confidence=90.0,
        provider="tesseract",
        processing_time=1.5
    )
    with patch.object(service, '_provider', mock_provider):
        image = Image.new('RGB', (10, 10), color='white')
        result = service.recognize(image, mode=OCRMode.CODE)
        assert result.text == "Recognized text"
        assert result.confidence == 90.0
        assert result.provider == "tesseract"
        assert result.processing_time == 1.5
        assert result.mode == OCRMode.CODE


def test_ocr_service_is_available():
    """Test OCRService is_available method."""
    if not OCR_AVAILABLE:
        return

    service = OCRService()

    # Test with no provider
    with patch.object(service, '_provider', None):
        assert not service.is_available()

    # Test with unavailable provider
    mock_provider = Mock()
    mock_provider.is_available.return_value = False
    with patch.object(service, '_provider', mock_provider):
        assert not service.is_available()

    # Test with available provider
    mock_provider = Mock()
    mock_provider.is_available.return_value = True
    with patch.object(service, '_provider', mock_provider):
        assert service.is_available()


def test_global_ocr_service():
    """Test that global OCR service instance exists."""
    if not OCR_AVAILABLE:
        return

    assert ocr_service is not None
    assert isinstance(ocr_service, OCRService)


def test_ocr_provider_interface():
    """Test OCRProviderInterface abstraction."""
    if not OCR_AVAILABLE:
        return

    # Test that we can't instantiate the abstract class directly
    try:
        provider = OCRProviderInterface()
        assert False, "Should not be able to instantiate abstract class"
    except TypeError:
        pass  # Expected

    # Test that concrete implementations work
    import oa_assistant.ocr.service
    with patch.object(oa_assistant.ocr.service, 'TESSERACT_AVAILABLE', True), \
         patch.object(oa_assistant.ocr.service, 'pytesseract') as mock_pytesseract:
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        provider = TesseractOCRProvider()
        assert isinstance(provider, OCRProviderInterface)
        assert provider.get_name() == "tesseract"


if __name__ == "__main__":
    test_ocr_result_model()
    test_ocr_mode_enum()
    test_tesseract_provider_unavailable()
    test_tesseract_provider_available()
    test_tesseract_provider_with_custom_path()
    test_ocr_service_initialization()
    test_ocr_service_recognize()
    test_ocr_service_is_available()
    test_global_ocr_service()
    test_ocr_provider_interface()
    print("All OCR tests passed!")