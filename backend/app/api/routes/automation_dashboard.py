from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.permissions import require_permission, Permission
from app.models.webhook import OutgoingWebhook, WebhookDeliveryLog, WebhookDeliveryStatus
from app.models.event_log import EventLog
from app.schemas.automation_dashboard import AutomationDashboardOut, ConnectedServiceOut, EventFeedItemOut

router = APIRouter(prefix="/automation-dashboard", tags=["automation-dashboard"])


@router.get("/", response_model=AutomationDashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    org_id = current_user.organization_id
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    webhooks = db.execute(select(OutgoingWebhook).where(OutgoingWebhook.organization_id == org_id)).scalars().all()

    services: list[ConnectedServiceOut] = []
    for w in webhooks:
        success_count = db.execute(
            select(func.count()).select_from(WebhookDeliveryLog).where(
                WebhookDeliveryLog.webhook_id == w.id, WebhookDeliveryLog.status == WebhookDeliveryStatus.SUCCESS,
            )
        ).scalar_one()
        failed_count = db.execute(
            select(func.count()).select_from(WebhookDeliveryLog).where(
                WebhookDeliveryLog.webhook_id == w.id, WebhookDeliveryLog.status == WebhookDeliveryStatus.FAILED,
            )
        ).scalar_one()
        last_log = db.execute(
            select(WebhookDeliveryLog).where(WebhookDeliveryLog.webhook_id == w.id)
            .order_by(WebhookDeliveryLog.created_at.desc()).limit(1)
        ).scalar_one_or_none()

        services.append(ConnectedServiceOut(
            id=w.id, name=w.name, integration_type=w.integration_type, target_url=w.target_url,
            is_active=w.is_active, event_types=w.event_types,
            success_count=success_count, failed_count=failed_count,
            last_delivery_at=last_log.created_at if last_log else None,
        ))

    pending_retries = db.execute(
        select(func.count()).select_from(WebhookDeliveryLog).where(
            WebhookDeliveryLog.organization_id == org_id, WebhookDeliveryLog.status == WebhookDeliveryStatus.RETRYING,
        )
    ).scalar_one()

    deliveries_24h = db.execute(
        select(func.count()).select_from(WebhookDeliveryLog).where(
            WebhookDeliveryLog.organization_id == org_id, WebhookDeliveryLog.created_at >= since,
        )
    ).scalar_one()

    failures_24h = db.execute(
        select(func.count()).select_from(WebhookDeliveryLog).where(
            WebhookDeliveryLog.organization_id == org_id, WebhookDeliveryLog.status == WebhookDeliveryStatus.FAILED,
            WebhookDeliveryLog.created_at >= since,
        )
    ).scalar_one()

    recent_events = db.execute(
        select(EventLog).where(EventLog.organization_id == org_id).order_by(EventLog.created_at.desc()).limit(50)
    ).scalars().all()

    return AutomationDashboardOut(
        connected_services=services,
        pending_retries=pending_retries,
        deliveries_last_24h=deliveries_24h,
        failures_last_24h=failures_24h,
        recent_events=[
            EventFeedItemOut(event_id=e.event_id, event_type=e.event_type, data=e.data, created_at=e.created_at)
            for e in recent_events
        ],
    )