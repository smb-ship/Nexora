from fastapi import Depends, HTTPException

from app.models.user import User, UserRole
from app.api.deps import get_current_user


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency — ensures the caller is logged in AND is a
    customer-role account. Kept deliberately separate from the staff
    Permission/ROLE_PERMISSIONS system: customer access is role-only and
    always additionally row-scoped to customer_id == current_user.id at the
    query level (see customer_portal.py) — a permission flag alone wouldn't
    express "only your own tickets," so this stays a distinct, minimal check."""
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(status_code=403, detail="This endpoint is only available to customer accounts")
    return current_user