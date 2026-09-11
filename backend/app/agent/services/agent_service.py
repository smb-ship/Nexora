"""Single entry point for running the Support Operations Agent. Routes
should call `run_support_operations_agent` and nothing lower-level -
everything about building the orchestrator, the tool context, and
persisting the run/action trail lives here so there's exactly one place
that can get any of it wrong.
"""

import logging

from sqlalchemy.orm import Session

from app.agent.runs import run_service
from app.agent.tools import AgentToolContext, build_operations_registry
from app.agent.orchestrator import AgentOrchestrator
from app.agent.security.validators import OPERATIONS_AGENT_SYSTEM_PROMPT
from app.models.agent_ops.run import AgentRun
from app.models.user import User

logger = logging.getLogger(__name__)

AGENT_NAME = "support_operations"


async def run_support_operations_agent(
    db: Session,
    user: User,
    message: str,
    history: list[dict] | None = None,
    provider=None,
) -> AgentRun:
    """Creates a persisted AgentRun, executes one orchestrator turn against
    the operations tool registry scoped to `user`'s organization, records
    every tool call as an AgentAction, and marks the run
    completed/failed. Returns the run with its `actions` populated.

    Known limitation: `current_step` is only ever set indirectly via
    completion/failure (see run_service) - AgentOrchestrator.run_turn()
    doesn't emit incremental progress callbacks, so there's no live
    "Searching knowledge base..." update mid-run yet. Milestone 9's
    dashboard should poll `status`, not expect `current_step` to change
    during a run - documented rather than worked around here, since
    adding a callback layer to the shared orchestrator is more surgery
    than this milestone's scope.
    """
    run = run_service.create_run(
        db, organization_id=user.organization_id, user_id=user.id,
        agent_name=AGENT_NAME, initial_request=message,
    )

    registry = build_operations_registry()
    orchestrator = AgentOrchestrator(tool_registry=registry, provider=provider, system_prompt=OPERATIONS_AGENT_SYSTEM_PROMPT)
    context = AgentToolContext(db=db, user=user, organization_id=user.organization_id)

    try:
        result = await orchestrator.run_turn(history=history or [], user_message=message, context=context)
    except Exception as exc:
        logger.error("Support Operations Agent run %s failed: %s", run.id, exc, exc_info=True)
        return run_service.fail_run(db, run, str(exc))

    if result.trace:
        run_service.record_trace(db, run, result.trace, registry.risk_of)

    return run_service.complete_run(db, run, result.content)