"""
NVIDIA Nemotron AI provider.
"""
import time
import logging
from typing import Optional, Dict, Any
from PIL import Image
import io
import base64

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from oa_assistant.core.config import settings
from oa_assistant.core.logging import logger
from oa_assistant.ai.interface import AIProviderInterface, AnalysisContext, AIResponse


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