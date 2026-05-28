from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    provider: Literal["ollama", "openai", "anthropic", "groq", "gemini"] = "ollama"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-20241022"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Google Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Negotiation
    max_rounds: int = 10
    buyer_company: str = "AcmeCorp Manufacturing"
    seller_company: str = "GlobalSupplyCo"
    buyer_location: str = "Barcelona, Spain"
    seller_location: str = "Düsseldorf, Germany"

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    return Settings()
