"""
Utility functions for converting User model to response format.
"""

from typing import Dict, Any
from models import User


def user_to_dict(user: User) -> Dict[str, Any]:
    """Convert User model to dictionary with proper ObjectId handling."""
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "firstName": user.firstName if user.firstName else "",
        "lastName": user.lastName if user.lastName else "",
        "title": user.title if user.title else "",
        "officeName": user.officeName,
        "supplierName": user.supplierName,
        "location": user.location if user.location else "",
        "phone": user.phone if user.phone else "",
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "role_ids": [str(rid) for rid in user.role_ids],
    }

