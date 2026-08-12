Nexora

AI-powered customer support platform — built end-to-end as a production-grade portfolio project. Nexora combines ticket management, live chat, a knowledge base, workflow automation, and AI-assisted support tooling into a single multi-tenant SaaS platform.

🔗 Live demo: nexora-lyart-six.vercel.app 🔑 Demo login: Click "Try the live demo" on the login page, or use test@nexora.com / Nexora123!

Tech Stack

Frontend

Next.js 15 (App Router) + TypeScript
Tailwind CSS v4
Recharts (analytics visualizations)
Deployed on Vercel

Backend

FastAPI + SQLAlchemy + PostgreSQL
JWT authentication via HttpOnly cookies
Deployed on Clever Cloud

AI

Groq (Llama 3.3 70B) for AI-assisted features
Local sentence-transformers embeddings for RAG over the knowledge base

Automation

n8n for external workflow orchestration (see Integrations below)
Features
Area	What it does
Ticket Management	Full CRUD, priority/status tracking, comment threads, internal notes
Live Chat	Embeddable widget (chat-widget.js) for customer websites, polling-based real-time conversations, staff reply interface
Knowledge Base	Article authoring, tagging, publish/draft states, AI-powered "suggest articles for this ticket"
AI Workspace (RAG)	Ask-the-knowledge-base Q&A with cited sources, prompt template library, per-ticket AI insights (summary, sentiment, predicted priority, suggested tags)
Workflow Automation	Rule builder (trigger → condition → action), idle-ticket escalation, full audit logging
Customer Portal	Separate self-service portal for end customers to submit and track their own tickets
Email Integration	Inbound email → ticket creation, threading, deduplication on Message-ID
Outgoing Webhooks	HMAC-signed, with automatic retry logic and delivery logs
n8n Integration	Key-authenticated inbound endpoint for external automation (see below)
Analytics & Reporting	Dashboard metrics, ticket trend charts, priority/status breakdowns
Team & RBAC	Owner / Admin / Manager / Agent / Viewer / Customer roles, token-based invitations
CRM	Customer records with full ticket/chat history and timeline, auto-created from ticket activity
n8n + Webhook Integration

Nexora ships with a purpose-built integration surface for connecting external systems (WhatsApp, Telegram, Discord, or any webhook-capable platform) through n8n:

Inbound: External platform → n8n Webhook Trigger → n8n HTTP Request node → Nexora's key-authenticated endpoint:

POST /api/v1/integrations/incoming/create-ticket
Header: X-Nexora-Webhook-Key: <key generated in Settings → Integrations>

This automatically creates a ticket, tagged with its originating source, and emits an event that feeds the live Analytics dashboard.

Outbound: Nexora emits HMAC-signed webhooks on events like ticket_created and ticket_status_changed, which n8n (or any subscriber) can consume to trigger notifications, sync to a CRM, or chain further automation.

This architecture keeps platform-specific integration logic (WhatsApp Business API, Telegram Bot API, etc.) out of Nexora's core codebase — n8n handles the messy per-platform webhook shapes, and Nexora exposes one clean, secure, authenticated endpoint.

Architecture Notes

A few deliberate decisions worth calling out:

Cross-site cookie auth via middleware proxy — the frontend (Vercel) and backend (Clever Cloud) are on different domains. Rather than relying on SameSite=None cookies (unreliable across browsers due to third-party cookie restrictions), all /api/* requests are proxied through Next.js middleware to the backend, so the browser only ever talks to a single first-party origin. Cookies stay first-party and reliable across all browsers.
redirect_slashes=False + skipTrailingSlashRedirect — FastAPI's default trailing-slash redirect behavior, combined with Next.js's own URL normalization, can silently strip trailing slashes before a request reaches the backend, causing hard-to-diagnose 404s. Both layers are configured to preserve request paths exactly as sent.
Idempotent seed scripts — backend/scripts/seed_demo.py safely creates (or no-ops if already present) the demo account, designed to be run against production without risk of duplication.
Local Development
bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

Copy .env.example → .env.local (frontend) and .env.example → .env (backend) and fill in your local Postgres connection string, Groq API key, and NEXT_PUBLIC_API_URL=http://localhost:8000.

Roadmap
 Direct WhatsApp Business API / Telegram Bot API integration (currently demonstrated via n8n + simulated webhook payloads)
 Autonomous AI ticket resolution — confidence-gated auto-reply for simple, KB-answerable questions, with automatic escalation to a human agent for anything else
 Customer notification triggers on ticket status change (email/webhook)
 Public marketing/landing page showcasing the live chat widget in context
Screenshots

(add dashboard, ticket view, AI panel, and analytics screenshots here)