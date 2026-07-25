import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.incoming_webhook_key import IncomingWebhookKey, generate_key
from app.models.ticket import Ticket, TicketComment, TicketSource, TicketPriority
from app.models.user import User
from app.core.permissions import require_permission, Permission
from app.core.events import emit_event, EventType
from app.schemas.integration import (
    IncomingWebhookKeyCreate, IncomingWebhookKeyOut, IncomingWebhookKeyCreated,
    N8nCreateTicketRequest, N8nAddCommentRequest,
)
import hashlib

router = APIRouter(prefix="/integrations", tags=["integrations"])


# --- Key management (staff-authenticated) ---

@router.post("/webhook-keys", response_model=IncomingWebhookKeyCreated, status_code=201)
def create_webhook_key(
    payload: IncomingWebhookKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    plaintext, key_hash = generate_key()
    key = IncomingWebhookKey(organization_id=current_user.organization_id, name=payload.name, key_hash=key_hash)
    db.add(key)
    db.commit()
    db.refresh(key)
    return IncomingWebhookKeyCreated(
        id=key.id, name=key.name, is_active=key.is_active,
        created_at=key.created_at, last_used_at=key.last_used_at, plaintext_key=plaintext,
    )


@router.get("/webhook-keys", response_model=list[IncomingWebhookKeyOut])
def list_webhook_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    return db.execute(
        select(IncomingWebhookKey).where(IncomingWebhookKey.organization_id == current_user.organization_id)
    ).scalars().all()


@router.delete("/webhook-keys/{key_id}", status_code=204)
def revoke_webhook_key(
    key_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    key = db.get(IncomingWebhookKey, key_id)
    if not key or key.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Key not found")
    db.delete(key)
    db.commit()


# --- Incoming actions (key-authenticated, for n8n) ---

def _authenticate_incoming(db: Session, x_nexora_webhook_key: str | None) -> IncomingWebhookKey:
    if not x_nexora_webhook_key:
        raise HTTPException(status_code=401, detail="Missing X-Nexora-Webhook-Key header")
    key_hash = hashlib.sha256(x_nexora_webhook_key.encode()).hexdigest()
    key = db.execute(
        select(IncomingWebhookKey).where(IncomingWebhookKey.key_hash == key_hash, IncomingWebhookKey.is_active.is_(True))
    ).scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=401, detail="Invalid or inactive webhook key")
    key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return key


@router.post("/incoming/create-ticket", status_code=201)
def n8n_create_ticket(
    payload: N8nCreateTicketRequest,
    db: Session = Depends(get_db),
    x_nexora_webhook_key: str | None = Header(default=None),
):
    """Called by an n8n Workflow's HTTP Request node. Constructs a Ticket
    directly — same pattern as EmailService.process_inbound — rather than
    routing through tickets.py's create_ticket, since that endpoint expects
    an authenticated staff User, not a key-authenticated integration."""
    key = _authenticate_incoming(db, x_nexora_webhook_key)

    ticket = Ticket(
        organization_id=key.organization_id,
        subject=payload.subject,
        description=payload.description,
        requester_name=payload.requester_name,
        requester_email=payload.requester_email,
        created_by=None,  # no staff user initiated this — system/integration-created
        priority=TicketPriority(payload.priority) if payload.priority else TicketPriority.MEDIUM,
        source=TicketSource.WEB,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    emit_event(
        db, EventType.TICKET_CREATED, ticket.organization_id,
        ticket=ticket,
        data={"ticket_id": str(ticket.id), "subject": ticket.subject, "source": "n8n"},
    )
    return {"ticket_id": str(ticket.id)}


@router.post("/incoming/add-comment", status_code=201)
def n8n_add_comment(
    payload: N8nAddCommentRequest,
    db: Session = Depends(get_db),
    x_nexora_webhook_key: str | None = Header(default=None),
):
    key = _authenticate_incoming(db, x_nexora_webhook_key)

    ticket = db.get(Ticket, payload.ticket_id)
    if not ticket or ticket.organization_id != key.organization_id:
        raise HTTPException(status_code=404, detail="Ticket not found")

    comment = TicketComment(
        ticket_id=ticket.id,
        author_id=ticket.created_by or ticket.customer_id,
        body=payload.body,
        is_internal_note=False,
    )
    db.add(comment)
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comment)

    emit_event(
        db, EventType.TICKET_COMMENT_ADDED, ticket.organization_id,
        ticket=ticket,
        data={"ticket_id": str(ticket.id), "comment_id": str(comment.id), "source": "n8n"},
    )
    return {"comment_id": str(comment.id)}