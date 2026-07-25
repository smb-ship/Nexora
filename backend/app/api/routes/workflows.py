import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.workflow import WorkflowRule, WorkflowCondition, WorkflowAction, WorkflowExecutionLog
from app.models.user import User
from app.schemas.workflow import (
    WorkflowRuleCreate, WorkflowRuleUpdate, WorkflowRuleOut, WorkflowExecutionLogOut,
)
from app.core.permissions import require_permission, Permission
from app.workflows.engine import run_idle_check

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _check_org(rule: WorkflowRule | None, current_user: User) -> WorkflowRule:
    if not rule or rule.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Workflow rule not found")
    return rule


def _get_rule_with_children(db: Session, rule_id: uuid.UUID) -> WorkflowRule | None:
    return (
        db.execute(
            select(WorkflowRule)
            .options(joinedload(WorkflowRule.conditions), joinedload(WorkflowRule.actions))
            .where(WorkflowRule.id == rule_id)
        )
        .unique()
        .scalar_one_or_none()
    )


@router.post("/", response_model=WorkflowRuleOut, status_code=201)
def create_rule(
    payload: WorkflowRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    rule = WorkflowRule(
        organization_id=current_user.organization_id,
        name=payload.name,
        description=payload.description,
        trigger_type=payload.trigger_type,
        condition_logic=payload.condition_logic,
        is_active=payload.is_active,
        run_order=payload.run_order,
        created_by=current_user.id,
    )
    db.add(rule)
    db.flush()

    for c in payload.conditions:
        db.add(WorkflowCondition(rule_id=rule.id, field=c.field, operator=c.operator, value=c.value, order=c.order))
    for a in payload.actions:
        db.add(WorkflowAction(rule_id=rule.id, action_type=a.action_type, params=a.params, order=a.order))

    db.commit()
    return _get_rule_with_children(db, rule.id)


@router.get("/", response_model=list[WorkflowRuleOut])
def list_rules(
    is_active: bool | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    stmt = (
        select(WorkflowRule)
        .options(joinedload(WorkflowRule.conditions), joinedload(WorkflowRule.actions))
        .where(WorkflowRule.organization_id == current_user.organization_id)
        .order_by(WorkflowRule.run_order.asc(), WorkflowRule.created_at.desc())
    )
    if is_active is not None:
        stmt = stmt.where(WorkflowRule.is_active.is_(is_active))
    return db.execute(stmt).unique().scalars().all()


@router.get("/{rule_id}", response_model=WorkflowRuleOut)
def get_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    return _check_org(_get_rule_with_children(db, rule_id), current_user)


@router.patch("/{rule_id}", response_model=WorkflowRuleOut)
def update_rule(
    rule_id: uuid.UUID,
    payload: WorkflowRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    rule = _check_org(db.get(WorkflowRule, rule_id), current_user)

    update_data = payload.model_dump(exclude_unset=True, exclude={"conditions", "actions"})
    for field, value in update_data.items():
        setattr(rule, field, value)

    if payload.conditions is not None:
        db.query(WorkflowCondition).filter(WorkflowCondition.rule_id == rule.id).delete()
        for c in payload.conditions:
            db.add(WorkflowCondition(rule_id=rule.id, field=c.field, operator=c.operator, value=c.value, order=c.order))

    if payload.actions is not None:
        db.query(WorkflowAction).filter(WorkflowAction.rule_id == rule.id).delete()
        for a in payload.actions:
            db.add(WorkflowAction(rule_id=rule.id, action_type=a.action_type, params=a.params, order=a.order))

    db.commit()
    return _get_rule_with_children(db, rule.id)


@router.post("/{rule_id}/toggle", response_model=WorkflowRuleOut)
def toggle_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    rule = _check_org(db.get(WorkflowRule, rule_id), current_user)
    rule.is_active = not rule.is_active
    db.commit()
    return _get_rule_with_children(db, rule.id)


@router.delete("/{rule_id}", status_code=204)
def delete_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    rule = _check_org(db.get(WorkflowRule, rule_id), current_user)
    db.delete(rule)
    db.commit()


@router.get("/{rule_id}/logs", response_model=list[WorkflowExecutionLogOut])
def get_rule_logs(
    rule_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    rule = _check_org(db.get(WorkflowRule, rule_id), current_user)
    stmt = (
        select(WorkflowExecutionLog)
        .where(WorkflowExecutionLog.rule_id == rule.id)
        .order_by(WorkflowExecutionLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


@router.post("/process-idle", status_code=200)
def process_idle_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    """Manually trigger TICKET_IDLE rule evaluation for this organization.
    In production, wire this to a scheduled job instead of a manual click —
    see Known Technical Debt at the end of this milestone."""
    count = run_idle_check(db, current_user.organization_id)
    return {"tickets_checked": count}