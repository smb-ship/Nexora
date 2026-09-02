from google import genai
from google.genai import types

from app.ai.providers.base import (
    AIProvider,
    ToolCall,
    ToolCompletion,
    ToolDefinition,
    new_tool_call_id,
)
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

    async def complete_with_tools(
        self,
        *,
        system: str,
        messages: list[dict],
        tools: list[ToolDefinition],
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> ToolCompletion:
        contents = [self._to_gemini_content(m) for m in messages]

                gemini_tools = (
            [
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=t.name,
                            description=t.description,
                            parameters=t.parameters,
                        )
                        for t in tools
                    ]
                )
            ]
            if tools
            else []
        )

                config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=max_tokens,
            tools=gemini_tools or None,
            # Disable "thinking" tokens - see note in complete() above.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )

        candidate = response.candidates[0]
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for part in candidate.content.parts:
            if part.function_call:
                tool_calls.append(
                    ToolCall(
                        id=new_tool_call_id(),
                        name=part.function_call.name,
                        arguments=dict(part.function_call.args or {}),
                    )
                )
            elif part.text:
                text_parts.append(part.text)

        return ToolCompletion(
            content="".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
        )

    @staticmethod
    def _to_gemini_content(m: dict) -> types.Content:
        role = m["role"]

        if role == "user":
            return types.Content(role="user", parts=[types.Part(text=m.get("content") or "")])

        if role == "tool":
            return types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=m["name"],
                            response={"result": m["content"]},
                        )
                    )
                ],
            )

        if role == "assistant":
            parts = []
            if m.get("content"):
                parts.append(types.Part(text=m["content"]))
            for tc in m.get("tool_calls", []):
                parts.append(
                    types.Part(function_call=types.FunctionCall(name=tc.name, args=tc.arguments))
                )
            return types.Content(role="model", parts=parts)

        raise ValueError(f"Unsupported message role for Gemini: {role}")