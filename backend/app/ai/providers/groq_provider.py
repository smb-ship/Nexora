import json

from groq import AsyncGroq

from app.ai.providers.base import AIProvider, ToolCall, ToolCompletion, ToolDefinition
from app.core.config import settings


class GroqProvider(AIProvider):
    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self._model = settings.GROQ_MODEL

    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.4,
        max_tokens: int = 800,
        json_mode: bool = False,
    ) -> str:
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        text = response.choices[0].message.content
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
        groq_messages = [{"role": "system", "content": system}]
        for m in messages:
            groq_messages.append(self._to_groq_message(m))

        groq_tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

                kwargs = {}
        if groq_tools:
            kwargs["tools"] = groq_tools
            kwargs["tool_choice"] = "auto"

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=groq_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        message = response.choices[0].message
        tool_calls = [
            ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=json.loads(tc.function.arguments or "{}"),
            )
            for tc in (message.tool_calls or [])
        ]
        return ToolCompletion(content=message.content, tool_calls=tool_calls)

    @staticmethod
    def _to_groq_message(m: dict) -> dict:
        role = m["role"]

        if role == "tool":
            return {
                "role": "tool",
                "tool_call_id": m["tool_call_id"],
                "content": m["content"],
            }

        if role == "assistant" and m.get("tool_calls"):
            return {
                "role": "assistant",
                "content": m.get("content"),
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in m["tool_calls"]
                ],
            }

        return {"role": role, "content": m.get("content", "")}