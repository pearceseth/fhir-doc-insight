"""LLM configuration settings."""

from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    """Configuration for LLM/Ollama settings."""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout: int = 120  # Local models can be slow
    ollama_temperature: float = 0.1  # Low temperature for consistent analytical responses
    ollama_max_tokens: int = 2048

    class Config:
        env_file = ".env"
        env_prefix = ""


llm_config = LLMConfig()
