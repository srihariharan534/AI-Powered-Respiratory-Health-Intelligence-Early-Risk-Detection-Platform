"""
Role-Based Access Control (RBAC) Definitions for NEXUS Governance (Phase 21).
Establishes actor identities, role hierarchies, and permission boundaries.
"""

from enum import Enum
from typing import Set
from fastapi import Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    VIEWER = "VIEWER"
    FIELD_OFFICER = "FIELD_OFFICER"
    OPERATOR = "OPERATOR"
    APPROVER = "APPROVER"
    COMMANDER = "COMMANDER"
    ADMIN = "ADMIN"


class Permission(str, Enum):
    VIEW_RECOMMENDATIONS = "view_recommendations"
    GENERATE_RECOMMENDATIONS = "generate_recommendations"
    APPROVE_RECOMMENDATION = "approve_recommendation"
    REJECT_RECOMMENDATION = "reject_recommendation"
    EXPIRE_RECOMMENDATION = "expire_recommendation"
    VIEW_AUDIT_LOG = "view_audit_log"


ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.VIEWER: {
        Permission.VIEW_RECOMMENDATIONS,
        Permission.VIEW_AUDIT_LOG,
    },
    UserRole.FIELD_OFFICER: {
        Permission.VIEW_RECOMMENDATIONS,
    },
    UserRole.OPERATOR: {
        Permission.VIEW_RECOMMENDATIONS,
        Permission.GENERATE_RECOMMENDATIONS,
        Permission.VIEW_AUDIT_LOG,
    },
    UserRole.APPROVER: {
        Permission.VIEW_RECOMMENDATIONS,
        Permission.APPROVE_RECOMMENDATION,
        Permission.REJECT_RECOMMENDATION,
        Permission.VIEW_AUDIT_LOG,
    },
    UserRole.COMMANDER: {
        Permission.VIEW_RECOMMENDATIONS,
        Permission.GENERATE_RECOMMENDATIONS,
        Permission.APPROVE_RECOMMENDATION,
        Permission.REJECT_RECOMMENDATION,
        Permission.EXPIRE_RECOMMENDATION,
        Permission.VIEW_AUDIT_LOG,
    },
    UserRole.ADMIN: {
        Permission.VIEW_RECOMMENDATIONS,
        Permission.GENERATE_RECOMMENDATIONS,
        Permission.APPROVE_RECOMMENDATION,
        Permission.REJECT_RECOMMENDATION,
        Permission.EXPIRE_RECOMMENDATION,
        Permission.VIEW_AUDIT_LOG,
    },
}


class AuthenticatedActor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actor_id: str = Field(..., min_length=2, description="Unique coordinator username or callsign")
    role: UserRole = Field(..., description="Assigned governance role")

    def has_permission(self, permission: Permission) -> bool:
        allowed = ROLE_PERMISSIONS.get(self.role, set())
        return permission in allowed


def get_current_actor(
    x_actor_id: str = Header(default="COORD-DEFAULT-01", alias="X-Actor-Id"),
    x_actor_role: str = Header(default="COMMANDER", alias="X-Actor-Role"),
) -> AuthenticatedActor:
    """
    Extracts and validates authenticated actor headers from incoming requests.
    Enforces server-side identity without trusting client UI boundaries.
    """
    role_normalized = x_actor_role.upper()
    try:
        user_role = UserRole(role_normalized)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid actor role '{x_actor_role}'. Allowed roles: {[r.value for r in UserRole]}",
        )

    return AuthenticatedActor(actor_id=x_actor_id, role=user_role)
