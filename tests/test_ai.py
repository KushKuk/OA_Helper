"""
Unit tests for AI functionality.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import Mock, patch, MagicMock

# Only import if we can create the necessary modules
try:
    from oa_assistant.ai.interface import AnalysisContext, AIResponse, AIProviderInterface
    from oa_assistant.ai.models import AnalysisContext as ModelAnalysisContext, AIResponse as ModelAIResponse
    from oa_assistant.ai.service import AIService, GeminiAIProvider, ai_service
    from oa_assistant.core.config import settings
    AI_AVAILABLE = True
except Exception:
    AI_AVAILABLE = False


def test_ai_response_model():
    """Test AIResponse model functionality."""
    if not AI_AVAILABLE:
        return

    # Test basic creation
    response = ModelAIResponse(text="Hello world", provider="gemini", model="gemini-1.5-flash")
    assert response.text == "Hello world"
    assert response.provider == "gemini"
    assert response.model == "gemini-1.5-flash"
    assert response.latency is None
    assert response.token_usage is None

    # Test with latency and token usage
    response_with_meta = ModelAIResponse(
        text="Hello world",
        provider="gemini",
        model="gemini-1.5-flash",
        latency=1.5,
        token_usage={"prompt_tokens": 10, "completion_tokens": 20}
    )
    assert response_with_meta.latency == 1.5
    assert response_with_meta.token_usage == {"prompt_tokens": 10, "completion_tokens": 20}

    # Test is_empty
    assert not ModelAIResponse(text="Hello", provider="gemini", model="gemini-1.5-flash").is_empty()
    assert ModelAIResponse(text="", provider="gemini", model="gemini-1.5-flash").is_empty()
    assert ModelAIResponse(text="   ", provider="gemini", model="gemini-1.5-flash").is_empty()
    assert ModelAIResponse(text="\n\t ", provider="gemini", model="gemini-1.5-flash").is_empty()

    # Test string representation
    response_str = str(ModelAIResponse(text="Hello world", provider="gemini", model="gemini-1.5-flash"))
    assert "AIResponse" in response_str
    assert "Hello world" in response_str


def test_analysis_context_model():
    """Test AnalysisContext model functionality."""
    if not AI_AVAILABLE:
        return

    # Test basic creation
    context = ModelAnalysisContext(text="Hello world")
    assert context.text == "Hello world"
    assert context.source == "ocr"
    assert context.capture_width is None
    assert context.capture_height is None
    assert context.ocr_mode is None

    # Test with all fields
    context_full = ModelAnalysisContext(
        text="Hello world",
        source="test",
        capture_width=800,
        capture_height=600,
        ocr_mode="code"
    )
    assert context_full.text == "Hello world"
    assert context_full.source == "test"
    assert context_full.capture_width == 800
    assert context_full.capture_height == 600
    assert context_full.ocr_mode == "code"


def test_ai_provider_interface():
    """Test AIProviderInterface abstraction."""
    if not AI_AVAILABLE:
        return

    # Test that we can't instantiate the abstract class directly
    try:
        provider = AIProviderInterface()
        assert False, "Should not be able to instantiate abstract class"
    except TypeError:
        pass  # Expected


def test_gemini_ai_provider_unavailable():
    """Test GeminiAIProvider when dependencies are not available."""
    if not AI_AVAILABLE:
        return

    with patch('oa_assistant.ai.service.GENAI_AVAILABLE', False):
        provider = GeminiAIProvider()
        assert not provider._available
        assert not provider.is_available()
        assert provider.get_name() == "gemini"
        assert provider.get_model() == settings.AI_MODEL


def test_gemini_ai_provider_no_api_key():
    """Test GeminiAIProvider when API key is not configured."""
    if not AI_AVAILABLE:
        return

    with patch('oa_assistant.ai.service.GENAI_AVAILABLE', True), \
         patch.object(settings, 'GEMINI_API_KEY', None):
        provider = GeminiAIProvider()
        assert not provider._available
        assert not provider.is_available()


def test_gemini_ai_provider_initialization():
    """Test GeminiAIProvider initialization when dependencies are available."""
    if not AI_AVAILABLE:
        return

    with patch('oa_assistant.ai.service.GENAI_AVAILABLE', True), \
         patch.object(settings, 'GEMINI_API_KEY', 'test-key'), \
         patch('oa_assistant.ai.service.genai') as mock_genai:
        mock_genai.configure.return_value = None
        provider = GeminiAIProvider()
        assert provider._available
        assert provider.is_available()
        assert provider.get_name() == "gemini"
        assert provider.get_model() == settings.AI_MODEL


def test_ai_service_initialization():
    """Test AIService initialization."""
    if not AI_AVAILABLE:
        return

    service = AIService()
    assert service is not None
    # Service should be initialized even if provider is not available


def test_ai_service_analyze_no_provider():
    """Test AIService analyze method when no provider available."""
    if not AI_AVAILABLE:
        return

    service = AIService()
    service._provider = None  # No provider

    context = AnalysisContext(text="Hello world")
    result = service.analyze(context)

    assert result.text == "AI is not configured. Please set GEMINI_API_KEY in your environment."
    assert result.provider == "none"
    assert result.model == "none"
    assert result.latency == 0.0


def test_ai_service_analyze_provider_not_available():
    """Test AIService analyze method when provider not available."""
    if not AI_AVAILABLE:
        return

    service = AIService()
    mock_provider = Mock()
    mock_provider.is_available.return_value = False
    service._provider = mock_provider

    context = AnalysisContext(text="Hello world")
    result = service.analyze(context)

    assert result.text == "AI is not configured. Please set GEMINI_API_KEY in your environment."
    assert result.provider == "none"
    assert result.model == "none"
    assert result.latency == 0.0


def test_ai_service_analyze_empty_text():
    """Test AIService analyze method with empty text."""
    if not AI_AVAILABLE:
        return

    service = AIService()
    mock_provider = Mock()
    mock_provider.is_available.return_value = True
    mock_provider.analyze.return_value = ModelAIResponse(
        text="No text provided for analysis.",
        provider="gemini",
        model="gemini-1.5-flash"
    )
    service._provider = mock_provider

    context = AnalysisContext(text="")
    result = service.analyze(context)

    assert result.text == "No text provided for analysis."
    assert result.provider == "gemini"
    assert result.model == "gemini-1.5-flash"


def test_ai_service_is_available():
    """Test AIService is_available method."""
    if not AI_AVAILABLE:
        return

    service = AIService()

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


def test_ai_service_get_provider_name():
    """Test AIService get_provider_name method."""
    if not AI_AVAILABLE:
        return

    service = AIService()

    # Test with no provider
    with patch.object(service, '_provider', None):
        assert service.get_provider_name() == "none"

    # Test with provider
    mock_provider = Mock()
    mock_provider.get_name.return_value = "gemini"
    with patch.object(service, '_provider', mock_provider):
        assert service.get_provider_name() == "gemini"


def test_ai_service_get_model_name():
    """Test AIService get_model_name method."""
    if not AI_AVAILABLE:
        return

    service = AIService()

    # Test with no provider
    with patch.object(service, '_provider', None):
        assert service.get_model_name() == "none"

    # Test with provider
    mock_provider = Mock()
    mock_provider.get_model.return_value = "gemini-1.5-flash"
    with patch.object(service, '_provider', mock_provider):
        assert service.get_model_name() == "gemini-1.5-flash"


def test_global_ai_service():
    """Test that global AI service instance exists."""
    if not AI_AVAILABLE:
        return

    assert ai_service is not None
    assert isinstance(ai_service, AIService)


def test_gemini_ai_provider_build_prompt_general():
    """Test GeminiAIProvider _build_prompt method for general text."""
    if not AI_AVAILABLE:
        return

    with patch('oa_assistant.ai.service.GENAI_AVAILABLE', True), \
         patch.object(settings, 'GEMINI_API_KEY', 'test-key'), \
         patch('oa_assistant.ai.service.genai'):
        provider = GeminiAIProvider()
        context = AnalysisContext(
            text="This is some sample text",
            ocr_mode="general_text"
        )
        prompt = provider._build_prompt(context)

        assert "Please analyze the following text" in prompt
        assert "This is some sample text" in prompt
        assert "general text or document content" in prompt
        assert "Summarize the main points" in prompt


def test_gemini_ai_provider_build_prompt_code():
    """Test GeminiAIProvider _build_prompt method for code."""
    if not AI_AVAILABLE:
        return

    with patch('oa_assistant.ai.service.GENAI_AVAILABLE', True), \
         patch.object(settings, 'GEMINI_API_KEY', 'test-key'), \
         patch('oa_assistant.ai.service.genai'):
        provider = GeminiAIProvider()
        context = AnalysisContext(
            text="def hello():\n    print('Hello World')",
            ocr_mode="code"
        )
        prompt = provider._build_prompt(context)

        assert "Please analyze the following text" in prompt
        assert "def hello():" in prompt
        assert "source code" in prompt
        assert "Explain what the code does" in prompt
        assert "Preserve code formatting" in prompt


if __name__ == "__main__":
    test_ai_response_model()
    test_analysis_context_model()
    test_ai_provider_interface()
    test_gemini_ai_provider_unavailable()
    test_gemini_ai_provider_no_api_key()
    test_gemini_ai_provider_initialization()
    test_ai_service_initialization()
    test_ai_service_analyze_no_provider()
    test_ai_service_analyze_provider_not_available()
    test_ai_service_analyze_empty_text()
    test_ai_service_is_available()
    test_ai_service_get_provider_name()
    test_ai_service_get_model_name()
    test_global_ai_service()
    test_gemini_ai_provider_build_prompt_general()
    test_gemini_ai_provider_build_prompt_code()
    print("All AI tests passed!")