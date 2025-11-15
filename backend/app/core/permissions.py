"""
Role-Based Access Control (RBAC) system
Defines permissions and role-based authorization
"""
from enum import Enum
from typing import List, Callable
from fastapi import HTTPException, status, Depends

from app.models import UserRole
from app.core.security import get_current_user


class Permission(str, Enum):
    """Permission enumeration"""

    # User permissions
    READ_PROFILE = "read:profile"
    UPDATE_PROFILE = "update:profile"
    DELETE_PROFILE = "delete:profile"

    # API Key permissions
    CREATE_API_KEY = "create:api_key"
    READ_API_KEY = "read:api_key"
    UPDATE_API_KEY = "update:api_key"
    DELETE_API_KEY = "delete:api_key"
    ROTATE_API_KEY = "rotate:api_key"

    # Webhook permissions
    CREATE_WEBHOOK = "create:webhook"
    READ_WEBHOOK = "read:webhook"
    UPDATE_WEBHOOK = "update:webhook"
    DELETE_WEBHOOK = "delete:webhook"
    TEST_WEBHOOK = "test:webhook"

    # Organization permissions
    CREATE_ORG = "create:organization"
    READ_ORG = "read:organization"
    UPDATE_ORG = "update:organization"
    DELETE_ORG = "delete:organization"
    INVITE_MEMBER = "invite:member"
    REMOVE_MEMBER = "remove:member"
    UPDATE_MEMBER_ROLE = "update:member_role"

    # Admin permissions
    READ_ALL_USERS = "read:all_users"
    UPDATE_ALL_USERS = "update:all_users"
    DELETE_ALL_USERS = "delete:all_users"
    SUSPEND_USER = "suspend:user"
    IMPERSONATE_USER = "impersonate:user"

    # Billing permissions
    MANAGE_BILLING = "manage:billing"
    VIEW_INVOICES = "view:invoices"
    PURCHASE_CREDITS = "purchase:credits"
    MANAGE_SUBSCRIPTION = "manage:subscription"

    # Analytics permissions
    VIEW_ANALYTICS = "view:analytics"
    VIEW_SYSTEM_ANALYTICS = "view:system_analytics"
    EXPORT_ANALYTICS = "export:analytics"

    # System permissions
    MANAGE_SYSTEM = "manage:system"
    VIEW_AUDIT_LOGS = "view:audit_logs"
    MANAGE_SYSTEM_CONFIG = "manage:system_config"
    BROADCAST_MESSAGE = "broadcast:message"
    MAINTENANCE_MODE = "maintenance:mode"


# Role-Permission Mapping
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: [p.value for p in Permission],

    UserRole.ADMIN: [
        # Profile
        Permission.READ_PROFILE,
        Permission.UPDATE_PROFILE,

        # API Keys
        Permission.CREATE_API_KEY,
        Permission.READ_API_KEY,
        Permission.UPDATE_API_KEY,
        Permission.DELETE_API_KEY,
        Permission.ROTATE_API_KEY,

        # Webhooks
        Permission.CREATE_WEBHOOK,
        Permission.READ_WEBHOOK,
        Permission.UPDATE_WEBHOOK,
        Permission.DELETE_WEBHOOK,
        Permission.TEST_WEBHOOK,

        # Organizations
        Permission.CREATE_ORG,
        Permission.READ_ORG,
        Permission.UPDATE_ORG,
        Permission.INVITE_MEMBER,
        Permission.REMOVE_MEMBER,
        Permission.UPDATE_MEMBER_ROLE,

        # Users (limited)
        Permission.READ_ALL_USERS,
        Permission.UPDATE_ALL_USERS,

        # Billing
        Permission.MANAGE_BILLING,
        Permission.VIEW_INVOICES,
        Permission.PURCHASE_CREDITS,
        Permission.MANAGE_SUBSCRIPTION,

        # Analytics
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_ANALYTICS,

        # System (limited)
        Permission.VIEW_AUDIT_LOGS,
    ],

    UserRole.USER: [
        # Profile
        Permission.READ_PROFILE,
        Permission.UPDATE_PROFILE,

        # API Keys
        Permission.CREATE_API_KEY,
        Permission.READ_API_KEY,
        Permission.UPDATE_API_KEY,
        Permission.DELETE_API_KEY,
        Permission.ROTATE_API_KEY,

        # Webhooks
        Permission.CREATE_WEBHOOK,
        Permission.READ_WEBHOOK,
        Permission.UPDATE_WEBHOOK,
        Permission.DELETE_WEBHOOK,
        Permission.TEST_WEBHOOK,

        # Organizations
        Permission.CREATE_ORG,
        Permission.READ_ORG,

        # Billing
        Permission.VIEW_INVOICES,
        Permission.PURCHASE_CREDITS,
        Permission.MANAGE_SUBSCRIPTION,

        # Analytics
        Permission.VIEW_ANALYTICS,
    ],

    UserRole.VIEWER: [
        # Profile
        Permission.READ_PROFILE,

        # API Keys (read only)
        Permission.READ_API_KEY,

        # Webhooks (read only)
        Permission.READ_WEBHOOK,

        # Organizations (read only)
        Permission.READ_ORG,

        # Analytics (read only)
        Permission.VIEW_ANALYTICS,
    ],
}


