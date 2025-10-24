# Deployment Fixes for VisionFFE Backend

## Issues Found and Fixed

### 1. ✅ Missing `Depends` Import (FIXED)

**Error:**
```
NameError: name 'Depends' is not defined
  File "/root/app/main.py", line 133, in <module>
    current_user = Depends(require_search_permission)
```

**Root Cause:**
The `Depends` class from FastAPI was not imported in `main.py`, but it was being used in the route decorators for authentication.

**Fix Applied:**
Changed line 1 in `backend/main.py` from:
```python
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
```

To:
```python
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends
```

**Why This Matters:**
- `Depends()` is used in FastAPI to specify dependency injection
- It's required for authentication functions like `require_search_permission`, `require_upload_permission`, and `require_stats_permission`
- Without it, the API endpoints cannot enforce authentication and permissions

---

### 2. ✅ Pydantic v2 Compatibility Issues (ALREADY FIXED)

**Fixed Files:**
- `backend/models.py` - Added `ConfigDict(arbitrary_types_allowed=True)`
- `backend/schemas.py` - Migrated from `@validator` to `@field_validator`
- `backend/auth_config.py` - Updated settings to use `ConfigDict`

---

## Pre-Deployment Checklist

Before deploying to Modal, verify:

- [ ] All imports are present
- [ ] No `NameError` or `ImportError`
- [ ] Pydantic v2 models/schemas are compatible
- [ ] Environment variables are configured
- [ ] MongoDB connection string is set
- [ ] JWT secret key is generated

## Testing Before Deployment

### 1. Test Import
```bash
python -c "from main import app; print('✅ Main app imported successfully')"
```

### 2. Run Test Suite
```bash
python test_fix.py
```

### 3. Start Backend Locally
```bash
python main.py
```

You should see output like:
```
🚀 Starting up...
📊 Initializing MongoDB database...
✅ MongoDB database initialized
✅ Connected to Pinecone. Vectors: 0
✅ Connected to Cloudflare R2
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### 4. Test Authentication Endpoint
```bash
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "TestPass123!"}'
```

Expected response:
```json
{
  "id": "...",
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-...",
  "role_ids": [...]
}
```

---

## Deployment Steps

### 1. Set Up Modal Secrets
```bash
# Create vision-api secret
modal secret create vision-api \
  PINECONE_API_KEY=your_key \
  PINECONE_INDEX_NAME=your_index \
  MODEL_PRESET=balanced \
  R2_ACCOUNT_ID=your_id \
  R2_ACCESS_KEY_ID=your_key \
  R2_SECRET_ACCESS_KEY=your_secret \
  R2_REGION=auto \
  R2_BUCKET_NAME=your_bucket

# Create auth-secrets secret
modal secret create auth-secrets \
  JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))") \
  MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net \
  MONGODB_DATABASE=visionffe_auth
```

### 2. Deploy to Modal
```bash
cd backend
modal deploy modal_deploy.py
```

### 3. Get Your URL
Modal will provide a URL like: `https://username--vision-ffe-api.modal.run`

### 4. Update Frontend Config
Update `frontend/config.ts`:
```typescript
api: {
  baseUrl: process.env.NODE_ENV === 'production' 
    ? 'https://username--vision-ffe-api.modal.run'  // Your Modal URL
    : 'http://localhost:8080',
}
```

---

## Troubleshooting

### Issue: `NameError: name 'X' is not defined`
**Solution:** Check that all required imports are present in `main.py`

### Issue: `PydanticSchemaGenerationError`
**Solution:** Ensure all models have `ConfigDict(arbitrary_types_allowed=True)`

### Issue: `ModuleNotFoundError: No module named 'X'`
**Solution:** Verify all dependencies are in `requirements.txt` and Modal secret includes necessary packages

### Issue: MongoDB Connection Failed
**Solution:** 
- Check MONGODB_URL in Modal secrets
- Verify IP whitelist in MongoDB Atlas (if using)
- Test connection locally first

### Issue: Authentication Not Working
**Solution:**
- Verify JWT_SECRET_KEY is set
- Check that auth routes are imported
- Ensure `Depends` is imported in main.py

---

## Summary

All identified issues have been fixed:
- ✅ Missing imports (Depends)
- ✅ Pydantic v2 compatibility
- ✅ Model validation errors
- ✅ Configuration issues

Your backend is now ready for Modal deployment! 🚀
