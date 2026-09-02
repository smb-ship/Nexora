import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ToolDefinition:
    """Provider-agnostic description of a tool the model is allowed to call."""

    name: str
    description: str
    parameters: dict  # JSON Schema object describing the tool's arguments


@dataclass
class ToolCall:
    """A single tool invocation requested by the model."""

    id: str
    name: str
    arguments: dict


@dataclass
class ToolCompletion:
    """Result of one turn of a tool-enabled completion."""

    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)

    @property
    def wants_tool_call(self) -> bool:
        return bool(self.tool_calls)


class AIProvider(ABC):
    """Abstract interface all AI providers must implement."""

    @abstractmethod
    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.4,
        max_tokens: int = 800,
        json_mode: bool = False,
    ) -> str:
        """Return the raw text completion from the underlying model."""
        raise NotImplementedError

    @abstractmethod
    async def complete_with_tools(
        self,
        *,
        system: str,
        messages: list[dict],
        tools: list[ToolDefinition],
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> ToolCompletion:
        """
        Run one turn of a tool-calling conversation.

        `messages` is a provider-agnostic list of turns. Each entry is a dict:
          - {"role": "user", "content": str}
          - {"role": "assistant", "content": str | None, "tool_calls": list[ToolCall]}
          - {"role": "tool", "tool_call_id": str, "name": str, "content": str}

        The caller builds this list turn-by-turn (see app/agent/orchestrator.py
        in Milestone 3) and appends a "tool" role entry with the tool's result
        before calling this again.

        Returns a ToolCompletion. If `tool_calls` is non-empty, the model
        wants those tools executed before it gives a final answer — don't
        treat `content` as a final answer in that case.
        """
        raise NotImplementedError


def new_tool_call_id() -> str:
    """Generates a synthetic tool-call id for providers that don't supply one."""
    return uuid.uuid4().hex[:12]