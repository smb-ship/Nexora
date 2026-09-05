from app.agent.orchestrator import AgentOrchestrator
from app.agent.security.validators import OPERATIONS_AGENT_SYSTEM_PROMPT
from app.agent.tools import communications, customers, knowledge, teams, tickets, workflows
from app.agent.tools.base import AgentToolContext, AgentToolRegistry

__all__ = ["AgentToolContext", "AgentToolRegistry", "build_operations_registry", "build_operations_orchestrator"]


def build_operations_registry() -> AgentToolRegistry:
    """Assembles every tool available to the staff-facing Support
    Operations Agent. Kept completely separate from
    app.agent.tool_registry.build_default_registry(), which backs the
    existing customer chatbot - the two agents never share a registry
    or a context type."""
    registry = AgentToolRegistry()
    tickets.register(registry)
    customers.register(registry)
    knowledge.register(registry)
    communications.register(registry)
    workflows.register(registry)
    teams.register(registry)
    return registry


def build_operations_orchestrator(provider=None) -> AgentOrchestrator:
    """Single entry point Milestone 4's routes should use: the existing
    AgentOrchestrator, wired to the operations registry and its own
    (non-customer-facing) system prompt."""
    return AgentOrchestrator(
        tool_registry=build_operations_registry(),
        provider=provider,
        system_prompt=OPERATIONS_AGENT_SYSTEM_PROMPT,
    )