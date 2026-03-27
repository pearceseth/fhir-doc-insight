"""Direct Ollama API client wrapper."""

import logging
from typing import AsyncGenerator

import httpx

from .config import llm_config

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Async client for Ollama API.
    Provides streaming and non-streaming chat completions.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ):
        self.base_url = (base_url or llm_config.ollama_base_url).rstrip("/")
        self.model = model or llm_config.ollama_model
        self.timeout = timeout or llm_config.ollama_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def check_health(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags", timeout=10.0)
            if response.status_code != 200:
                logger.warning(f"Ollama returned status {response.status_code}")
                return False
            data = response.json()
            available_models = data.get("models", [])

            # Check for model match (with or without :latest tag)
            model_base = self.model.split(":")[0]
            for m in available_models:
                model_name = m.get("name", "")
                # Match "llama3" with "llama3:latest" or exact match
                if model_name == self.model or model_name == f"{self.model}:latest" or model_name.split(":")[0] == model_base:
                    return True

            logger.warning(f"Model '{self.model}' not found. Available: {[m.get('name') for m in available_models]}")
            return False
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate a completion (non-streaming)."""
        client = await self._get_client()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or llm_config.ollama_temperature,
                "num_predict": llm_config.ollama_max_tokens,
            },
        }
        if system:
            payload["system"] = system

        response = await client.post(
            f"{self.base_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        return response.json().get("response", "")

    async def chat(
        self,
        messages: list[dict],
        temperature: float | None = None,
    ) -> str:
        """Chat completion (non-streaming)."""
        client = await self._get_client()

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or llm_config.ollama_temperature,
                "num_predict": llm_config.ollama_max_tokens,
            },
        }

        response = await client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        """Chat completion with streaming."""
        client = await self._get_client()

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature or llm_config.ollama_temperature,
                "num_predict": llm_config.ollama_max_tokens,
            },
        }

        async with client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if data.get("done"):
                        break


# Singleton instance
_ollama_client: OllamaClient | None = None


def get_ollama_client() -> OllamaClient:
    """Get or create the singleton Ollama client."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
