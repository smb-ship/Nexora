"""Tool abstraction for the staff-facing Support Operations Agent.

Deliberately separate from app/agent/tool_registry.py, which backs the
existing CUSTOMER-facing chat agent (that ToolContext is scoped to a
logged-in customer, and its registry is - by design - still empty).
Tools here run on behalf of an authenticated STAFF user (owner / admin /
manager / agent / viewer) and can read and mutate organization data, so
every tool executor MUST filter its own queries by
`context.organization_id` - exactly like the existing route handlers do -
and MUST NOT trust ids embedded in the model-supplied arguments without
an explicit ownership check first.

Reused, not duplicated:
- `ToolResult` from app.agent.tool_registry - a generic success/summary/
  data envelope with no customer-specific fields, so there's no reason
  to redefine it here.
- `ToolDefinition` / `ToolCall` / `ToolCompletion` from
  app.ai.providers.base - already provider-agnostic.
- `AgentOrchestrator` from app.agent.orchestrator, completely
  unmodified: its only contract with a `tool_registry` is
  `.definitions()` and `.execute(name, arguments, context)`, both of
  which `AgentToolRegistry` below implements with the same signatures.
  That means the same orchestrator loop (understand -> tool loop ->
  respond) drives both the customer chatbot and the operations agent -
  only the registry and context passed to it differ.
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Awaitable, Callable

from sqlalchemy.orm import Session

from app.agent.security.tool_permissions import ToolRisk
from app.agent.tool_registry import ToolResult
from app.ai.providers.base import ToolDefinition
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class AgentToolContext:
    """Everything a Support Operations Agent tool executor needs, scoped
    to the calling STAFF user (never a customer)."""

    db: Session
    user: User
    organization_id: uuid.UUID


AgentToolFn = Callable[[dict, AgentToolContext], Awaitable[ToolResult]]


@dataclass
class _RegisteredTool:
    definition: ToolDefinition
    risk: ToolRisk
    executor: AgentToolFn


class AgentToolRegistry:
    """Same shape as app.agent.tool_registry.ToolRegistry (definitions()
    / execute()) so AgentOrchestrator works with either one unmodified.
    Adds risk classification, which the customer registry has no need
    for since it has zero write tools registered."""

    def __init__(self) -> None:
        self._tools: dict[str, _RegisteredTool] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        risk: ToolRisk,
        executor: AgentToolFn,
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
        self._tools[name] = _RegisteredTool(
            definition=ToolDefinition(name=name, description=description, parameters=parameters),
            risk=risk,
            executor=executor,
        )

    def definitions(self) -> list[ToolDefinition]:
        return [t.definition for t in self._tools.values()]

    def risk_of(self, name: str) -> ToolRisk | None:
        tool = self._tools.get(name)
        return tool.risk if tool else None

    def names_by_risk(self, risk: ToolRisk) -> list[str]:
        return [name for name, t in self._tools.items() if t.risk == risk]

    async def execute(self, name: str, arguments: dict, context: AgentToolContext) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            logger.warning("Model requested unknown operations tool '%s'", name)
            return ToolResult(success=False, summary=f"Tool '{name}' does not exist.")
        try:
            return await tool.executor(arguments, context)
        except Exception as exc:
            logger.error("Operations tool '%s' raised an exception: %s", name, exc, exc_info=True)
            return ToolResult(success=False, summary=f"Tool '{name}' failed: {exc}")