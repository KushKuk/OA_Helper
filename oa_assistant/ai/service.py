"""
AI service for orchestrating AI operations.
"""
import time
import logging
from typing import Optional
from dataclasses import asdict

from oa_assistant.core.config import settings
from oa_assistant.core.logging import logger
from oa_assistant.ai.interface import AIProviderInterface, AnalysisContext, AIResponse

# Try to import google.generativeai, but handle gracefully if not available
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

# Try to import requests for Nemotron API, but handle gracefully if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


class GeminiAIProvider(AIProviderInterface):
    """
    Gemini AI provider using Google's Generative AI SDK.
    """

    def __init__(self):
        """Initialize the Gemini AI provider."""
        self._available = False
        self._model_name = settings.AI_MODEL
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Gemini AI is available and configured."""
        if not GENAI_AVAILABLE:
            logger.warning("google-generativeai package not installed")
            self._available = False
            return

        # Get API key from settings
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY not configured")
            self._available = False
            return

        # Configure the Gemini API
        try:
            genai.configure(api_key=api_key)
            # Test if the model is available by trying to get model info
            # Note: We don't actually call the API here to avoid using quota in tests
            self._available = True
            logger.info(f"Gemini AI provider is available with model: {self._model_name}")
        except Exception as e:
            logger.error(f"Gemini AI not available: {e}")
            self._available = False

    def analyze(self, context: AnalysisContext) -> AIResponse:
        """
        Perform AI analysis on the provided context using Gemini.

        Args:
            context: AnalysisContext containing text and metadata

        Returns:
            AIResponse: AI analysis result
        """
        start_time = time.time()

        if not self._available:
            return AIResponse(
                text="AI is not configured. Please set GEMINI_API_KEY in your environment.",
                provider="gemini",
                model=self._model_name,
                latency=time.time() - start_time
            )

        if not context.text or context.text.strip() == "":
            return AIResponse(
                text="No text provided for analysis.",
                provider="gemini",
                model=self._model_name,
                latency=time.time() - start_time
            )

        try:
            # Configure generation parameters for better text preservation
            generation_config = {
                "temperature": 0.2,  # Low temperature for more consistent responses
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            }

            # Create the model
            model = genai.GenerativeModel(
                model_name=self._model_name,
                generation_config=generation_config
            )

            # Build the prompt based on OCR mode
            prompt = self._build_prompt(context)

            # Generate response
            response = model.generate_content(prompt)

            # Extract text from response
            result_text = ""
            if hasattr(response, 'text'):
                result_text = response.text
            elif hasattr(response, 'parts'):
                result_text = ''.join([part.text for part in response.parts if hasattr(part, 'text')])
            else:
                result_text = str(response)

            # Calculate latency
            latency = time.time() - start_time

            logger.debug(f"Gemini AI analysis completed in {latency:.2f}s")

            return AIResponse(
                text=result_text.strip(),
                provider="gemini",
                model=self._model_name,
                latency=latency
            )

        except Exception as e:
            logger.error(f"Gemini AI analysis failed: {e}")
            return AIResponse(
                text=f"AI analysis failed: {str(e)}",
                provider="gemini",
                model=self._model_name,
                latency=time.time() - start_time
            )

    def _build_prompt(self, context: AnalysisContext) -> str:
        """
        Build an appropriate prompt for the AI based on context.

        Args:
            context: AnalysisContext containing text and metadata

        Returns:
            str: Prompt for the AI model
        """
        # Base instruction
        prompt = """Please analyze the following text extracted from a screen capture.
Provide a clear, concise explanation of what the content represents, identify important information,
and provide a useful response that would be helpful for understanding or working with this content.
"""

        # Add specific instructions based on OCR mode
        if context.ocr_mode == "code":
            prompt += """The text appears to be source code. Please:
