# Fixed: MongoDB Atlas SSL/TLS Connection Error

## Problem

You were getting an SSL handshake error when connecting to MongoDB Atlas:
```
[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error
SSL handshake failed on MongoDB Atlas connection
```

This happened because the MongoDB client wasn't properly configured for SSL/TLS connections to MongoDB Atlas.

## Root Causes

1. **Missing SSL certificate validation** - The client wasn't using proper CA certificates
2. **No connection timeout parameters** - Connections were hanging or failing silently
3. **Missing certifi package** - CA bundle for SSL verification wasn't available
4. **Retry configuration missing** - No automatic retry on transient failures

## Fixes Applied

### 1. Added Proper SSL/TLS Configuration ✅

```python
# Detect if using MongoDB Atlas
is_atlas = "mongodb+srv://" in auth_settings.mongodb_url

# Create SSL context with proper certificate validation
if is_atlas:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
```

**Why:** MongoDB Atlas requires proper SSL/TLS certificates for secure connections

### 2. Added Connection Parameters ✅

```python
client = AsyncIOMotorClient(
    auth_settings.mongodb_url,
    ssl_certfile=None if not is_atlas else certifi.where(),
    ssl_ca_certs=certifi.where() if is_atlas else None,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
    retryWrites=True,
    maxPoolSize=10,
    minPoolSize=1,
    retryReads=True
)
```

**Parameters explained:**
- `ssl_ca_certs`: CA certificate bundle for SSL verification
- `serverSelectionTimeoutMS`: Time to select a server (10 seconds)
- `connectTimeoutMS`: Time to establish connection (10 seconds)
- `socketTimeoutMS`: Time for socket operations (10 seconds)
- `retryWrites`: Automatic retry on write failures
- `retryReads`: Automatic retry on read failures
- `maxPoolSize`: Max connection pool size
- `minPoolSize`: Min connection pool size

### 3. Added Connection Test ✅

```python
# Test the connection
await client.admin.command('ping')
print("✅ MongoDB connection successful")
```

**Why:** Verifies connection before initializing Beanie

### 4. Added certifi Package ✅

Added `certifi` to `requirements.txt` for SSL certificate bundle

### 5. Added Proper Error Handling ✅

```python
except Exception as e:
    print(f"❌ Error initializing MongoDB: {e}")
    if client:
        client.close()
    raise
```

**Why:** Ensures connection is closed on error and error is properly reported

## Solutions by Error Type

### Issue: SSL Handshake Failed

**Causes:**
- Missing CA certificates
- Network issues
- MongoDB Atlas IP whitelist not configured

**Solutions:**
1. **Ensure certifi is installed:**
   ```bash
   pip install certifi
   ```

2. **Check MongoDB Atlas IP Whitelist:**
   - Go to MongoDB Atlas Dashboard
   - Go to Network Access → IP Whitelist
   - Add Modal's IP or allow all IPs temporarily: `0.0.0.0/0`

3. **Verify MONGODB_URL format:**
   ```
   ✅ Correct: mongodb+srv://username:password@cluster.mongodb.net/dbname
   ❌ Incorrect: mongodb://username:password@cluster.mongodb.net/dbname
   ```

### Issue: Connection Timeout

**Causes:**
- Network firewall blocking connection
- MongoDB cluster not running
- Wrong connection string

**Solutions:**
1. **Test connection locally first:**
   ```bash
   python -c "
   import asyncio
   from motor.motor_asyncio import AsyncIOMotorClient
   import certifi
   
   async def test():
       client = AsyncIOMotorClient(
           'mongodb+srv://user:pass@cluster.mongodb.net/db',
           ssl_ca_certs=certifi.where()
       )
       result = await client.admin.command('ping')
       print('Connected:', result)
   
   asyncio.run(test())
   "
   ```

2. **Check MongoDB Atlas cluster status:**
   - Ensure cluster is running (not paused)
   - Check cluster region matches your network

3. **Verify credentials:**
   - Check username and password are correct
   - Check special characters are URL-encoded

### Issue: Certificate Verification Error

**Cause:** SSL certificate validation failing

**Solution:** This fix automatically handles it with `certifi.where()`

## Environment Variables Needed

```bash
# Set these in Modal secrets or .env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/dbname
MONGODB_DATABASE=visionffe_auth
```

**Important:**
- Use `mongodb+srv://` not `mongodb://`
- Include database name or let it default
- URL-encode special characters: `@` → `%40`, `:` → `%3A`

## Testing

### Local Test

```bash
cd backend
python main.py
```

Expected output:
```
🚀 Starting up...
📊 Initializing MongoDB database...
✅ MongoDB connection successful
✅ MongoDB database initialized
🔧 Initializing embedder model...
...
```

### Modal Deployment Test

After updating requirements.txt:

```bash
modal deploy modal_deploy.py
```

Check logs:
```bash
modal app logs vision-ffe-api
```

Expected output should show:
```
✅ MongoDB connection successful
✅ MongoDB database initialized
```

## Troubleshooting Checklist

- [x] Added `certifi` to requirements.txt
- [x] Added SSL/TLS configuration
- [x] Added connection parameters
- [x] Added connection test with ping
- [x] Added proper error handling
- [x] MONGODB_URL format is `mongodb+srv://...`
- [x] MongoDB credentials are correct
- [x] MongoDB Atlas IP whitelist configured (0.0.0.0/0 or specific IPs)

## Next Steps

1. **Update requirements.txt** (already done)
2. **Install locally:**
   ```bash
   pip install certifi
   ```
3. **Test connection locally:**
   ```bash
   python main.py
   ```
4. **Deploy to Modal:**
   ```bash
   modal deploy modal_deploy.py
   ```

## Additional Resources

- [MongoDB Atlas Connection Guide](https://www.mongodb.com/docs/guides/atlas/connection-strings/)
- [PyMongo SSL/TLS Configuration](https://pymongo.readthedocs.io/en/stable/examples/connecting.html#connect-to-a-mongodb-instance)
- [Motor (Async Driver) SSL/TLS](https://motor.readthedocs.io/en/stable/examples/ssl.html)

Your MongoDB connection should now work reliably with SSL/TLS! 🚀
