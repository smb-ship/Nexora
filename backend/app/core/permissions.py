import enum
from fastapi import Depends, HTTPException
from app.models.user import User, UserRole
from app.api.deps import get_current_user


class Permission(str, enum.Enum):
    TICKET_CREATE = "ticket:create"
    TICKET_UPDATE_STATUS = "ticket:update_status"
    TICKET_UPDATE_PRIORITY = "ticket:update_priority"
    TICKET_ASSIGN = "ticket:assign"
    TICKET_DELETE = "ticket:delete"
    TICKET_COMMENT = "ticket:comment"
    TICKET_INTERNAL_NOTE = "ticket:internal_note"
    TICKET_AI_USE = "ticket:ai_use"
    TEAM_MANAGE = "team:manage"
    TEAM_INVITE = "team:invite"
    TEAM_ROLE_MANAGE = "team:role_manage"
    TEAM_MEMBER_REMOVE = "team:member_remove"
    WORKFLOW_MANAGE = "workflow:manage"
    CUSTOMER_MANAGE = "customer:manage"
    KNOWLEDGE_MANAGE = "knowledge:manage"


_ALL_TICKET_PERMS = {
    Permission.TICKET_CREATE, Permission.TICKET_UPDATE_STATUS, Permission.TICKET_UPDATE_PRIORITY,
    Permission.TICKET_ASSIGN, Permission.TICKET_DELETE, Permission.TICKET_COMMENT,
    Permission.TICKET_INTERNAL_NOTE, Permission.TICKET_AI_USE,
}
_ALL_TEAM_PERMS = {
    Permission.TEAM_MANAGE, Permission.TEAM_INVITE, Permission.TEAM_ROLE_MANAGE, Permission.TEAM_MEMBER_REMOVE,
}
_ALL_WORKFLOW_PERMS = {
    Permission.WORKFLOW_MANAGE,
}

ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.OWNER: _ALL_TICKET_PERMS | _ALL_TEAM_PERMS | _ALL_WORKFLOW_PERMS | {Permission.CUSTOMER_MANAGE, Permission.KNOWLEDGE_MANAGE},
    UserRole.ADMIN: _ALL_TICKET_PERMS | _ALL_TEAM_PERMS | _ALL_WORKFLOW_PERMS | {Permission.CUSTOMER_MANAGE, Permission.KNOWLEDGE_MANAGE},
    UserRole.MANAGER: {
        Permission.TICKET_CREATE, Permission.TICKET_UPDATE_STATUS, Permission.TICKET_UPDATE_PRIORITY,
        Permission.TICKET_ASSIGN, Permission.TICKET_COMMENT, Permission.TICKET_INTERNAL_NOTE,
        Permission.TICKET_AI_USE, Permission.TEAM_MANAGE, Permission.TEAM_INVITE,
        Permission.WORKFLOW_MANAGE, Permission.CUSTOMER_MANAGE, Permission.KNOWLEDGE_MANAGE,
    },
    UserRole.AGENT: {
        # Agents get CUSTOMER_MANAGE too: onboarding a caller's account while
        # logging a phone/email ticket on their behalf is routine front-line
        # support work, not an admin action. Agents can VIEW/search knowledge
        # articles (no permission gate on those endpoints — any authenticated
        # staff member can read them) but cannot create/edit/delete them,
        # hence no KNOWLEDGE_MANAGE here.
        Permission.TICKET_CREATE, Permission.TICKET_UPDATE_STATUS, Permission.TICKET_UPDATE_PRIORITY,
        Permission.TICKET_ASSIGN, Permission.TICKET_COMMENT, Permission.TICKET_INTERNAL_NOTE,
        Permission.TICKET_AI_USE, Permission.CUSTOMER_MANAGE,
    },
    UserRole.VIEWER: set(),
    UserRole.CUSTOMER: set(),
}


def require_permission(permission: Permission):
    """FastAPI dependency factory — use as Depends(require_permission(Permission.X))."""
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if permission not in ROLE_PERMISSIONS.get(current_user.role, set()):
            raise HTTPException(status_code=403, detail="You don't have permission to perform this action")
        return current_user
    return checker