"""LLM provider abstraction for chat completions."""
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Generator, List, Optional

import httpx

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
        images: Optional[List[str]] = None
    ) -> str:
        """Generate chat completion. Images are base64-encoded strings."""
        pass

    def chat_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
        images: Optional[List[str]] = None
    ) -> Generator[str, None, None]:
        """Stream chat completion. Override for streaming support."""
        yield self.chat(messages, temperature, max_tokens, images)


class GroqProvider(LLMProvider):
    """Groq API provider (free tier - Gemma 2 9B). Text-only, no multimodal."""

    def __init__(self):
        from groq import Groq
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        self.client = Groq(api_key=api_key)
        self.model = "gemma2-9b-it"

    def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
        images: Optional[List[str]] = None
    ) -> str:
        if images:
            logger.warning("Groq provider does not support images, ignoring attachments")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def chat_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
        images: Optional[List[str]] = None
    ) -> Generator[str, None, None]:
        """Stream chat completion from Groq."""
        if images:
            logger.warning("Groq provider does not support images, ignoring attachments")

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OllamaProvider(LLMProvider):
    """Ollama provider using /api/generate endpoint."""

    def __init__(self):
        self.base_url = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
        self.client = httpx.Client(timeout=120.0)
        self.model = os.environ.get('OLLAMA_MODEL', 'gemma3:4b')

    def _messages_to_prompt(self, messages: List[dict]) -> str:
        """Convert chat messages to single prompt for /api/generate."""
        parts = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            if role == 'system':
                parts.append(f"System: {content}")
            elif role == 'user':
                parts.append(f"User: {content}")
            elif role == 'assistant':
                parts.append(f"Assistant: {content}")
        parts.append("Assistant:")
        return "\n\n".join(parts)

    def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
        images: Optional[List[str]] = None
    ) -> str:
        if images:
            logger.warning("Ollama /api/generate does not support images, ignoring")

        prompt = self._messages_to_prompt(messages)
        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens}
            }
        )
        response.raise_for_status()
        return response.json()["response"]

    def chat_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 500,
        images: Optional[List[str]] = None
    ) -> Generator[str, None, None]:
        """Stream chat completion from Ollama."""
        if images:
            logger.warning("Ollama /api/generate does not support images, ignoring")

        prompt = self._messages_to_prompt(messages)

        with httpx.Client(timeout=120.0) as client:
            with client.stream(
                'POST',
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": temperature, "num_predict": max_tokens}
                }
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if 'response' in data:
                            yield data['response']


def get_llm_provider() -> LLMProvider:
    """Returns Ollama if configured, else Groq."""
    ollama_host = os.environ.get('OLLAMA_HOST')
    if ollama_host:
        logger.info(f"Using Ollama at {ollama_host}")
        return OllamaProvider()
    logger.info("Using Groq API")
    return GroqProvider()
