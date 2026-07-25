from dataclasses import dataclass, field


@dataclass
class EmailAttachmentData:
    filename: str
    content_type: str | None = None
    size_bytes: int | None = None
    storage_key: str | None = None


@dataclass
class InboundEmail:
    """Normalized representation of an incoming email, independent of which
    provider produced it. Every provider's fetch/webhook handler must
    translate its own payload into this shape before handing it to
    EmailService — that's the entire point of the abstraction."""
    message_id: str
    from_address: str
    to_addresses: list[str]
    subject: str
    text_body: str
    inbox_email_address: str
    cc_addresses: list[str] = field(default_factory=list)
    bcc_addresses: list[str] = field(default_factory=list)
    html_body: str | None = None
    in_reply_to: str | None = None
    references: list[str] = field(default_factory=list)
    attachments: list[EmailAttachmentData] = field(default_factory=list)


@dataclass
class OutboundEmail:
    """Normalized representation of an email Nexora wants to send. Built by
    EmailService from a TicketComment, handed to whichever provider is
    active — the provider never sees TicketComment/Ticket directly."""
    message_id: str
    from_address: str
    to_addresses: list[str]
    subject: str
    text_body: str
    html_body: str | None = None
    in_reply_to: str | None = None
    references: list[str] = field(default_factory=list)
    cc_addresses: list[str] = field(default_factory=list)


@dataclass
class SendResult:
    success: bool
    provider_message_id: str | None = None
    error: str | None = None