def check_permission(user_role: UserRole, required_permission: Permission) -> bool:
    """Check if a role has a specific permission"""
    return required_permission.value in ROLE_PERMISSIONS.get(user_role, [])


def check_permissions(user_role: UserRole, required_permissions: List[Permission]) -> bool:
    """Check if a role has all required permissions"""
    role_perms = ROLE_PERMISSIONS.get(user_role, [])
    return all(perm.value in role_perms for perm in required_permissions)


def require_permission(permission: Permission) -> Callable:
    """
    Dependency to require a specific permission

    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            current_user = Depends(require_permission(Permission.READ_ALL_USERS))
        ):
            ...
    """
    async def permission_dependency(current_user = Depends(get_current_user)):
        if not check_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required"
            )
        return current_user

    return permission_dependency


def require_permissions(permissions: List[Permission]) -> Callable:
    """
    Dependency to require multiple permissions (AND logic)

    Usage:
        @router.delete("/critical")
        async def critical_endpoint(
            current_user = Depends(require_permissions([
                Permission.DELETE_ALL_USERS,
                Permission.MANAGE_SYSTEM
            ]))
        ):
            ...
    """
    async def permissions_dependency(current_user = Depends(get_current_user)):
        if not check_permissions(current_user.role, permissions):
            missing = [
                p.value for p in permissions
                if not check_permission(current_user.role, p)
            ]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissions denied: {', '.join(missing)} required"
            )
        return current_user

    return permissions_dependency


def require_role(role: UserRole) -> Callable:
    """
    Dependency to require a specific role

    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            current_user = Depends(require_role(UserRole.ADMIN))
        ):
            ...
    """
    async def role_dependency(current_user = Depends(get_current_user)):
        if current_user.role != role and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {role.value} required"
            )
        return current_user

    return role_dependency


def require_roles(roles: List[UserRole]) -> Callable:
    """
    Dependency to require one of multiple roles (OR logic)

    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            current_user = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
        ):
            ...
    """
    async def roles_dependency(current_user = Depends(get_current_user)):
        if current_user.role not in roles and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join([r.value for r in roles])}"
            )
        return current_user

    return roles_dependency


def is_admin(current_user) -> bool:
    """Check if user is an admin"""
    return current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]


def is_super_admin(current_user) -> bool:
    """Check if user is a super admin"""
    return current_user.role == UserRole.SUPER_ADMIN


# Organization-specific permissions

async def require_org_permission(
    organization_id: int,
    required_roles: List[str] = None
):
    """
    Check if user has permission in an organization

    Usage:
        org_member = await require_org_permission(org_id, ["owner", "admin"])
    """
    from app.services.organization_service import OrganizationService
    from app.database import get_db

    if required_roles is None:
        required_roles = ["owner", "admin", "member"]

    async def org_permission_dependency(
        current_user = Depends(get_current_user),
        db = Depends(get_db)
    ):
        # Super admins have access to everything
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        # Check organization membership
        member = await OrganizationService.get_member(
            db,
            organization_id=organization_id,
            user_id=current_user.id
        )

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this organization"
            )

        if member.role.value not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Organization role required: {', '.join(required_roles)}"
            )

        return member

    return org_permission_dependency
