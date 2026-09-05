import uuid

from sqlalchemy import or_, select

from app.agent.security.tool_permissions import ToolRisk
from app.agent.tool_registry import ToolResult
from app.agent.tools.base import AgentToolContext, AgentToolRegistry
from app.ai.embeddings import cosine_similarity, embed_text
from app.models.knowledge import ArticleStatus, KnowledgeArticle

# Same ceiling app/api/routes/knowledge.py uses before handing candidates
# to an AI call - kept here as a sane cap on how many articles we score.
MAX_CANDIDATES = 50


def _parse_uuid(raw) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(raw))
    except (ValueError, TypeError, AttributeError):
        return None


def _article_summary(a: KnowledgeArticle, score: float | None = None) -> dict:
    out = {
        "id": str(a.id),
        "title": a.title,
        "tags": a.tags,
        "status": a.status.value,
        "excerpt": a.body[:300],
        "updated_at": a.updated_at.isoformat(),
    }
    if score is not None:
        out["similarity"] = round(score, 4)
    return out


async def _search_knowledge_base(args: dict, ctx: AgentToolContext) -> ToolResult:
    """Reuses the existing embedding pipeline (app.ai.embeddings) rather
    than standing up a second RAG system - same one used by
    /knowledge/articles/suggest and the staff 'Ask VertexIQ' RAG."""
    query = (args.get("query") or "").strip()
    if not query:
        return ToolResult(success=False, summary="query is required.")

    published = ctx.db.execute(
        select(KnowledgeArticle)
        .where(KnowledgeArticle.organization_id == ctx.organization_id, KnowledgeArticle.status == ArticleStatus.PUBLISHED)
        .order_by(KnowledgeArticle.updated_at.desc())
        .limit(MAX_CANDIDATES)
    ).scalars().all()

    if not published:
        return ToolResult(success=True, summary="No published knowledge articles in this organization.", data={"articles": []})

    query_vec = embed_text(query)
    scored = [
        (a, cosine_similarity(query_vec, a.embedding))
        for a in published
        if a.embedding
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    limit = min(int(args.get("limit") or 5), 20)
    top = scored[:limit]

    return ToolResult(
        success=True,
        summary=f"Found {len(top)} relevant article(s).",
        data={"articles": [_article_summary(a, score) for a, score in top]},
    )


async def _get_knowledge_document(args: dict, ctx: AgentToolContext) -> ToolResult:
    article_id = _parse_uuid(args.get("article_id"))
    if not article_id:
        return ToolResult(success=False, summary="article_id must be a valid UUID.")

    article = ctx.db.get(KnowledgeArticle, article_id)
    if not article or article.organization_id != ctx.organization_id:
        return ToolResult(success=False, summary="Article not found in this organization.")

    return ToolResult(
        success=True,
        summary=f"Found article '{article.title}'.",
        data={
            "id": str(article.id), "title": article.title, "body": article.body,
            "tags": article.tags, "status": article.status.value, "updated_at": article.updated_at.isoformat(),
        },
    )


async def _find_similar_articles(args: dict, ctx: AgentToolContext) -> ToolResult:
    article_id = _parse_uuid(args.get("article_id"))
    if not article_id:
        return ToolResult(success=False, summary="article_id must be a valid UUID.")

    source = ctx.db.get(KnowledgeArticle, article_id)
    if not source or source.organization_id != ctx.organization_id:
        return ToolResult(success=False, summary="Article not found in this organization.")

    if not source.embedding:
        return ToolResult(success=True, summary="Source article has no embedding yet.", data={"articles": []})

    candidates = ctx.db.execute(
        select(KnowledgeArticle).where(
            KnowledgeArticle.organization_id == ctx.organization_id,
            KnowledgeArticle.status == ArticleStatus.PUBLISHED,
            KnowledgeArticle.id != article_id,
        ).limit(MAX_CANDIDATES)
    ).scalars().all()

    scored = [(a, cosine_similarity(source.embedding, a.embedding)) for a in candidates if a.embedding]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    limit = min(int(args.get("limit") or 5), 20)
    top = scored[:limit]

    return ToolResult(
        success=True,
        summary=f"Found {len(top)} similar article(s).",
        data={"articles": [_article_summary(a, score) for a, score in top]},
    )


def register(registry: AgentToolRegistry) -> None:
    # No required_permission on any tool below: GET /knowledge/articles and
    # GET /knowledge/articles/{id} are open to any authenticated staff
    # member (Depends(get_current_user), no require_permission gate), so
    # these read tools match that - not an oversight.
    registry.register(
        name="search_knowledge_base",
        description="Semantic search over this organization's published knowledge base articles.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "description": "Max results, default 5, max 20"},
            },
            "required": ["query"],
        },
        risk=ToolRisk.READ,
        executor=_search_knowledge_base,
    )
    registry.register(
        name="get_knowledge_document",
        description="Get the full title/body/tags of a single knowledge article by id.",
        parameters={
            "type": "object",
            "properties": {"article_id": {"type": "string"}},
            "required": ["article_id"],
        },
        risk=ToolRisk.READ,
        executor=_get_knowledge_document,
    )
    registry.register(
        name="find_similar_articles",
        description="Find published articles semantically similar to a given article.",
        parameters={
            "type": "object",
            "properties": {
                "article_id": {"type": "string"},
                "limit": {"type": "integer", "description": "Max results, default 5, max 20"},
            },
            "required": ["article_id"],
        },
        risk=ToolRisk.READ,
        executor=_find_similar_articles,
    )