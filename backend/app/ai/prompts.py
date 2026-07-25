from app.models.ticket import Ticket


def _conversation_context(ticket: Ticket, include_internal: bool = True) -> str:
    lines = [
        f"Subject: {ticket.subject}",
        f"Customer ({ticket.requester_name}): {ticket.description}",
    ]
    for comment in ticket.comments:
        if comment.is_internal_note and not include_internal:
            continue
        speaker = "Agent (internal note)" if comment.is_internal_note else "Agent (reply to customer)"
        lines.append(f"{speaker}: {comment.body}")
    return "\n".join(lines)


def summarize_prompt(ticket: Ticket) -> tuple[str, str]:
    system = (
        "You are an assistant for customer support agents. Summarize the ticket "
        "conversation in 2-4 concise sentences, focused on the customer's issue and "
        "current state. Only mention internal notes if directly relevant to understanding "
        "the issue."
    )
    user = _conversation_context(ticket, include_internal=True)
    return system, user


def sentiment_prompt(ticket: Ticket) -> tuple[str, str]:
    system = (
        "You are a sentiment analysis assistant. Analyze the customer's tone based on "
        "their messages only. Respond ONLY with a JSON object: "
        '{"sentiment": "positive"|"neutral"|"negative"|"frustrated", "score": <float -1.0 to 1.0>}. '
        "No other text."
    )
    user = _conversation_context(ticket, include_internal=False)
    return system, user


def priority_prompt(ticket: Ticket) -> tuple[str, str]:
    system = (
        "You are a triage assistant for a customer support platform. Based on the ticket "
        "content, predict the appropriate priority. Respond ONLY with a JSON object: "
        '{"priority": "low"|"medium"|"high"|"urgent", "reasoning": "<one sentence>"}. '
        "No other text."
    )
    user = _conversation_context(ticket, include_internal=True)
    return system, user


def tags_prompt(ticket: Ticket) -> tuple[str, str]:
    system = (
        "You are a ticket tagging assistant. Suggest 2-5 short, lowercase, hyphenated tags "
        "that categorize this ticket (e.g. 'billing-issue', 'login-error', 'feature-request'). "
        'Respond ONLY with compact, single-line JSON, no indentation or line breaks: '
        '{"tags": ["tag-one", "tag-two"]}. No other text.'
    )
    user = _conversation_context(ticket, include_internal=True)
    return system, user


def reply_suggestion_prompt(ticket: Ticket, instructions: str | None = None) -> tuple[str, str]:
    system = (
        "You are drafting a reply to a customer on behalf of a support agent. Write a "
        "professional, empathetic, concise reply that addresses the customer's issue based "
        "on the conversation so far. Do not reference internal notes. Return plain text only, "
        "no markdown, no preamble - just the reply message."
    )
    context = _conversation_context(ticket, include_internal=False)
    if instructions:
        context += f"\n\nAdditional instructions from agent: {instructions}"
    return system, context


def internal_note_prompt(ticket: Ticket) -> tuple[str, str]:
    system = (
        "You are an internal assistant for support agents. Based on the full ticket "
        "conversation (including internal notes), write a short internal-only note "
        "highlighting anything agents should be aware of: risk of churn, escalation needs, "
        "unresolved questions, or relevant context. This is never shown to the customer. "
        "Keep it to 2-3 sentences."
    )
    user = _conversation_context(ticket, include_internal=True)
    return system, user