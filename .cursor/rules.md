# Nexora Project Rules

You are working on Nexora, a production-quality AI-powered customer support platform.

## General Principles

- Write production-ready code.
- Prefer readability over cleverness.
- Keep components small and reusable.
- Follow SOLID principles.
- Never duplicate logic unnecessarily.
- Always use TypeScript with strict typing.
- Avoid using `any` unless there is a clear reason.

## Frontend

- Framework: Next.js 15 App Router
- Language: TypeScript
- Styling: Tailwind CSS v4
- Components: Base UI
- Icons: Lucide React

### Rules

- Prefer Server Components.
- Use Client Components only when necessary.
- Use async Server Components for data fetching.
- Keep pages minimal.
- Put reusable UI inside `components/`.
- Use proper loading and error states.
- Build accessible interfaces.

## Backend

- FastAPI
- SQLAlchemy 2.0
- Alembic
- Pydantic v2

### Rules

- Keep API routes thin.
- Put business logic inside services.
- Validate all request data.
- Return consistent API responses.

## Database

- Write efficient SQLAlchemy queries.
- Avoid N+1 queries.
- Use relationships correctly.
- Write migrations using Alembic.

## UI

- Modern SaaS design.
- Responsive layouts.
- Consistent spacing.
- Smooth animations.
- Accessible color contrast.

## Code Style

- Prefer descriptive names.
- Keep functions short.
- Avoid deeply nested code.
- Use existing utilities before creating new ones.

Always build solutions as if they will be used in production.