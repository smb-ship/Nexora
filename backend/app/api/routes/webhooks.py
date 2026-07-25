import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.webhook import OutgoingWebhook, WebhookDeliveryLog
from app.models.user import User
from app.core.permissions import require_permission, Permission
from app.schemas.webhook import (
    OutgoingWebhookCreate, OutgoingWebhookUpdate, OutgoingWebhookOut, WebhookDeliveryLogOut,
)
from app.webhooks.dispatcher import sweep_retries

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _check_org(webhook: OutgoingWebhook | None, current_user: User) -> OutgoingWebhook:
    if not webhook or webhook.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.post("/", response_model=OutgoingWebhookOut, status_code=201)
def create_webhook(
    payload: OutgoingWebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    webhook = OutgoingWebhook(
        organization_id=current_user.organization_id,
        name=payload.name,
        target_url=payload.target_url,
        event_types=payload.event_types,
        integration_type=payload.integration_type,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.get("/", response_model=list[OutgoingWebhookOut])
def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    return db.execute(
        select(OutgoingWebhook).where(OutgoingWebhook.organization_id == current_user.organization_id)
    ).scalars().all()


@router.patch("/{webhook_id}", response_model=OutgoingWebhookOut)
def update_webhook(
    webhook_id: uuid.UUID,
    payload: OutgoingWebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    webhook = _check_org(db.get(OutgoingWebhook, webhook_id), current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(webhook, field, value)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.delete("/{webhook_id}", status_code=204)
def delete_webhook(
    webhook_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    webhook = _check_org(db.get(OutgoingWebhook, webhook_id), current_user)
    db.delete(webhook)
    db.commit()


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryLogOut])
def list_deliveries(
    webhook_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    _check_org(db.get(OutgoingWebhook, webhook_id), current_user)
    return db.execute(
        select(WebhookDeliveryLog)
        .where(WebhookDeliveryLog.webhook_id == webhook_id)
        .order_by(WebhookDeliveryLog.created_at.desc())
        .limit(200)
    ).scalars().all()


@router.post("/process-retries", status_code=200)
def process_retries(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    """Mirrors the existing /workflows/process-idle pattern from Milestone 6
    — call this periodically from cron/APScheduler/Windows Task Scheduler
    to sweep due retries. Manually triggerable here for testing."""
    count = sweep_retries(db, current_user.organization_id)
    return {"retried": count}