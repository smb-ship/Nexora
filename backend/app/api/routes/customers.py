import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.core.permissions import require_permission, Permission
from app.schemas.customer import CustomerCreate, CustomerListItem

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/", response_model=CustomerListItem, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    customer = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        organization_id=current_user.organization_id,
        role=UserRole.CUSTOMER,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/", response_model=list[CustomerListItem])
def list_customers(
    q: str | None = Query(None, description="Search name/email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.CUSTOMER_MANAGE)),
):
    stmt = select(User).where(
        User.organization_id == current_user.organization_id,
        User.role == UserRole.CUSTOMER,
    )
    if q:
        search = f"%{q}%"
        stmt = stmt.where(or_(User.email.ilike(search), User.full_name.ilike(search)))

    stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()