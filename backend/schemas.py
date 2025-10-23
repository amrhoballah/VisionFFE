from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserResponse(UserBase):
    id: str  # MongoDB ObjectId as string
    is_active: bool
    is_verified: bool
    created_at: datetime
    role_ids: List[str] = []  # MongoDB ObjectIds as strings
    
    class Config:
        from_attributes = True

class UserWithRoles(UserResponse):
    roles: List['RoleResponse'] = []

# Role schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class RoleResponse(RoleBase):
    id: str  # MongoDB ObjectId as string
    created_at: datetime
    permission_ids: List[str] = []  # MongoDB ObjectIds as strings
    
    class Config:
        from_attributes = True

# Permission schemas
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    resource: str
    action: str

class PermissionCreate(PermissionBase):
    role_id: str  # MongoDB ObjectId as string

class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None

class PermissionResponse(PermissionBase):
    id: str  # MongoDB ObjectId as string
    created_at: datetime
    
    class Config:
        from_attributes = True

# Authentication schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(UserCreate):
    pass

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# Update forward references
UserResponse.model_rebuild()
UserWithRoles.model_rebuild()
RoleResponse.model_rebuild()
PermissionResponse.model_rebuild()
