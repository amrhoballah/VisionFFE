from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from models import User, Role, Permission, Token
from auth_utils import verify_token
from auth_config import auth_settings

# Security scheme
security = HTTPBearer()

class AuthError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class PermissionError(HTTPException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get the current authenticated user."""
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token, "access")
    if not payload:
        raise AuthError("Invalid token")
    
    # Check if token is revoked
    db_token = await Token.find_one(
        Token.token == token,
        Token.is_revoked == False
    )
    
    if not db_token:
        raise AuthError("Token has been revoked")
    
    # Check if token is expired
    if db_token.expires_at < datetime.utcnow():
        raise AuthError("Token has expired")
    
    # Get user
    user = await User.find_one(User.id == ObjectId(payload.get("sub")))
    if not user:
        raise AuthError("User not found")
    
    if not user.is_active:
        raise AuthError("User account is deactivated")
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise AuthError("User account is deactivated")
    return current_user

async def get_current_verified_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get the current verified user."""
    if not current_user.is_verified:
        raise AuthError("User account is not verified")
    return current_user

async def get_user_roles_and_permissions(user: User) -> tuple[List[Role], List[Permission]]:
    """Get user's roles and their permissions."""
    if not user.role_ids:
        return [], []
    
    # Get user's roles
    roles = await Role.find(Role.id.in_(user.role_ids)).to_list()
    
    # Get all permissions for these roles
    permission_ids = []
    for role in roles:
        permission_ids.extend(role.permission_ids)
    
    if not permission_ids:
        return roles, []
    
    permissions = await Permission.find(Permission.id.in_(permission_ids)).to_list()
    return roles, permissions

def require_permission(resource: str, action: str):
    """Decorator to require specific permission."""
    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # Get user's roles and permissions
        roles, permissions = await get_user_roles_and_permissions(current_user)
        
        # Check if user has admin role (full access)
        admin_role = any(role.name == "admin" for role in roles)
        if admin_role:
            return current_user
        
        # Check specific permission
        has_permission = False
        for permission in permissions:
            if (permission.resource == resource or permission.resource == "*") and \
               (permission.action == action or permission.action == "*"):
                has_permission = True
                break
        
        if not has_permission:
            raise PermissionError(f"Permission required: {action} on {resource}")
        
        return current_user
    
    return permission_checker

def require_role(role_name: str):
    """Decorator to require specific role."""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        roles, _ = await get_user_roles_and_permissions(current_user)
        has_role = any(role.name == role_name for role in roles)
        if not has_role:
            raise PermissionError(f"Role required: {role_name}")
        return current_user
    
    return role_checker

async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin role."""
    roles, _ = await get_user_roles_and_permissions(current_user)
    admin_role = any(role.name == "admin" for role in roles)
    if not admin_role:
        raise PermissionError("Admin role required")
    return current_user

# Common permission dependencies
require_search_permission = require_permission("images", "read")
require_upload_permission = require_permission("images", "write")
require_stats_permission = require_permission("stats", "read")