- Explain what the code does
- Identify any key algorithms, functions, or concepts
- Preserve code formatting in your response when discussing specific code elements
- If there are errors or issues, point them out constructively
"""
        else:
            prompt += """The text appears to be general text or document content. Please:
- Summarize the main points
- Identify key information or data presented
- Explain any technical concepts or terminology
- Provide context that would help someone understand this content
"""

        prompt += f"\n\nExtracted text:\n---\n{context.text}\n---\n\nPlease provide your analysis:"

        return prompt

    def is_available(self) -> bool:
        """
        Check if the Gemini AI provider is available.

        Returns:
            bool: True if provider is available
        """
        return self._available

    def get_name(self) -> str:
        """
        Get the name of the AI provider.

        Returns:
            str: Provider name
        """
        return "gemini"

    def get_model(self) -> str:
        """
        Get the model name used by the AI provider.

        Returns:
            str: Model name
        """
        return self._model_name


class NemotronAIProvider(AIProviderInterface):
    """
    NVIDIA Nemotron AI provider using NVIDIA's API.
    """

    def __init__(self):
        """Initialize the Nemotron AI provider."""
        self._available = False
        self._model_name = getattr(settings, 'NEMOTRON_MODEL', 'nemotron-3-8b-chat')
        self._api_url = getattr(settings, 'NEMOTRON_API_URL', 'https://ai.api.nvidia.com/v1/nemotron')
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Nemotron AI is available and configured."""
        if not REQUESTS_AVAILABLE:
            logger.warning("requests package not installed")
            self._available = False
            return

        # Get API key from settings
        api_key = getattr(settings, 'NEMOTRON_API_KEY', None)
        if not api_key:
            logger.warning("NEMOTRON_API_KEY not configured")
            self._available = False
            return

        # Test if the API is available by checking if we can reach the endpoint
        # Note: We don't actually call the API here to avoid using quota in tests
        self._available = True
        logger.info(f"Nemotron AI provider is available with model: {self._model_name}")

    def analyze(self, context: AnalysisContext) -> AIResponse:
        """
        Perform AI analysis on the provided context using Nemotron.

        Args:
            context: AnalysisContext containing text and metadata

        Returns:
            AIResponse: AI analysis result
        """
        start_time = time.time()

        if not self._available:
            return AIResponse(
                text="AI is not configured. Please set NEMOTRON_API_KEY in your environment.",
                provider="nemotron",
                model=self._model_name,
                latency=time.time() - start_time
            )

        if not context.text or context.text.strip() == "":
            return AIResponse(
                text="No text provided for analysis.",
                provider="nemotron",
                model=self._model_name,
                latency=time.time() - start_time
            )

        try:
            # Build the prompt based on OCR mode
            prompt = self._build_prompt(context)

            # Prepare headers
            headers = {
                "Authorization": f"Bearer {getattr(settings, 'NEMOTRON_API_KEY')}",
                "Content-Type": "application/json"
            }

            # Prepare payload
            payload = {
                "model": self._model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1024,
                "temperature": 0.2,
                "top_p": 0.8,
                "stream": False
            }

            # Make API request
            response = requests.post(
                self._api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"Nemotron API request failed with status {response.status_code}: {response.text}")
                return AIResponse(
                    text=f"AI analysis failed: API returned status {response.status_code}",
                    provider="nemotron",
                    model=self._model_name,
                    latency=time.time() - start_time
                )

            # Parse response
            response_data = response.json()

            # Extract text from response
            result_text = ""
            if 'choices' in response_data and len(response_data['choices']) > 0:
                choice = response_data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    result_text = choice['message']['content']
                elif 'text' in choice:
                    result_text = choice['text']
            else:
                result_text = str(response_data)

            # Calculate latency
            latency = time.time() - start_time

            logger.debug(f"Nemotron AI analysis completed in {latency:.2f}s")

            return AIResponse(
                text=result_text.strip(),
                provider="nemotron",
                model=self._model_name,
                latency=latency
            )

        except Exception as e:
            logger.error(f"Nemotron AI analysis failed: {e}")
            return AIResponse(
                text=f"AI analysis failed: {str(e)}",
                provider="nemotron",
                model=self._model_name,
                latency=time.time() - start_time
            )

    def _build_prompt(self, context: AnalysisContext) -> str:
        """
        Build an appropriate prompt for the AI based on context.

        Args:
            context: AnalysisContext containing text and metadata

        Returns:
            str: Prompt for the AI model
        """
        # Base instruction
        prompt = """Please analyze the following text extracted from a screen capture.
Provide a clear, concise explanation of what the content represents, identify important information,
and provide a useful response that would be helpful for understanding or working with this content.
"""

        # Add specific instructions based on OCR mode
        if context.ocr_mode == "code":
            prompt += """The text appears to be source code. Please:
- Explain what the code does
- Identify any key algorithms, functions, or concepts
- Preserve code formatting in your response when discussing specific code elements
- If there are errors or issues, point them out constructively
"""
        else:
            prompt += """The text appears to be general text or document content. Please:
- Summarize the main points
- Identify key information or data presented
- Explain any technical concepts or terminology
- Provide context that would help someone understand this content
"""

        prompt += f"\n\nExtracted text:\n---\n{context.text}\n---\n\nPlease provide your analysis:"

        return prompt

    def is_available(self) -> bool:
        """
        Check if the Nemotron AI provider is available.

        Returns:
            bool: True if provider is available
        """
        return self._available

    def get_name(self) -> str:
        """
        Get the name of the AI provider.

        Returns:
            str: Provider name
        """
        return "nemotron"

    def get_model(self) -> str:
        """
        Get the model name used by the AI provider.

        Returns:
            str: Model name
        """
        return self._model_name


