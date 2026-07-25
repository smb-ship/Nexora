import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.email import EmailInbox, EmailProviderType
from app.models.user import User
from app.core.permissions import require_permission, Permission
from app.schemas.email import SimulateInboundEmailRequest, DevOutboxItem, EmailInboxCreate, EmailInboxOut
from app.email.schemas import InboundEmail
from app.email.service import EmailService
from app.email.providers.development import DevelopmentEmailProvider

router = APIRouter(prefix="/email-dev", tags=["email-dev"])


@router.post("/inboxes", response_model=EmailInboxOut, status_code=status.HTTP_201_CREATED)
def create_inbox(
    payload: EmailInboxCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    """Reuses WORKFLOW_MANAGE for now — inbox configuration is an
    admin/manager-level action with no dedicated permission yet (see Known
    Technical Debt: a proper EMAIL_MANAGE permission is a 5-minute add
    later, deliberately deferred to avoid scope creep on this milestone)."""
    if db.query(EmailInbox).filter(EmailInbox.email_address == payload.email_address).first():
        raise HTTPException(status_code=400, detail="An inbox with this email address already exists")

    inbox = EmailInbox(
        organization_id=current_user.organization_id,
        email_address=payload.email_address,
        display_name=payload.display_name,
        provider_type=EmailProviderType(payload.provider_type),
    )
    db.add(inbox)
    db.commit()
    db.refresh(inbox)
    return inbox


@router.get("/inboxes", response_model=list[EmailInboxOut])
def list_inboxes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    return db.query(EmailInbox).filter(EmailInbox.organization_id == current_user.organization_id).all()


@router.post("/simulate-inbound", status_code=status.HTTP_201_CREATED)
async def simulate_inbound(
    payload: SimulateInboundEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE)),
):
    inbox = db.get(EmailInbox, payload.inbox_id)
    if not inbox or inbox.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Inbox not found")

    email = InboundEmail(
        message_id=payload.message_id or f"<sim-{uuid.uuid4()}@nexora.dev>",
        from_address=payload.from_address,
        to_addresses=payload.to_addresses or [inbox.email_address],
        subject=payload.subject,
        text_body=payload.text_body,
        html_body=payload.html_body,
        in_reply_to=payload.in_reply_to,
        references=payload.references,
        inbox_email_address=inbox.email_address,
    )

    comment = await EmailService(db).process_inbound(inbox, email)
    return {"ticket_id": str(comment.ticket_id), "comment_id": str(comment.id), "message_id": comment.email_message_id}


@router.get("/outbox", response_model=list[DevOutboxItem])
def get_dev_outbox(current_user: User = Depends(require_permission(Permission.WORKFLOW_MANAGE))):
    """Everything the development provider has 'sent' during this server
    process's lifetime. This is how you verify outbound replies without a
    real mailbox — see Phase D."""
    return DevelopmentEmailProvider.get_sent_log()