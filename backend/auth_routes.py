from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from typing import List
from bson import ObjectId

from models import User, Role, Token
from schemas import (
    LoginRequest, RegisterRequest, TokenResponse, RefreshTokenRequest,
    PasswordChangeRequest, UserResponse, UserCreate, UserUpdate, UserWithRoles, RoleResponse
)
from auth_utils import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    verify_token, generate_token_id, check_password_strength
)
from auth_dependencies import get_current_user, get_current_active_user, require_admin
from auth_config import auth_settings
from user_utils import user_to_dict

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: RegisterRequest):
    """Register a new user."""
    # Check if username already exists
    existing_user = await User.find_one(User.username == user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_user = await User.find_one(User.email == user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    password_check = check_password_strength(user_data.password)
    if not password_check["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(password_check['issues'])}"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        firstName=user_data.firstName,
        lastName=user_data.lastName,
        title=user_data.title,
        officeName=user_data.officeName,
        supplierName=user_data.supplierName,
        location=user_data.location,
        phone=user_data.phone
    )
    
    # Assign default role (user)
    default_role = await Role.find_one({
        "$or": [
                Role.name == "supplier",
                Role.name == "designer"
            ]
        })
    if default_role:
        user.role_ids.append(default_role.id)
    
    await user.insert()
    
    # Convert to dict and ensure ObjectIds are strings
    return user_to_dict(user)

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Login and return access and refresh tokens."""
    # Find user by username or email
    user = await User.find_one({
        "$or": [
                {"username": login_data.username},
                {"email": login_data.username}
            ]
        }
    )
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store tokens in database
    access_token_record = Token(
        token=access_token,
        token_type="access",
        expires_at=datetime.utcnow() + timedelta(minutes=auth_settings.access_token_expire_minutes),
        user_id=user.id
    )
    
    refresh_token_record = Token(
        token=refresh_token,
        token_type="refresh",
        expires_at=datetime.utcnow() + timedelta(days=auth_settings.refresh_token_expire_days),
        user_id=user.id
    )
    
    await access_token_record.insert()
    await refresh_token_record.insert()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_settings.access_token_expire_minutes * 60
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token, "refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if token exists and is not revoked
    token_record = await Token.find_one(
        Token.token == refresh_data.refresh_token,
        Token.is_revoked == False
    )
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked"
        )
    
    # Check if token is expired
    if token_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    # Get user
    user = await User.find_one(User.id == ObjectId(payload.get("sub")))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    new_access_token = create_access_token(data={"sub": str(user.id)})
    
    # Store new access token
    new_token_record = Token(
        token=new_access_token,
        token_type="access",
        expires_at=datetime.utcnow() + timedelta(minutes=auth_settings.access_token_expire_minutes),
        user_id=user.id
    )
    
    await new_token_record.insert()
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_data.refresh_token,  # Keep the same refresh token
        expires_in=auth_settings.access_token_expire_minutes * 60
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout by revoking all user tokens."""
    # Revoke all active tokens for the user
    await Token.find(Token.user_id == current_user.id, Token.is_revoked == False).update_many(
        {"$set": {"is_revoked": True}}
    )
    
    return {"message": "Successfully logged out"}

@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Change user password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    password_check = check_password_strength(password_data.new_password)
    if not password_check["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(password_check['issues'])}"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    
    # Revoke all existing tokens to force re-login
    await Token.find(Token.user_id == current_user.id, Token.is_revoked == False).update_many(
        {"$set": {"is_revoked": True}}
    )
    
    return {"message": "Password changed successfully. Please login again."}

@router.get("/me", response_model=UserWithRoles)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information with roles."""
    user_dict = user_to_dict(current_user)
    roles = []
    if current_user.role_ids:
        roles = await Role.find({"_id": {"$in": current_user.role_ids}}).to_list()
    # Map roles to RoleResponse-like dicts
    user_dict["roles"] = [
        {
            "id": str(role.id),
            "name": role.name,
            "description": role.description,
            "created_at": role.created_at,
            "permission_ids": [str(pid) for pid in role.permission_ids],
        } for role in roles
    ]
    return user_dict
