from typing import Any


def format_payload(integration_type: str, event_type: str, public_dict: dict[str, Any]) -> dict[str, Any]:
    """Phase E: Discord and Slack expect their own JSON shape (a top-level
    'content' or 'text' string), not Nexora's raw event envelope. Everything
    else (generic, n8n) gets the raw envelope untouched — n8n's webhook node
    parses arbitrary JSON natively, so no reshaping is needed there."""
    if integration_type == "discord":
        return {
            "content": f"**{event_type}**\n```json\n{public_dict}\n```",
        }
    if integration_type == "slack":
        return {
            "text": f"*{event_type}*\n```{public_dict}```",
        }
    return public_dict