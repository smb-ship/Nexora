import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.events import Event
from app.models.webhook import OutgoingWebhook, WebhookDeliveryLog, WebhookDeliveryStatus
from app.webhooks.signing import build_signature_headers, canonical_json
from app.webhooks.formatters import format_payload

logger = logging.getLogger(__name__)

MAX_DELIVERY_ATTEMPTS = 5
RETRY_BACKOFF_MINUTES = [1, 5, 15, 60, 240]  # attempt index -> minutes until next retry
REQUEST_TIMEOUT_SECONDS = 10


def _next_retry_delay(attempt_count: int) -> timedelta | None:
    if attempt_count >= len(RETRY_BACKOFF_MINUTES):
        return None
    return timedelta(minutes=RETRY_BACKOFF_MINUTES[attempt_count - 1])


def _deliver_once(db: Session, webhook: OutgoingWebhook, log: WebhookDeliveryLog, body: dict) -> None:
    payload_bytes = canonical_json(body)
    headers = build_signature_headers(webhook.signing_secret, payload_bytes)

    log.attempt_count += 1
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = client.post(webhook.target_url, content=payload_bytes, headers=headers)
        log.response_status_code = response.status_code
        log.response_body = response.text[:2000]  # cap stored body size

        if 200 <= response.status_code < 300:
            log.status = WebhookDeliveryStatus.SUCCESS
            log.delivered_at = datetime.now(timezone.utc)
            log.next_retry_at = None
        else:
            _mark_retry_or_failed(log, error=f"HTTP {response.status_code}")
    except httpx.RequestError as exc:
        log.error_message = str(exc)
        _mark_retry_or_failed(log, error=str(exc))

    db.commit()


def _mark_retry_or_failed(log: WebhookDeliveryLog, error: str) -> None:
    log.error_message = error
    delay = _next_retry_delay(log.attempt_count)
    if delay is None:
        log.status = WebhookDeliveryStatus.FAILED
        log.next_retry_at = None
    else:
        log.status = WebhookDeliveryStatus.RETRYING
        log.next_retry_at = datetime.now(timezone.utc) + delay


def dispatch_to_webhooks(db: Session, event: Event) -> None:
    """Global bus subscriber (registered in event_subscribers.py). Finds
    every active webhook in the event's org whose event_types includes this
    event, and attempts one synchronous delivery each. On failure, a
    WebhookDeliveryLog row is left in RETRYING state for the sweep endpoint
    (Step 8b) to pick up later — the emitting request is never blocked
    beyond the initial attempt's timeout."""
    webhooks = db.execute(
        select(OutgoingWebhook).where(
            OutgoingWebhook.organization_id == event.organization_id,
            OutgoingWebhook.is_active.is_(True),
        )
    ).scalars().all()

    matching = [w for w in webhooks if event.type.value in w.event_types]
    if not matching:
        return

    public_dict = event.to_public_dict()

    for webhook in matching:
        log = WebhookDeliveryLog(
            webhook_id=webhook.id,
            organization_id=webhook.organization_id,
            event_type=event.type.value,
            event_id=event.id,
            payload=public_dict,
            status=WebhookDeliveryStatus.PENDING,
        )
        db.add(log)
        db.flush()

        body = format_payload(webhook.integration_type, event.type.value, public_dict)
        _deliver_once(db, webhook, log, body)


def sweep_retries(db: Session, organization_id) -> int:
    """Re-attempts every WebhookDeliveryLog in RETRYING state whose
    next_retry_at has passed. Intended to be called periodically by an
    external scheduler, exactly like run_idle_check — see the
    /webhooks/process-retries endpoint."""
    now = datetime.now(timezone.utc)
    due_logs = db.execute(
        select(WebhookDeliveryLog).where(
            WebhookDeliveryLog.organization_id == organization_id,
            WebhookDeliveryLog.status == WebhookDeliveryStatus.RETRYING,
            WebhookDeliveryLog.next_retry_at <= now,
        )
    ).scalars().all()

    for log in due_logs:
        webhook = db.get(OutgoingWebhook, log.webhook_id)
        if not webhook or not webhook.is_active:
            log.status = WebhookDeliveryStatus.FAILED
            log.error_message = "Webhook deleted or deactivated before retry"
            db.commit()
            continue
        body = format_payload(webhook.integration_type, log.event_type, log.payload)
        _deliver_once(db, webhook, log, body)

    return len(due_logs)