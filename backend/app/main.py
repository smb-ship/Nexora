import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth
from app.api.routes import (
    invitations, organizations, teams, tickets, workflows, customer_portal, customers,
    webhooks, integrations, chat_public, chat_staff, automation_dashboard, knowledge, ai_workspace,
)
from app.api.routes import ai
from app.api.routes import analytics as analytics_router
from app.core.event_subscribers import register_subscribers

app = FastAPI(title="Nexora API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_subscribers()

app.include_router(auth.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(invitations.router, prefix="/api/v1")
app.include_router(tickets.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(customer_portal.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(analytics_router.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(integrations.router, prefix="/api/v1")
app.include_router(chat_public.router, prefix="/api/v1")
app.include_router(chat_staff.router, prefix="/api/v1")
app.include_router(automation_dashboard.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(ai_workspace.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}