"""
Milestone 4 smoke test: persistent agent runs.

Does NOT require a live database - mocks the SQLAlchemy session and
verifies run_service's status transitions and action recording, plus
the full run_support_operations_agent flow with a fake AI provider.

Run from the backend/ directory with your venv active:
    python scripts/test_agent_runs.py

Expected output ends with "ALL TESTS PASSED".
"""
import asyncio
import sys
import uuid
from unittest.mock import MagicMock

sys.path.insert(0, ".")

from app.agent.runs import run_service
from app.agent.security.tool_permissions import ToolRisk
from app.agent.services.agent_service import run_support_operations_agent
from app.ai.providers.base import ToolCall, ToolCompletion
from app.models.agent_ops.run import AgentRun, AgentRunStatus
from app.models.user import User, UserRole


def make_user(org_id: uuid.UUID) -> User:
    return User(
        id=uuid.uuid4(), email="manager@nexora.test", hashed_password="x",
        full_name="Manager", organization_id=org_id, role=UserRole.MANAGER,
    )


def test_create_and_complete_run():
    fake_db = MagicMock()
    org_id, user_id = uuid.uuid4(), uuid.uuid4()

    run = run_service.create_run(fake_db, org_id, user_id, "support_operations", "Handle Sarah's billing issue")
    assert run.status == AgentRunStatus.RUNNING
    assert run.organization_id == org_id and run.user_id == user_id
    assert fake_db.add.called and fake_db.commit.called

    trace = [
        {"tool": "search_customers", "arguments": {"query": "sarah"}, "success": True, "summary": "Found 1 customer(s)."},
        {"tool": "get_customer_tickets", "arguments": {"customer_id": "..."}, "success": True, "summary": "Customer has 1 ticket(s)."},
    ]
    run_service.record_trace(fake_db, run, trace, risk_of=lambda name: ToolRisk.READ)
    assert fake_db.add.call_count >= 3  # 1 run + 2 actions

    completed = run_service.complete_run(fake_db, run, "Found the ticket and flagged it high priority.")
    assert completed.status == AgentRunStatus.COMPLETED
    assert completed.completed_at is not None
    print("[OK] create_run -> record_trace -> complete_run status lifecycle")


def test_fail_run():
    fake_db = MagicMock()
    run = run_service.create_run(fake_db, uuid.uuid4(), uuid.uuid4(), "support_operations", "Do something")
    failed = run_service.fail_run(fake_db, run, "AI provider timed out")
    assert failed.status == AgentRunStatus.FAILED
    assert failed.error == "AI provider timed out"
    assert failed.completed_at is not None
    print("[OK] fail_run sets status=FAILED with error and completed_at")


def test_get_and_list_scoped_to_org():
    fake_db = MagicMock()
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    run_in_b = AgentRun(id=uuid.uuid4(), organization_id=org_b, user_id=uuid.uuid4(), agent_name="support_operations", initial_request="x")

    fake_db.execute.return_value.scalar_one_or_none.return_value = run_in_b
    result = run_service.get_org_run(fake_db, run_in_b.id, org_a)
    assert result is None, "a run from another organization must never be returned"

    fake_db.execute.return_value.scalar_one_or_none.return_value = run_in_b
    result2 = run_service.get_org_run(fake_db, run_in_b.id, org_b)
    assert result2 is run_in_b
    print("[OK] get_org_run enforces organization scoping")


def test_full_agent_service_flow():
    """End-to-end: run_support_operations_agent creates a run, drives the
    real orchestrator against a fake provider that calls one tool, and
    persists the resulting trace - proving Milestones 2-4 compose."""
    class FakeProvider:
        def __init__(self):
            self.calls = 0

        async def complete_with_tools(self, *, system, messages, tools, temperature=0.4, max_tokens=800):
            self.calls += 1
            if self.calls == 1:
                return ToolCompletion(content=None, tool_calls=[ToolCall(id="c1", name="list_teams", arguments={})])
            return ToolCompletion(content="There are 2 teams.", tool_calls=[])

    fake_db = MagicMock()
    fake_db.execute.return_value.scalars.return_value.all.return_value = []
    user = make_user(uuid.uuid4())

    run = asyncio.run(run_support_operations_agent(fake_db, user, "How many teams do we have?", provider=FakeProvider()))

    assert run.status == AgentRunStatus.COMPLETED
    assert run.final_result == "There are 2 teams."
    assert run.initial_request == "How many teams do we have?"
    print("[OK] run_support_operations_agent: full orchestrator -> tool -> persistence flow completes")


def test_full_agent_service_flow_failure():
    """A provider that raises must land the run in FAILED, not raise
    out of run_support_operations_agent and lose the record."""
    class BrokenProvider:
        async def complete_with_tools(self, **kwargs):
            raise RuntimeError("upstream AI provider is down")

    fake_db = MagicMock()
    user = make_user(uuid.uuid4())

    run = asyncio.run(run_support_operations_agent(fake_db, user, "Anything", provider=BrokenProvider()))
    assert run.status == AgentRunStatus.FAILED
    assert "upstream AI provider is down" in run.error
    print("[OK] a raising provider still yields a persisted FAILED run, not an unhandled exception")


if __name__ == "__main__":
    test_create_and_complete_run()
    test_fail_run()
    test_get_and_list_scoped_to_org()
    test_full_agent_service_flow()
    test_full_agent_service_flow_failure()
    print("\nALL TESTS PASSED")