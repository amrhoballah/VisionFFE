from beanie import Document, Indexed
from pydantic import Field, EmailStr, ConfigDict
from typing import List, Optional, Annotated
from datetime import datetime
from bson import ObjectId

class User(Document):
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    role_ids: List[ObjectId] = Field(default_factory=list)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
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
