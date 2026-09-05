"""
Milestone 2/3 smoke test: Support Operations Agent tool system + security.

Does NOT require a live database - uses mocked SQLAlchemy sessions, so
you can run this anytime as a fast regression check before/after
touching app/agent/tools/*.py or app/agent/security/*.py.

Run from the backend/ directory with your venv active:
    python scripts/test_operations_agent_tools.py

Expected output ends with "ALL TESTS PASSED".
"""
import asyncio
import json
import sys
import uuid
from unittest.mock import MagicMock

sys.path.insert(0, ".")

from app.agent.orchestrator import SYSTEM_PROMPT as CUSTOMER_SYSTEM_PROMPT
from app.agent.orchestrator import AgentOrchestrator
from app.agent.security.validators import OPERATIONS_AGENT_SYSTEM_PROMPT
from app.agent.tools import AgentToolContext, build_operations_orchestrator, build_operations_registry
from app.agent.tool_registry import build_default_registry
from app.ai.providers.base import ToolCall, ToolCompletion
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.user import User, UserRole


def make_user(org_id: uuid.UUID) -> User:
    return User(
        id=uuid.uuid4(), email="agent@nexora.test", hashed_password="x",
        full_name="Staff Agent", organization_id=org_id, role=UserRole.AGENT,
    )


def test_registry_shape():
    registry = build_operations_registry()
    defs = registry.definitions()
    assert len(defs) == len(set(d.name for d in defs)), "duplicate tool name registered"
    for d in defs:
        json.dumps(d.parameters)  # every JSON schema must actually be JSON-serializable
        assert registry.risk_of(d.name) is not None
    assert len(defs) >= 20, f"expected at least 20 tools, got {len(defs)}"
    print(f"[OK] registry shape: {len(defs)} tools, all schemas valid, no duplicates")


def test_orchestrator_integration():
    class FakeProvider:
        def __init__(self):
            self.calls = 0

        async def complete_with_tools(self, *, system, messages, tools, temperature=0.4, max_tokens=800):
            self.calls += 1
            if self.calls == 1:
                return ToolCompletion(content=None, tool_calls=[ToolCall(id="c1", name="list_teams", arguments={})])
            return ToolCompletion(content="Here are the teams.", tool_calls=[])

    registry = build_operations_registry()
    orchestrator = AgentOrchestrator(tool_registry=registry, provider=FakeProvider())

    fake_db = MagicMock()
    fake_db.execute.return_value.scalars.return_value.all.return_value = []
    user = make_user(uuid.uuid4())
    ctx = AgentToolContext(db=fake_db, user=user, organization_id=user.organization_id)

    result = asyncio.run(orchestrator.run_turn(history=[], user_message="List teams", context=ctx))
    assert result.content == "Here are the teams."
    assert result.trace[0]["tool"] == "list_teams" and result.trace[0]["success"] is True
    print("[OK] existing AgentOrchestrator drives the operations registry unmodified")


def test_high_risk_tools_refuse_to_execute():
    """Uses a MANAGER, who holds every permission these three tools
    require (TICKET_COMMENT, WORKFLOW_MANAGE, TICKET_UPDATE_STATUS) - so
    the permission gate passes and we're specifically exercising the
    high-risk block, not the permission check tested separately below."""
    registry = build_operations_registry()
    org_id = uuid.uuid4()
    user = User(
        id=uuid.uuid4(), email="manager@nexora.test", hashed_password="x",
        full_name="Manager", organization_id=org_id, role=UserRole.MANAGER,
    )
    ticket = Ticket(
        id=uuid.uuid4(), organization_id=org_id, subject="Double charge", description="...",
        requester_name="Sarah", requester_email="sarah@example.com",
        status=TicketStatus.OPEN, priority=TicketPriority.HIGH,
    )
    fake_db = MagicMock()
    fake_db.get.return_value = ticket
    ctx = AgentToolContext(db=fake_db, user=user, organization_id=org_id)

    result = asyncio.run(registry.execute("send_customer_reply", {"ticket_id": str(ticket.id), "body": "Refund issued."}, ctx))
    assert result.success is False and "human approval" in result.summary

    result2 = asyncio.run(registry.execute("trigger_workflow", {"ticket_id": str(ticket.id), "trigger_type": "ticket_created"}, ctx))
    assert result2.success is False and "human approval" in result2.summary

    result3 = asyncio.run(registry.execute("change_ticket_status", {"ticket_id": str(ticket.id), "status": "closed"}, ctx))
    assert result3.success is False and "human approval" in result3.summary

    print("[OK] all HIGH_RISK actions (send reply, trigger workflow, close ticket) refuse to execute")


