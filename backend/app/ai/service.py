import json
import logging

from app.ai.providers.base import AIProvider
from app.ai.providers.factory import get_ai_provider
from app.ai import prompts
from app.models.ticket import Ticket, TicketPriority
from app.models.ticket_ai_insight import SentimentLabel

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Raised when the AI provider fails or returns an unusable response."""


class AIService:
    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or get_ai_provider()

    async def summarize(self, ticket: Ticket) -> str:
        system, user = prompts.summarize_prompt(ticket)
        text = await self._provider.complete(system=system, user=user, temperature=0.3, max_tokens=300)
        return text.strip()

    async def analyze_sentiment(self, ticket: Ticket) -> tuple[SentimentLabel, float]:
        system, user = prompts.sentiment_prompt(ticket)
        raw = await self._provider.complete(
            system=system, user=user, temperature=0.0, max_tokens=300, json_mode=True
        )
        data = self._parse_json(raw)
        try:
            return SentimentLabel(data["sentiment"]), float(data["score"])
        except (KeyError, ValueError) as exc:
            raise AIServiceError(f"Malformed sentiment response: {raw}") from exc

    async def predict_priority(self, ticket: Ticket) -> TicketPriority:
        system, user = prompts.priority_prompt(ticket)
        raw = await self._provider.complete(
            system=system, user=user, temperature=0.0, max_tokens=300, json_mode=True
        )
        data = self._parse_json(raw)
        try:
            return TicketPriority(data["priority"])
        except (KeyError, ValueError) as exc:
            raise AIServiceError(f"Malformed priority response: {raw}") from exc

    async def suggest_tags(self, ticket: Ticket) -> list[str]:
        system, user = prompts.tags_prompt(ticket)
        raw = await self._provider.complete(
            system=system, user=user, temperature=0.3, max_tokens=500, json_mode=True
        )
    
        data = self._parse_json(raw)
        tags = data.get("tags")
        if not isinstance(tags, list):
            raise AIServiceError(f"Malformed tags response: {raw}")
        return [str(t) for t in tags][:5]

    async def suggest_reply(self, ticket: Ticket, instructions: str | None = None) -> str:
        system, user = prompts.reply_suggestion_prompt(ticket, instructions)
        text = await self._provider.complete(system=system, user=user, temperature=0.5, max_tokens=400)
        return text.strip()

    async def generate_internal_note(self, ticket: Ticket) -> str:
        system, user = prompts.internal_note_prompt(ticket)
        text = await self._provider.complete(system=system, user=user, temperature=0.3, max_tokens=200)
        return text.strip()

    async def suggest_articles(self, ticket: Ticket, candidates: list[dict]) -> list[dict]:
        """candidates: list of {"id": str, "title": str, "excerpt": str}.
        Returns a list of {"id": str, "reason": str} in relevance order, as
        returned by the model — the router (knowledge.py) resolves these IDs
        back to full KnowledgeArticle rows."""
        if not candidates:
            return []
        system, user = prompts.suggest_articles_prompt(ticket, candidates)
        raw = await self._provider.complete(
            system=system, user=user, temperature=0.0, max_tokens=500, json_mode=True
        )
        data = self._parse_json(raw)
        suggestions = data.get("suggestions")
        if not isinstance(suggestions, list):
            raise AIServiceError(f"Malformed suggest_articles response: {raw}")
        return suggestions

    async def answer_with_rag(self, question: str, articles: list[dict]) -> str:
        """articles: pre-retrieved top-k KB articles (embedding similarity
        search happens in the router, not here — this method only asks the
        LLM to answer grounded in what's passed in)."""
        system, user = prompts.rag_answer_prompt(question, articles)
        text = await self._provider.complete(system=system, user=user, temperature=0.2, max_tokens=600)
        return text.strip()

    @staticmethod
    def _parse_json(raw: str) -> dict:
        cleaned = raw.strip()

        # Strip markdown code fences (```json ... ``` or ``` ... ```)
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        # Strip conversational preamble by extracting the outermost {...} block
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("AI provider returned invalid JSON even after cleanup: %s", raw)
            raise AIServiceError(f"Invalid JSON from AI provider: {raw}") from exc