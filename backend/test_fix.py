#!/usr/bin/env python
"""
Test script to verify Pydantic v2 compatibility fixes
"""
import sys
from datetime import datetime

print("🧪 Testing Pydantic v2 Compatibility Fixes...\n")

# Test 1: Import models
print("1️⃣  Testing model imports...")
try:
    from models import User, Role, Permission, Token
    print("   ✅ Models imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import models: {e}")
    sys.exit(1)

# Test 2: Import schemas
print("2️⃣  Testing schema imports...")
try:
    from schemas import (
        UserResponse, UserCreate, LoginRequest, TokenResponse,
        RoleResponse, PermissionResponse, PasswordChangeRequest
    )
    print("   ✅ Schemas imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import schemas: {e}")
    sys.exit(1)

# Test 3: Validate user schema
print("3️⃣  Testing UserCreate schema validation...")
try:
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="SecurePass123!"
    )
    print(f"   ✅ UserCreate validation passed: {user_data.username}")
except Exception as e:
    print(f"   ❌ UserCreate validation failed: {e}")
    sys.exit(1)

# Test 4: Validate login schema
print("4️⃣  Testing LoginRequest schema validation...")
try:
    login_data = LoginRequest(
        username="testuser",
        password="SecurePass123!"
    )
    print(f"   ✅ LoginRequest validation passed: {login_data.username}")
except Exception as e:
    print(f"   ❌ LoginRequest validation failed: {e}")
    sys.exit(1)

# Test 5: Validate token response schema
print("5️⃣  Testing TokenResponse schema validation...")
try:
    token_data = TokenResponse(
        access_token="test_token_123",
        refresh_token="refresh_token_123",
        token_type="bearer",
        expires_in=1800
    )
    print(f"   ✅ TokenResponse validation passed")
except Exception as e:
    print(f"   ❌ TokenResponse validation failed: {e}")
    sys.exit(1)

# Test 6: Validate password schema
print("6️⃣  Testing PasswordChangeRequest schema validation...")
try:
    password_data = PasswordChangeRequest(
        current_password="OldPass123!",
        new_password="NewPass456!"
    )
    print(f"   ✅ PasswordChangeRequest validation passed")
except Exception as e:
    print(f"   ❌ PasswordChangeRequest validation failed: {e}")
    sys.exit(1)

# Test 7: Validate config
print("7️⃣  Testing auth config loading...")
try:
    from auth_config import auth_settings
    print(f"   ✅ Auth config loaded: {auth_settings.mongodb_database}")
except Exception as e:
    print(f"   ❌ Failed to load auth config: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("🎉 All tests passed! Pydantic v2 is working correctly!")
print("="*50 + "\n")
print("Your backend is ready for deployment. Try running:")
print("  python main.py")
