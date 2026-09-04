from app.agent.tools import communications, customers, knowledge, teams, tickets, workflows
from app.agent.tools.base import AgentToolContext, AgentToolRegistry

__all__ = ["AgentToolContext", "AgentToolRegistry", "build_operations_registry"]


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