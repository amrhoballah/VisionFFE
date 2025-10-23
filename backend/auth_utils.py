from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from auth_config import auth_settings
import secrets

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=auth_settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, auth_settings.secret_key, algorithm=auth_settings.algorithm)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=auth_settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, auth_settings.secret_key, algorithm=auth_settings.algorithm)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, auth_settings.secret_key, algorithms=[auth_settings.algorithm])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None

def generate_token_id() -> str:
    """Generate a unique token ID for database storage."""
    return secrets.token_urlsafe(32)

def check_password_strength(password: str) -> Dict[str, Any]:
    """Check password strength and return validation results."""
    issues = []
    
    if len(password) < auth_settings.password_min_length:
        issues.append(f"Password must be at least {auth_settings.password_min_length} characters long")
    
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one digit")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        issues.append("Password must contain at least one special character")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "strength": "strong" if len(issues) == 0 else "weak"
    }
