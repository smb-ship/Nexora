"""
Milestone 2 smoke test: Support Operations Agent tool system.

Does NOT require a live database - uses mocked SQLAlchemy sessions, so
you can run this anytime as a fast regression check before/after
touching app/agent/tools/*.py.

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

from app.agent.orchestrator import AgentOrchestrator
from app.agent.tools import AgentToolContext, build_operations_registry
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
    registry = build_operations_registry()
    org_id = uuid.uuid4()
    user = make_user(org_id)
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
    test_cross_org_isolation()
    test_unknown_tool()
    print("\nALL TESTS PASSED")