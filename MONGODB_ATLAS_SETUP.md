# MongoDB Atlas Setup Guide

## Quick Setup for VisionFFE

### Step 1: Create MongoDB Atlas Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Click "Sign Up for free"
3. Create account with email/password or Google/GitHub

### Step 2: Create a Cluster

1. Click "Create a Cluster"
2. Choose **Free Tier** (M0) for development
3. Select Cloud Provider: AWS, Google Cloud, or Azure
4. Select Region closest to you (e.g., US East for Modal)
5. Click "Create Cluster"
6. Wait 1-3 minutes for cluster to initialize

### Step 3: Set Up Network Access

**Critical for Modal deployment!**

1. In MongoDB Atlas Dashboard, go to **Network Access**
2. Click "Add IP Address"
3. For development/testing: Click "Allow Access from Anywhere" and set to `0.0.0.0/0`
   - ⚠️ **Production**: Only add specific IPs
4. Click "Confirm"

### Step 4: Create Database User

1. Go to **Database Access**
2. Click "Add New Database User"
3. Enter username: `visionffe_user` (or your choice)
4. Choose **Password** authentication
5. Generate a strong password (save it!)
6. Database User Privileges: **Atlas Admin**
7. Click "Add User"

### Step 5: Get Connection String

1. Go to **Clusters** → Click your cluster name
2. Click "Connect"
3. Choose "Connect your application"
4. Select **Python** and **3.6 or later**
5. Copy the connection string

**Example connection string:**
```
mongodb+srv://visionffe_user:PASSWORD@cluster0.mongodb.net/visionffe_auth?retryWrites=true&w=majority
```

### Step 6: Configure Your Application

**Local Development:**
1. Create `.env` file in backend directory
2. Add your connection string:
   ```
   MONGODB_URL=mongodb+srv://visionffe_user:YOUR_PASSWORD@cluster0.mongodb.net/visionffe_auth?retryWrites=true&w=majority
   MONGODB_DATABASE=visionffe_auth
   JWT_SECRET_KEY=your-super-secret-key-here
   ```

**Modal Deployment:**
1. Create Modal secret:
   ```bash
   modal secret create auth-secrets \
     MONGODB_URL='mongodb+srv://visionffe_user:YOUR_PASSWORD@cluster0.mongodb.net/visionffe_auth?retryWrites=true&w=majority' \
     MONGODB_DATABASE=visionffe_auth \
     JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   ```

## Connection String Format

### MongoDB Atlas (SRV)
```
mongodb+srv://username:password@cluster.mongodb.net/database
```

✅ Use this for MongoDB Atlas
- Automatically handles replica sets
- Uses SRV records for connection
- Supports encryption by default

### Local MongoDB
```
mongodb://localhost:27017
```

✅ Use this for local development

## URL Encoding Special Characters

If your password contains special characters, you must URL-encode them:

| Character | Encoded |
|-----------|---------|
| ! | %21 |
| @ | %40 |
| # | %23 |
| $ | %24 |
| % | %25 |
| & | %26 |
| = | %3D |
| ? | %3F |
| : | %3A |

**Example:**
- Password: `pass@word123!`
- Encoded: `pass%40word123%21`
- URL: `mongodb+srv://user:pass%40word123%21@cluster.mongodb.net/db`

## Troubleshooting

### Connection Refused
**Problem:** `Connection refused`
**Solution:**
1. Check cluster is running (not paused)
2. Check IP whitelist includes your IP
3. Verify username/password are correct

### SSL Certificate Error
**Problem:** `[SSL: TLSV1_ALERT_INTERNAL_ERROR]`
**Solution:**
1. Ensure `certifi` package is installed: `pip install certifi`
2. Update requirements.txt to include `certifi`
3. Verify connection string uses `mongodb+srv://` not `mongodb://`

### IP Whitelist Timeout
**Problem:** Connection times out or hangs
**Solution:**
1. Add `0.0.0.0/0` to IP whitelist temporarily
2. Or add Modal's IP range: `0.0.0.0/0`
3. In production, restrict to specific IPs

### Wrong Connection String
**Problem:** `Failed to initialize MongoDB`
**Solution:**
- Make sure you're using the MongoDB Atlas connection string
- Format: `mongodb+srv://username:password@cluster.mongodb.net/database`
- Not the SSH string or other connection types

## Best Practices

### Development
- Use M0 (free) tier for testing
- Allow all IPs: `0.0.0.0/0`
- Use weak passwords for development

### Production
- Use M2+ (paid) tier for production
- Restrict IP whitelist to only needed IPs
- Use strong passwords
- Enable two-factor authentication
- Set up backup
- Use encryption at rest and in transit

## Commands to Test Connection

### Python Test
```bash
python -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import certifi

async def test():
    url = 'mongodb+srv://user:pass@cluster.mongodb.net/db'
    client = AsyncIOMotorClient(url, ssl_ca_certs=certifi.where())
    result = await client.admin.command('ping')
    print('✅ Connected:', result)

asyncio.run(test())
"
```

### Using mongosh (MongoDB shell)
```bash
mongosh "mongodb+srv://username:password@cluster.mongodb.net/database"
```

## VisionFFE Database Schema

Your MongoDB Atlas cluster will have:

```
visionffe_auth (database)
├── users (collection)
├── roles (collection)
├── permissions (collection)
└── tokens (collection)
```

Automatically created on first run by `init_default_data()`.

## Cost Estimation

**Free Tier (M0):**
- 512 MB storage
- Shared resources
- Perfect for development/testing
- Cost: $0/month

**M2 Tier:**
- 2 GB storage
- Dedicated resources
- Good for small production
- Cost: ~$15/month

**M10+ Tier:**
- 10+ GB storage
- Full production features
- Recommended for production
- Cost: ~$57+/month

Start with M0 for development, upgrade to M2+ for production.

## Next Steps

1. Create MongoDB Atlas cluster
2. Add IP whitelist
3. Create database user
4. Get connection string
5. Set MONGODB_URL environment variable
6. Test connection locally: `python main.py`
7. Deploy to Modal: `modal deploy modal_deploy.py`

Your VisionFFE backend is now ready with MongoDB Atlas! 🚀
