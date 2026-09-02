import json
import logging
import uuid
from dataclasses import dataclass
from typing import Awaitable, Callable

from sqlalchemy.orm import Session

from app.ai.providers.base import ToolDefinition
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class ToolContext:
    """Everything a tool execution function needs, scoped to the calling
    customer. Every tool MUST filter its own DB queries using these fields -
    never trust the model-supplied arguments for identity or ownership."""

    db: Session
    customer: User
    organization_id: uuid.UUID


@dataclass
class ToolResult:
    success: bool
    summary: str  # short human-readable line, used in the trace/logs
    data: dict | None = None

    def to_model_text(self) -> str:
        """What gets sent back to the LLM as this tool call's result."""
        payload = {"success": self.success, "summary": self.summary}
        if self.data is not None:
            payload["data"] = self.data
        return json.dumps(payload)


ToolFn = Callable[[dict, ToolContext], Awaitable[ToolResult]]


class ToolRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        self._executors: dict[str, ToolFn] = {}

    def register(self, definition: ToolDefinition, executor: ToolFn) -> None:
        if definition.name in self._definitions:
            raise ValueError(f"Tool '{definition.name}' is already registered")
        self._definitions[definition.name] = definition
        self._executors[definition.name] = executor

    def definitions(self) -> list[ToolDefinition]:
        return list(self._definitions.values())

    async def execute(self, name: str, arguments: dict, context: ToolContext) -> ToolResult:
        executor = self._executors.get(name)
        if executor is None:
            logger.warning("Model requested unknown tool '%s'", name)
            return ToolResult(success=False, summary=f"Tool '{name}' does not exist.")
        try:
            return await executor(arguments, context)
        except Exception as exc:
            logger.error("Tool '%s' raised an exception: %s", name, exc, exc_info=True)
            return ToolResult(success=False, summary=f"Tool '{name}' failed: {exc}")


def build_default_registry() -> ToolRegistry:
    """Assembles the registry with every tool available to the customer
    agent. Intentionally empty for Milestone 3 - this proves the
    orchestrator loop, memory, and routing work with zero tools before
    Milestone 4 registers real ones (ticket lookup, creation, etc.)."""
    registry = ToolRegistry()
    return registry