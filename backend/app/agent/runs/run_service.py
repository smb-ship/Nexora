"""Persistence for agent runs. Deliberately dumb - no orchestration logic
lives here, only reading/writing AgentRun/AgentAction rows. The actual
"run the agent and persist what happened" flow is
app.agent.services.agent_service.run_support_operations_agent, which
calls these functions around the existing AgentOrchestrator.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.agent.security.tool_permissions import ToolRisk
from app.models.agent_ops.action import AgentAction
from app.models.agent_ops.run import AgentRun, AgentRunStatus


def create_run(db: Session, organization_id: uuid.UUID, user_id: uuid.UUID, agent_name: str, initial_request: str) -> AgentRun:
    run = AgentRun(
        organization_id=organization_id, user_id=user_id, agent_name=agent_name,
        initial_request=initial_request, status=AgentRunStatus.RUNNING,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def record_trace(db: Session, run: AgentRun, trace: list[dict], risk_of) -> None:
    """`trace` is exactly what AgentOrchestrator.run_turn() returns on its
    AgentTurnResult - [{"tool", "arguments", "success", "summary"}, ...].
    `risk_of` is AgentToolRegistry.risk_of, passed in rather than imported
    so this function has no dependency on which registry produced the trace."""
    for i, entry in enumerate(trace):
        risk: ToolRisk | None = risk_of(entry.get("tool"))
        db.add(AgentAction(
            run_id=run.id,
            sequence=i,
            tool_name=entry.get("tool", "unknown"),
            arguments=entry.get("arguments"),
            success=bool(entry.get("success")),
            summary=entry.get("summary"),
            risk=risk.value if risk else None,
        ))
    db.commit()


def complete_run(db: Session, run: AgentRun, final_result: str | None) -> AgentRun:
    run.status = AgentRunStatus.COMPLETED
    run.final_result = final_result
    run.current_step = None
    run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


def fail_run(db: Session, run: AgentRun, error: str) -> AgentRun:
    run.status = AgentRunStatus.FAILED
    run.error = error
    run.current_step = None
    run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


def get_org_run(db: Session, run_id: uuid.UUID, organization_id: uuid.UUID) -> AgentRun | None:
    run = db.execute(
        select(AgentRun).options(selectinload(AgentRun.actions)).where(AgentRun.id == run_id)
    ).scalar_one_or_none()
    if not run or run.organization_id != organization_id:
        return None
    return run


def list_org_runs(db: Session, organization_id: uuid.UUID, limit: int = 20) -> list[AgentRun]:
    limit = min(limit, 100)
    return list(
        db.execute(
            select(AgentRun).where(AgentRun.organization_id == organization_id)
            .order_by(AgentRun.started_at.desc()).limit(limit)
        ).scalars().all()
    )