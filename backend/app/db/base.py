from app.db.base_class import Base
from app.models.user import User  # noqa
from app.models.ticket import Ticket, TicketComment  # noqa
from app.models.ticket_read_receipt import TicketReadReceipt  # noqa
from app.models.organization import Organization  # noqa
from app.models.team import Team, TeamMembership  # noqa
from app.models.invitation import Invitation  # noqa
from app.models.webhook import OutgoingWebhook, WebhookDeliveryLog  # noqa
from app.models.event_log import EventLog  # noqa
from app.models.incoming_webhook_key import IncomingWebhookKey  # noqa
from app.models.chat import ChatWidgetSettings, ChatVisitor, ChatConversation, ChatMessage  # noqa
from app.models.knowledge import KnowledgeArticle  # noqa
from app.models.customer_note import CustomerNote  # noqa
from app.models.prompt_template import PromptTemplate  # noqa