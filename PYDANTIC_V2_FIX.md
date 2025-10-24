# Pydantic v2 Migration Fix - Bson ObjectId Issue

## Problem
You were getting the following error:
```
PydanticSchemaGenerationError: "Unable to generate pydantic-core schema for <class 'bson.objectid.ObjectId'>. 
Set `arbitrary_types_allowed=True` in the model_config to ignore this error..."
```

This error occurs because Pydantic v2 requires explicit configuration to handle non-standard types like BSON ObjectId.

## Root Causes
1. **Missing `arbitrary_types_allowed=True`** in Pydantic models that use ObjectId
2. **Deprecated `@validator` decorator** - should use `@field_validator` in Pydantic v2
3. **Old `Config` class syntax** - should use `model_config = ConfigDict(...)` in Pydantic v2
4. **Old `from_attributes` configuration** - needs to be in `ConfigDict`

## Files Fixed

### 1. `backend/models.py`
**Changes:**
- Added `from pydantic import ConfigDict` import
- Added `model_config = ConfigDict(arbitrary_types_allowed=True)` to all document models:
  - `User`
  - `Role`
  - `Permission`
  - `Token`
- Changed `role_ids: List[ObjectId] = []` to `role_ids: List[ObjectId] = Field(default_factory=list)`
- Changed `permission_ids: List[ObjectId] = []` to `permission_ids: List[ObjectId] = Field(default_factory=list)`

**Why:** The `arbitrary_types_allowed=True` config tells Pydantic to accept ObjectId types without validation. The `Field(default_factory=list)` is the proper Pydantic v2 way to handle default mutable values.

### 2. `backend/schemas.py`
**Changes:**
- Updated imports: `from pydantic import BaseModel, EmailStr, field_validator, ConfigDict`
- Removed `from bson import ObjectId` (not needed in schemas)
- Replaced all `@validator` with `@field_validator` decorators
- Added `@classmethod` decorator to validator methods
- Changed `class Config: from_attributes = True` to `model_config = ConfigDict(from_attributes=True)`

**Why:** Pydantic v2 deprecated the `@validator` decorator in favor of `@field_validator`. The `@classmethod` decorator is now required.

### 3. `backend/auth_config.py`
**Changes:**
- Added `from pydantic import ConfigDict` import
- Changed `class Config: env_file = ".env"` to `model_config = ConfigDict(env_file=".env")`

**Why:** Pydantic v2 uses `ConfigDict` for all configuration instead of the `Config` inner class.

## How to Verify the Fix

1. **Check that models load without errors:**
   ```bash
   python -c "from models import User, Role, Permission, Token; print('✅ Models loaded successfully')"
   ```

2. **Check that schemas validate:**
   ```bash
   python -c "from schemas import UserResponse, TokenResponse; print('✅ Schemas loaded successfully')"
   ```

3. **Run the backend:**
   ```bash
   python main.py
   ```

4. **Test a registration endpoint:**
   ```bash
   curl -X POST http://localhost:8080/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "email": "test@example.com", "password": "TestPass123!"}'
   ```

## What's Different in Pydantic v2

### Decorators
```python
# Pydantic v1 (deprecated)
@validator('field_name')
def validate_field(cls, v):
    return v

# Pydantic v2 (new)
@field_validator('field_name')
@classmethod
def validate_field(cls, v):
    return v
```

### Configuration
```python
# Pydantic v1 (deprecated)
class Config:
    from_attributes = True
    arbitrary_types_allowed = True

# Pydantic v2 (new)
model_config = ConfigDict(
    from_attributes=True,
    arbitrary_types_allowed=True
)
```

### Handling Custom Types
```python
# Before (would fail)
user_id: ObjectId

# After (with arbitrary_types_allowed=True)
model_config = ConfigDict(arbitrary_types_allowed=True)
user_id: ObjectId  # Now works!
```

## Next Steps

1. ✅ Models and schemas are now Pydantic v2 compatible
2. ✅ ObjectId handling is fixed
3. ✅ Ready for deployment to Modal

The error should now be resolved. Your backend is ready to deploy! 🚀
