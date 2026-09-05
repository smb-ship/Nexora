import logging
from dataclasses import dataclass, field

from app.agent.tool_registry import ToolContext, ToolRegistry
from app.ai.providers.factory import get_ai_provider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Nexora's AI customer support assistant. You talk directly to logged-in customers.

Rules:
- Never claim an action was completed unless a tool result actually confirms it.
- If you don't have a tool that can do what's being asked, say so plainly instead of pretending.
- If you're missing information you need (like a ticket number), ask the customer for it rather than guessing.
- Keep answers concise, friendly, and grounded only in what tools/knowledge actually returned.
"""

MAX_TOOL_ITERATIONS = 5


class AgentError(Exception):
    """Raised when the agent cannot complete a turn due to a provider failure."""


@dataclass
class AgentTurnResult:
    content: str
    trace: list[dict] = field(default_factory=list)


class AgentOrchestrator:
    def __init__(self, tool_registry: ToolRegistry, provider=None, system_prompt: str | None = None) -> None:
        self._tools = tool_registry
        self._provider = provider or get_ai_provider()
        # Defaults to the customer-chatbot prompt above so every existing
        # caller (app/api/routes/agent.py constructs this with only
        # tool_registry=) behaves identically to before. The Support
        # Operations Agent passes its own prompt from
        # app.agent.security.validators.OPERATIONS_AGENT_SYSTEM_PROMPT.
        self._system_prompt = system_prompt or SYSTEM_PROMPT

    async def run_turn(self, history: list[dict], user_message: str, context: ToolContext) -> AgentTurnResult:
        """
        Understand -> decide -> (tool loop) -> respond.

        `history` is the provider-agnostic message list for everything
        BEFORE this turn. Appends the new user message, then loops: ask the
        model, and if it requests tools, execute them and feed results back,
        until it gives a final answer or MAX_TOOL_ITERATIONS is hit.
        """
        messages = history + [{"role": "user", "content": user_message}]
        trace: list[dict] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            try:
                result = await self._provider.complete_with_tools(
                    system=self._system_prompt,
                    messages=messages,
                    tools=self._tools.definitions(),
                )
            except Exception as exc:
                logger.error("Agent provider call failed: %s", exc, exc_info=True)
                raise AgentError(f"AI provider request failed: {exc}") from exc

            if not result.wants_tool_call:
                return AgentTurnResult(content=result.content or "", trace=trace)

            messages.append(
                {"role": "assistant", "content": result.content, "tool_calls": result.tool_calls}
            )

            for call in result.tool_calls:
                tool_result = await self._tools.execute(call.name, call.arguments, context)
                trace.append(
                    {
                        "tool": call.name,
                        "arguments": call.arguments,
                        "success": tool_result.success,
                        "summary": tool_result.summary,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.name,
                        "content": tool_result.to_model_text(),
                    }
                )

        return AgentTurnResult(
            content=(
                "I wasn't able to finish that within the allowed number of steps. "
                "Could you rephrase or simplify your request?"
            ),
            trace=trace,
        )