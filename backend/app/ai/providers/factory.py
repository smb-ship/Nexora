from functools import lru_cache

from app.ai.providers.base import AIProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.groq_provider import GroqProvider
from app.core.config import settings


@lru_cache
def get_ai_provider() -> AIProvider:
    """Returns the configured AI provider instance. Swap providers via the AI_PROVIDER env var."""
    if settings.AI_PROVIDER == "groq":
        return GroqProvider()
    if settings.AI_PROVIDER == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unsupported AI_PROVIDER: {settings.AI_PROVIDER}")