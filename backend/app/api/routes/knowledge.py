import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.knowledge import KnowledgeArticle, ArticleStatus
from app.models.ticket import Ticket
from app.models.user import User
from app.core.permissions import require_permission, Permission
from app.api.deps import get_current_user
from app.schemas.knowledge import (
    KnowledgeArticleCreate, KnowledgeArticleUpdate, KnowledgeArticleOut,
    KnowledgeArticleListItem, SuggestedArticleOut,
)
from app.ai.service import AIService, AIServiceError
from app.ai.embeddings import embed_text

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# How many published articles get sent to the AI as candidates. Kept
# deliberately small — a real RAG/embedding pipeline would scale past this,
# but for a KB of reasonable size, sending titles+excerpts directly to the
# LLM is simpler and avoids standing up a vector store for this milestone.
MAX_AI_CANDIDATES = 30


def _check_org(article: KnowledgeArticle | None, current_user: User) -> KnowledgeArticle:
    if not article or article.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/articles", response_model=KnowledgeArticleOut, status_code=201)
def create_article(
    payload: KnowledgeArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.KNOWLEDGE_MANAGE)),
):
    status_enum = ArticleStatus(payload.status)
    article = KnowledgeArticle(
        organization_id=current_user.organization_id,
        title=payload.title,
        body=payload.body,
        tags=payload.tags,
        status=status_enum,
        author_id=current_user.id,
        published_at=datetime.now(timezone.utc) if status_enum == ArticleStatus.PUBLISHED else None,
    )
    if payload.body.strip():
        article.embedding = embed_text(f"{payload.title}\n{payload.body}")
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.get("/articles", response_model=list[KnowledgeArticleListItem])
def list_articles(
    search: str | None = Query(None, min_length=1, max_length=200),
    status: str | None = Query(None),
    tag: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Read access is available to any authenticated staff member — no
    KNOWLEDGE_MANAGE gate here, matching how ticket listing works."""
    stmt = select(KnowledgeArticle).where(KnowledgeArticle.organization_id == current_user.organization_id)

    if status:
        stmt = stmt.where(KnowledgeArticle.status == status)
    if tag:
        stmt = stmt.where(KnowledgeArticle.tags.any(tag))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(KnowledgeArticle.title.ilike(pattern), KnowledgeArticle.body.ilike(pattern)))

    stmt = stmt.order_by(KnowledgeArticle.updated_at.desc())
    return db.execute(stmt).scalars().all()


@router.get("/articles/suggest", response_model=list[SuggestedArticleOut])
async def suggest_articles_for_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.TICKET_AI_USE)),
):
    """AI-assisted retrieval: given a ticket, ask the AI provider which
    published KB articles (title + short excerpt of each) are most
    relevant. Reuses AIService exactly like every other AI feature in
    Nexora — no separate embedding/vector infrastructure."""
    ticket = db.get(Ticket, ticket_id)
    if not ticket or ticket.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Ticket not found")

    published = db.execute(
        select(KnowledgeArticle)
        .where(
            KnowledgeArticle.organization_id == current_user.organization_id,
            KnowledgeArticle.status == ArticleStatus.PUBLISHED,
        )
        .order_by(KnowledgeArticle.updated_at.desc())
        .limit(MAX_AI_CANDIDATES)
    ).scalars().all()

    if not published:
        return []

    candidates = [
        {"id": str(a.id), "title": a.title, "excerpt": a.body[:200]}
        for a in published
    ]
    articles_by_id = {str(a.id): a for a in published}

    try:
        suggestions = await AIService().suggest_articles(ticket, candidates)
    except AIServiceError:
        # Never let a bad AI response break the ticket workflow — surface
        # an empty suggestion list rather than a 500.
        return []

    results: list[SuggestedArticleOut] = []
    for s in suggestions:
        article = articles_by_id.get(str(s.get("id")))
        if article:
            results.append(SuggestedArticleOut(
                id=article.id, title=article.title, tags=article.tags,
                reason=str(s.get("reason", "")),
            ))
    return results


@router.get("/articles/{article_id}", response_model=KnowledgeArticleOut)
def get_article(
    article_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    article = _check_org(db.get(KnowledgeArticle, article_id), current_user)
    article.view_count += 1
    db.commit()
    db.refresh(article)
    return article


@router.patch("/articles/{article_id}", response_model=KnowledgeArticleOut)
def update_article(
    article_id: uuid.UUID,
    payload: KnowledgeArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.KNOWLEDGE_MANAGE)),
):
    article = _check_org(db.get(KnowledgeArticle, article_id), current_user)
    update_data = payload.model_dump(exclude_unset=True)

    was_published = article.status == ArticleStatus.PUBLISHED
    for field, value in update_data.items():
        if field == "status":
            value = ArticleStatus(value)
        setattr(article, field, value)

    if article.status == ArticleStatus.PUBLISHED and not was_published:
        article.published_at = datetime.now(timezone.utc)

    if "title" in update_data or "body" in update_data:
        if article.body.strip():
            article.embedding = embed_text(f"{article.title}\n{article.body}")

    db.commit()
    db.refresh(article)
    return article


@router.delete("/articles/{article_id}", status_code=204)
def delete_article(
    article_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.KNOWLEDGE_MANAGE)),
):
    article = _check_org(db.get(KnowledgeArticle, article_id), current_user)
    db.delete(article)
    db.commit()