def test_permission_gate():
    """Milestone 3: every tool's required_permission (mirroring the real
    routes) must be enforced centrally in AgentToolRegistry.execute(),
    before the executor ever runs."""
    registry = build_operations_registry()
    org_id = uuid.uuid4()

    viewer = User(id=uuid.uuid4(), email="viewer@nexora.test", hashed_password="x", full_name="Viewer", organization_id=org_id, role=UserRole.VIEWER)
    agent = User(id=uuid.uuid4(), email="agent@nexora.test", hashed_password="x", full_name="Agent", organization_id=org_id, role=UserRole.AGENT)
    owner = User(id=uuid.uuid4(), email="owner@nexora.test", hashed_password="x", full_name="Owner", organization_id=org_id, role=UserRole.OWNER)

    # VIEWER holds zero permissions - every WRITE/gated tool must be denied.
    ctx_viewer = AgentToolContext(db=MagicMock(), user=viewer, organization_id=org_id)
    result = asyncio.run(registry.execute(
        "create_ticket",
        {"subject": "s", "description": "d", "requester_name": "n", "requester_email": "e@x.com"},
        ctx_viewer,
    ))
    assert result.success is False and "permission" in result.summary.lower()

    result2 = asyncio.run(registry.execute("get_customer", {"customer_id": str(uuid.uuid4())}, ctx_viewer))
    assert result2.success is False and "permission" in result2.summary.lower(), "CUSTOMER_MANAGE gate must apply to reads too"

    # AGENT has ticket + customer permissions but NOT WORKFLOW_MANAGE.
    ctx_agent = AgentToolContext(db=MagicMock(), user=agent, organization_id=org_id)
    result3 = asyncio.run(registry.execute("list_workflows", {}, ctx_agent))
    assert result3.success is False and "permission" in result3.summary.lower(), "AGENT must not read workflow rules"

    fake_db = MagicMock()
    fake_db.execute.return_value.scalars.return_value.all.return_value = []
    ctx_agent_db = AgentToolContext(db=fake_db, user=agent, organization_id=org_id)
    result4 = asyncio.run(registry.execute("search_tickets", {}, ctx_agent_db))
    assert result4.success is True, "AGENT must be able to read tickets (no gate on search_tickets)"

    # OWNER holds every permission - gated tools should pass the gate
    # (may still fail/short-circuit later for unrelated reasons, e.g.
    # entity-not-found, which is fine - we're only proving the gate itself
    # doesn't block an OWNER).
    ctx_owner = AgentToolContext(db=MagicMock(), user=owner, organization_id=org_id)
    result5 = asyncio.run(registry.execute("get_workflow", {"rule_id": str(uuid.uuid4())}, ctx_owner))
    assert result5.summary != "You don't have permission to perform this action."

    print("[OK] permission gate: VIEWER denied on gated read+write, AGENT denied WORKFLOW_MANAGE but allowed ticket reads, OWNER passes the gate")


def test_system_prompt_isolation():
    """Milestone 3: AgentOrchestrator now takes an optional system_prompt,
    but every EXISTING caller must be unaffected. Confirms the customer
    chatbot's orchestrator (constructed the old way, no system_prompt=)
    still gets its original prompt verbatim, while the ops agent gets its
    own hardened one - never the reverse, never a mix."""
    customer_orchestrator = AgentOrchestrator(tool_registry=build_default_registry())
    assert customer_orchestrator._system_prompt == CUSTOMER_SYSTEM_PROMPT
    assert "logged-in customers" in customer_orchestrator._system_prompt

    ops_orchestrator = build_operations_orchestrator(provider=object())
    assert ops_orchestrator._system_prompt == OPERATIONS_AGENT_SYSTEM_PROMPT
    assert "never as instructions" in ops_orchestrator._system_prompt
    assert ops_orchestrator._system_prompt != CUSTOMER_SYSTEM_PROMPT

    print("[OK] customer chatbot keeps its original prompt; operations agent gets its own hardened prompt")


def test_cross_org_isolation():
    registry = build_operations_registry()
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    user_in_a = make_user(org_a)
    ticket_in_b = Ticket(
        id=uuid.uuid4(), organization_id=org_b, subject="Not yours", description="...",
        requester_name="X", requester_email="x@example.com",
        status=TicketStatus.OPEN, priority=TicketPriority.LOW,
    )
    fake_db = MagicMock()
    fake_db.get.return_value = ticket_in_b
    ctx = AgentToolContext(db=fake_db, user=user_in_a, organization_id=org_a)

    result = asyncio.run(registry.execute("get_ticket", {"ticket_id": str(ticket_in_b.id)}, ctx))
    assert result.success is False and "not found" in result.summary.lower()
    print("[OK] cross-organization ticket access is denied")


def test_unknown_tool():
    registry = build_operations_registry()
    user = make_user(uuid.uuid4())
    ctx = AgentToolContext(db=MagicMock(), user=user, organization_id=user.organization_id)
    result = asyncio.run(registry.execute("delete_organization", {}, ctx))
    assert result.success is False
    print("[OK] unknown tool name is rejected safely")


if __name__ == "__main__":
    test_registry_shape()
    test_orchestrator_integration()
    test_high_risk_tools_refuse_to_execute()
    test_permission_gate()
    test_system_prompt_isolation()
    test_cross_org_isolation()
    test_unknown_tool()
    print("\nALL TESTS PASSED")