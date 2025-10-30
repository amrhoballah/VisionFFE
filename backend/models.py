from beanie import Document, Indexed
from pydantic import Field, EmailStr, ConfigDict, model_serializer
from typing import List, Optional, Annotated
from datetime import datetime
from bson import ObjectId

class User(Document):
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    firstName: Optional[str] = ""  # Legacy support: empty string default
    lastName: Optional[str] = ""  # Legacy support: empty string default
    title: Optional[str] = ""  # Legacy support: empty string default (Office, Freelancer, or Supplier)
    officeName: Optional[str] = None  # Only for Office title
    supplierName: Optional[str] = None  # Only for Supplier title
    location: Optional[str] = ""  # Legacy support: empty string default (Country)
    phone: Optional[str] = ""  # Legacy support: empty string default (Full phone number with country code)
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    role_ids: List[ObjectId] = Field(default_factory=list)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def model_dump(self, **kwargs):
        """Override to convert ObjectIds to strings"""
        data = super().model_dump(**kwargs)
        # Convert ObjectId fields to strings for API response
        if 'id' in data and isinstance(data['id'], ObjectId):
            data['id'] = str(data['id'])
        if 'role_ids' in data:
            data['role_ids'] = [str(rid) if isinstance(rid, ObjectId) else rid for rid in data['role_ids']]
        return data
    
    class Settings:
        name = "users"
        indexes = [
            "username",
            "email",
            "is_active",
            "is_verified"
        ]

class Role(Document):
    name: Indexed(str, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    permission_ids: List[ObjectId] = Field(default_factory=list)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    class Settings:
        name = "roles"
        indexes = [
            "name"
        ]

class Permission(Document):
    name: Indexed(str, unique=True)
    description: Optional[str] = None
    resource: str
    action: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    class Settings:
        name = "permissions"
        indexes = [
            "name",
            "resource",
            "action"
        ]

class Token(Document):
    token: Indexed(str, unique=True)
    token_type: str = "bearer"  # "access" or "refresh"
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: ObjectId
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    class Settings:
        name = "tokens"
        indexes = [
            "token",
            "user_id",
            "is_revoked",
            "expires_at"
        ]

class Project(Document):
    name: Indexed(str)
    user_id: ObjectId
    photo_urls: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    class Settings:
        name = "projects"
        indexes = [
            "user_id",
            "name"
        ]