class AIService:
    """
    Service for performing AI analysis operations.
    """

    def __init__(self):
        """Initialize the AI service."""
        self._provider: Optional[AIProviderInterface] = None
        self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Initialize the AI provider based on configuration."""
        provider_name = settings.AI_PROVIDER.lower()

        if provider_name == "gemini":
            self._provider = GeminiAIProvider()
        elif provider_name == "nemotron":
            self._provider = NemotronAIProvider()
        else:
            logger.warning(f"Unknown AI provider: {provider_name}")
            self._provider = None

        if self._provider:
            logger.info(f"AI service initialized with provider: {self._provider.get_name()}")
        else:
            logger.warning("AI service initialized without a provider")

    def analyze(self, context: AnalysisContext) -> AIResponse:
        """
        Perform AI analysis on the provided context.

        Args:
            context: AnalysisContext containing text and metadata

        Returns:
            AIResponse: AI analysis result
        """
        if not self._provider or not self._provider.is_available():
            logger.warning("AI provider not available")
            provider_name = settings.AI_PROVIDER.lower()
            if provider_name == "gemini":
                error_text = "AI is not configured. Please set GEMINI_API_KEY in your environment."
            elif provider_name == "nemotron":
                error_text = "AI is not configured. Please set NEMOTRON_API_KEY in your environment."
            else:
                error_text = "AI is not configured. Please check your AI_PROVIDER setting."

            return AIResponse(
                text=error_text,
                provider="none",
                model="none",
                latency=0.0
            )

        return self._provider.analyze(context)

    def is_available(self) -> bool:
        """
        Check if AI service is available (has a working provider).

        Returns:
            bool: True if service is available
        """
        return self._provider is not None and self._provider.is_available()

    def get_provider_name(self) -> str:
        """
        Get the name of the current AI provider.

        Returns:
            str: Provider name or "none"
        """
        if self._provider:
            return self._provider.get_name()
        return "none"

    def get_model_name(self) -> str:
        """
        Get the model name used by the current AI provider.

        Returns:
            str: Model name or "none"
        """
        if self._provider:
            return self._provider.get_model()
        return "none"


# Global AI service instance
ai_service = AIService()