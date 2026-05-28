from langchain_core.language_models import BaseChatModel

from config import get_settings


def create_llm(temperature: float = 0.1) -> BaseChatModel:
    """Return a chat model for the configured provider."""
    settings = get_settings()

    match settings.provider:
        case "ollama":
            from langchain_ollama import ChatOllama

            return ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=temperature,
            )
        case "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=temperature,
            )
        case "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                api_key=settings.anthropic_api_key,
                model=settings.anthropic_model,
                temperature=temperature,
            )
        case "groq":
            from langchain_groq import ChatGroq

            return ChatGroq(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                temperature=temperature,
            )
        case "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                google_api_key=settings.google_api_key,
                model=settings.gemini_model,
                temperature=temperature,
            )
        case _:
            raise ValueError(f"Unsupported provider: {settings.provider!r}")
