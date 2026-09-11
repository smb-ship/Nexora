import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.runs import run_service
from app.agent.services.agent_service import run_support_operations_agent
from app.api.routes.analytics import require_staff
from app.db.session import get_db
from app.models.user import User
from app.schemas.agent_ops.run import AgentRunOut, AgentRunRequest, AgentRunSummary

router = APIRouter(prefix="/agent-ops/runs", tags=["agent-ops"])


@router.post("", response_model=AgentRunOut)
async def create_run(
    payload: AgentRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> AgentRunOut:
    """Runs the Support Operations Agent once and returns the completed
    (or failed) run with its full action trace. Reuses the same
    require_staff dependency app/api/routes/analytics.py already defines
    to keep customers out - individual tools still enforce their own
    Permission on top of this, per Milestone 3."""
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")
    run = await run_support_operations_agent(db, current_user, payload.message)
    return run


@router.get("", response_model=list[AgentRunSummary])
def list_runs(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> list[AgentRunSummary]:
    return run_service.list_org_runs(db, current_user.organization_id, limit=limit)


@router.get("/{run_id}", response_model=AgentRunOut)
def get_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> AgentRunOut:
    run = run_service.get_org_run(db, run_id, current_user.organization_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run