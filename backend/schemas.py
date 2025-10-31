from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    firstName: Optional[str] = ""  # Legacy support
    lastName: Optional[str] = ""  # Legacy support
    title: Optional[str] = ""  # Legacy support: Office, Freelancer, or Supplier
    officeName: Optional[str] = None  # Only for Office title
    supplierName: Optional[str] = None  # Only for Supplier title
    location: Optional[str] = ""  # Legacy support: Country
    phone: Optional[str] = ""  # Legacy support: Full phone number with country code

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    title: Optional[str] = None
    officeName: Optional[str] = None
    supplierName: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserResponse(UserBase):
    id: str  # MongoDB ObjectId as string
    is_active: bool
    is_verified: bool
    created_at: datetime
    role_ids: List[str] = []  # MongoDB ObjectIds as strings
    
    model_config = ConfigDict(from_attributes=True)

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
    
    model_config = ConfigDict(from_attributes=True)

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
    
    model_config = ConfigDict(from_attributes=True)

# Project schemas
class ProjectBase(BaseModel):
    name: str

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: str
    user_id: str
    photo_urls: List[str] = []
    extracted_items: List[dict] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

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
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# Update forward references
UserResponse.model_rebuild()
UserWithRoles.model_rebuild()
RoleResponse.model_rebuild()
PermissionResponse.model_rebuild()
