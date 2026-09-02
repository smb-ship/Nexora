"""
Milestone 2 smoke test: confirms the configured AI provider can execute
a tool-calling round trip (model decides to call a tool, we return a
result, model gives a final answer).

Run from backend/ with: python scripts/test_tool_calling.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.providers.base import ToolDefinition
from app.ai.providers.factory import get_ai_provider


GET_TIME_TOOL = ToolDefinition(
    name="get_current_time",
    description="Returns the current server time. Call this if the user asks what time it is.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)


async def main():
    provider = get_ai_provider()
    messages = [{"role": "user", "content": "What time is it right now?"}]

    print("--- Turn 1: asking the model, expecting it to request the tool ---")
    result = await provider.complete_with_tools(
        system="You are a helpful assistant. Use tools when they help answer the question.",
        messages=messages,
        tools=[GET_TIME_TOOL],
    )
    print("content:", result.content)
    print("tool_calls:", result.tool_calls)

    if not result.wants_tool_call:
        print("\nFAIL: model answered directly instead of requesting the tool.")
        return

    tool_call = result.tool_calls[0]
    assert tool_call.name == "get_current_time"

    messages.append({"role": "assistant", "content": result.content, "tool_calls": result.tool_calls})
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": tool_call.name,
        "content": "14:32:00 UTC",
    })

    print("\n--- Turn 2: sending the tool result back, expecting a final answer ---")
    final = await provider.complete_with_tools(
        system="You are a helpful assistant. Use tools when they help answer the question.",
        messages=messages,
        tools=[GET_TIME_TOOL],
    )
    print("content:", final.content)
    print("tool_calls:", final.tool_calls)

    if final.content and "14:32" in final.content:
        print("\nPASS: full tool-calling round trip worked.")
    else:
        print("\nCHECK MANUALLY: got a final answer but couldn't auto-verify it mentions the time.")


if __name__ == "__main__":
    asyncio.run(main())