from typing import List, Optional
from fastapi import HTTPException, Depends, Request
from backend.services.token_utils import verify_token
from backend.models.user import User
from beanie import PydanticObjectId
import logging

logger = logging.getLogger('service.admin_rbac')

# Admin role hierarchy
ADMIN_ROLES = {
    "super_admin": 4,
    "admin": 3,
    "moderator": 2,
    "finance_admin": 2,
    "read_only": 1
}

# Permission mappings
PERMISSIONS = {
    "super_admin": ["*"],  # All permissions
    "admin": [
        "users.view", "users.ban", "users.suspend", "users.edit",
        "analytics.view", "analytics.export",
        "moderation.view", "moderation.action",
        "security.view", "security.action",
        "payouts.view", "payouts.approve",
        "system.view"
    ],
    "moderator": [
        "users.view",
        "moderation.view", "moderation.action",
        "analytics.view"
    ],
    "finance_admin": [
        "users.view",
        "payouts.view", "payouts.approve",
        "analytics.view", "analytics.export"
    ],
    "read_only": [
        "users.view",
        "analytics.view",
        "moderation.view",
        "security.view",
        "payouts.view"
    ]
}

class AdminRBACService:
    """Role-Based Access Control for admin users"""
    
    @staticmethod
    def has_permission(role: str, permission: str) -> bool:
        """Check if role has specific permission"""
        if role not in PERMISSIONS:
            return False
        
        role_permissions = PERMISSIONS[role]
        
        # Super admin has all permissions
        if "*" in role_permissions:
            return True
        
        # Check exact permission or wildcard
        if permission in role_permissions:
            return True
        
        # Check wildcard permissions (e.g., "users.*" matches "users.ban")
        permission_parts = permission.split(".")
        for perm in role_permissions:
            if perm.endswith(".*"):
                if permission.startswith(perm[:-2]):
                    return True
        
        return False
    
    @staticmethod
    def require_permission(permission: str):
        """Decorator to require specific permission"""
        async def dependency(request: Request, admin_user = Depends(get_admin_user)):
            if not AdminRBACService.has_permission(admin_user.role, permission):
                logger.warning(
                    f"Permission denied: {admin_user.email} tried to access {permission}",
                    extra={
                        "event": "permission_denied",
                        "admin_user_id": str(admin_user.id),
                        "permission": permission,
                        "role": admin_user.role
                    }
                )
                raise HTTPException(status_code=403, detail=f"Permission denied: {permission} required")
            return admin_user
        return dependency
    
    @staticmethod
    def require_role(required_roles: List[str]):
        """Decorator to require specific role(s)"""
        async def dependency(admin_user = Depends(get_admin_user)):
            if admin_user.role not in required_roles:
                logger.warning(
                    f"Role denied: {admin_user.email} with role {admin_user.role} tried to access {required_roles}",
                    extra={
                        "event": "role_denied",
                        "admin_user_id": str(admin_user.id),
                        "required_roles": required_roles,
                        "actual_role": admin_user.role
                    }
                )
                raise HTTPException(status_code=403, detail="Insufficient role privileges")
            return admin_user
        return dependency


async def get_admin_user(request: Request) -> User:
    """Get current admin user from JWT token"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.replace("Bearer ", "")
    
    try:
        payload = verify_token(token, "access")
        user_id = payload.get("sub")
        role = payload.get("role")
        
        # Check if user has admin role
        if role not in ADMIN_ROLES:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        user = await User.get(PydanticObjectId(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin authentication failed: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication failed")