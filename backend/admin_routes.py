from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from bson import ObjectId

from models import User, Role, Permission
from schemas import UserResponse, UserCreate, UserUpdate, RoleResponse, RoleCreate, RoleUpdate
from auth_dependencies import require_admin, get_current_active_user
from auth_utils import get_password_hash, check_password_strength
from user_utils import user_to_dict

router = APIRouter(prefix="/admin", tags=["user-management"])

# User Management Endpoints
@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_admin)
):
    """Get all users (admin only)."""
    query = User.find()
    
    if search:
        query = query.find(
            (User.username.contains(search)) | (User.email.contains(search))
        )
    
    users = await query.skip(skip).limit(limit).to_list()
    return [user_to_dict(user) for user in users]

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin)
):
    """Get a specific user by ID (admin only)."""
    try:
        user = await User.find_one(User.id == ObjectId(user_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user_to_dict(user)

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin)
):
    """Create a new user (admin only)."""
    # Check if username already exists
    existing_user = await User.find_one(User.username == user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    existing_user = await User.find_one(User.email == user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
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
        phone=user_data.phone,
        is_active=True,
        is_verified=True  # Admin-created users are auto-verified
    )
    
    # Assign default role
    default_role = await Role.find_one(Role.name == "user")
    if default_role:
        user.role_ids.append(default_role.id)
    
    await user.insert()
    return user_to_dict(user)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin)
):
    """Update a user (admin only)."""
    try:
        user = await User.find_one(User.id == ObjectId(user_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if user_data.username is not None:
        # Check if new username already exists
        existing_user = await User.find_one(
            User.username == user_data.username,
            User.id != ObjectId(user_id)
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        user.username = user_data.username
    
    if user_data.email is not None:
        # Check if new email already exists
        existing_user = await User.find_one(
            User.email == user_data.email,
            User.id != ObjectId(user_id)
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        user.email = user_data.email
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    if user_data.is_verified is not None:
        user.is_verified = user_data.is_verified
    
    await user.save()
    return user_to_dict(user)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin)
):
    """Delete a user (admin only)."""
    try:
        user = await User.find_one(User.id == ObjectId(user_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Prevent admin from deleting themselves
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await user.delete()
    return {"message": "User deleted successfully"}

# Role Management Endpoints
@router.get("/roles", response_model=List[RoleResponse])
async def get_roles(current_user: User = Depends(require_admin)):
    """Get all roles (admin only)."""
    roles = await Role.find_all().to_list()
    return roles

@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_admin)
):
    """Create a new role (admin only)."""
    # Check if role name already exists
    existing_role = await Role.find_one(Role.name == role_data.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists"
        )
    
    role = Role(
        name=role_data.name,
        description=role_data.description
    )
    
    await role.insert()
    return role

@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: User = Depends(require_admin)
):
    """Update a role (admin only)."""
    try:
        role = await Role.find_one(Role.id == ObjectId(role_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID format"
        )
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Prevent modification of default roles
    if role.name in ["admin", "user", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify default roles"
        )
    
    if role_data.name is not None:
        # Check if new name already exists
        existing_role = await Role.find_one(
            Role.name == role_data.name,
            Role.id != ObjectId(role_id)
        )
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name already exists"
            )
        role.name = role_data.name
    
    if role_data.description is not None:
        role.description = role_data.description
    
    await role.save()
    return role

@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    current_user: User = Depends(require_admin)
):
    """Delete a role (admin only)."""
    try:
        role = await Role.find_one(Role.id == ObjectId(role_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role ID format"
        )
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Prevent deletion of default roles
    if role.name in ["admin", "user", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default roles"
        )
    
    # Check if role is assigned to any users
    users_with_role = await User.find(User.role_ids == ObjectId(role_id)).to_list()
    if users_with_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete role that is assigned to users"
        )
    
    await role.delete()
    return {"message": "Role deleted successfully"}

# User-Role Assignment Endpoints
@router.post("/users/{user_id}/roles/{role_id}")
async def assign_role_to_user(
    user_id: str,
    role_id: str,
    current_user: User = Depends(require_admin)
):
    """Assign a role to a user (admin only)."""
    try:
        user = await User.find_one(User.id == ObjectId(user_id))
        role = await Role.find_one(Role.id == ObjectId(role_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user or role ID format"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if user already has this role
    if ObjectId(role_id) in user.role_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this role"
        )
    
    user.role_ids.append(ObjectId(role_id))
    await user.save()
    
    return {"message": f"Role '{role.name}' assigned to user '{user.username}'"}

@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    current_user: User = Depends(require_admin)
):
    """Remove a role from a user (admin only)."""
    try:
        user = await User.find_one(User.id == ObjectId(user_id))
        role = await Role.find_one(Role.id == ObjectId(role_id))
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user or role ID format"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Prevent removing admin role from the last admin
    if role.name == "admin":
        admin_users = await User.find(User.role_ids == ObjectId(role_id)).to_list()
        if len(admin_users) == 1 and user in admin_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove admin role from the last admin user"
            )
    
    # Check if user has this role
    if ObjectId(role_id) not in user.role_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have this role"
        )
    
    user.role_ids.remove(ObjectId(role_id))
    await user.save()
    
    return {"message": f"Role '{role.name}' removed from user '{user.username}'"}
