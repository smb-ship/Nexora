"""
Idempotent seed script for the demo account.
Safe to run multiple times — skips creation if the user already exists.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.main  # noqa: F401 - importing the full app registers every SQLAlchemy model, avoiding relationship resolution errors

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.core.security import hash_password

DEMO_EMAIL = "test@nexora.com"
DEMO_PASSWORD = "Nexora123!"
DEMO_ORG_NAME = "Nexora Demo"
DEMO_ORG_SLUG = "nexora-demo"


def main():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if existing:
            print(f"Demo user '{DEMO_EMAIL}' already exists (id={existing.id}). Nothing to do.")
            return

        org = db.query(Organization).filter(Organization.slug == DEMO_ORG_SLUG).first()
        if not org:
            org = Organization(name=DEMO_ORG_NAME, slug=DEMO_ORG_SLUG)
            db.add(org)
            db.flush()
            print(f"Created organization '{DEMO_ORG_NAME}' (id={org.id})")

        user = User(
            email=DEMO_EMAIL,
            full_name="Demo Owner",
            hashed_password=hash_password(DEMO_PASSWORD),
            organization_id=org.id,
            role=UserRole.OWNER,
        )
        db.add(user)
        db.commit()
        print(f"Created demo user '{DEMO_EMAIL}' (id={user.id}) in org '{DEMO_ORG_NAME}'")
        print(f"Login with: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()