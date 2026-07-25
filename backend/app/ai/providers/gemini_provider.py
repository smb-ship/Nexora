from google import genai
from google.genai import types

from app.ai.providers.base import AIProvider
from app.core.config import settings


class GeminiProvider(AIProvider):
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.GEMINI_MODEL

    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.4,
        max_tokens: int = 800,
        json_mode: bool = False,
    ) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json" if json_mode else "text/plain",
            # Disable "thinking" tokens - these tasks are simple classification/
            # generation and thinking tokens were silently eating the entire
            # max_output_tokens budget on reasoning-enabled Flash models,
            # truncating visible output to a few characters.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=user,
            config=config,
        )

        text = response.text
        if not text:
            raise RuntimeError("AI provider returned an empty response")
        return text