# Modal Deployment Guide for VisionFFE

## Prerequisites

1. **Install Modal CLI**:
   ```bash
   pip install modal
   ```

2. **Set up Modal Account**:
   ```bash
   modal token new
   ```
   Follow the prompts to create your Modal account and get your API token.

## Step 1: Create Modal Secrets

You need to create two Modal secrets to store your environment variables:

### Secret 1: `vision-api` (for existing API keys)
```bash
modal secret create vision-api \
  PINECONE_API_KEY=your_pinecone_api_key_here \
  PINECONE_INDEX_NAME=your_index_name \
  MODEL_PRESET=balanced \
  R2_ACCOUNT_ID=your_r2_account_id \
  R2_ACCESS_KEY_ID=your_r2_access_key \
  R2_SECRET_ACCESS_KEY=your_r2_secret_key \
  R2_REGION=auto \
  R2_BUCKET_NAME=your_bucket_name
```

### Secret 2: `auth-secrets` (for authentication)
```bash
modal secret create auth-secrets \
  JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production \
  MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net \
  MONGODB_DATABASE=visionffe_auth
```

**Important Notes:**
- Replace `your-super-secret-jwt-key-change-this-in-production` with a strong, random secret key
- For MongoDB, use MongoDB Atlas connection string or your MongoDB instance URL
- Generate a strong JWT secret: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

## Step 2: Deploy to Modal

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Deploy the application**:
   ```bash
   modal deploy modal_deploy.py
   ```

3. **Wait for deployment**:
   Modal will build the image and deploy your application. This may take 5-10 minutes for the first deployment.

4. **Get your deployment URL**:
   After successful deployment, Modal will provide you with a URL like:
   ```
   https://your-username--vision-ffe-api.modal.run
   ```

## Step 3: Update Frontend Configuration

Update your frontend configuration to use the Modal deployment URL:

1. **Edit `frontend/config.ts`**:
   ```typescript
   export const config = {
     api: {
       baseUrl: process.env.NODE_ENV === 'production' 
         ? 'https://your-username--vision-ffe-api.modal.run'  // Replace with your Modal URL
         : 'http://localhost:8080',
     },
     // ... rest of config
   };
   ```

2. **Update `frontend/services/authService.ts`**:
   The authService will automatically use the config.baseUrl, so no changes needed there.

## Step 4: Test the Deployment

1. **Test the API directly**:
   ```bash
   curl https://your-username--vision-ffe-api.modal.run/
   ```
   Should return:
   ```json
   {
     "status": "online",
     "model": "loaded",
     "pinecone": "connected",
     "database_size": 0,
     "device": "cuda"
   }
   ```

2. **Test authentication endpoints**:
   ```bash
   # Test registration
   curl -X POST https://your-username--vision-ffe-api.modal.run/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "email": "test@example.com", "password": "testpassword123"}'
   ```

3. **Test with frontend**:
   - Build and deploy your frontend to your hosting service
   - Update the config.ts with your Modal URL
   - Test the complete authentication flow

## Step 5: Create Admin User (Optional)

If you want to create an admin user, you can run the create_admin script locally with your Modal MongoDB connection:

1. **Set up local environment**:
   ```bash
   # Create local .env file with your Modal MongoDB URL
   echo "MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net" > .env
   echo "MONGODB_DATABASE=visionffe_auth" >> .env
   echo "JWT_SECRET_KEY=your-super-secret-jwt-key" >> .env
   ```

2. **Run admin creation script**:
   ```bash
   python create_admin.py
   ```

## Monitoring and Management

### View Logs
```bash
modal app logs vision-ffe-api
```

### Scale Down (to save costs)
```bash
modal app stop vision-ffe-api
```

### Scale Up
```bash
modal app start vision-ffe-api
```

### Update Deployment
After making changes to your code:
```bash
modal deploy modal_deploy.py
```

## Cost Optimization

1. **Use scaledown_window**: Already set to 300 seconds (5 minutes)
2. **Monitor usage**: Check Modal dashboard for usage and costs
3. **Consider smaller GPU**: Change `gpu="T4"` to `gpu="A10G"` or `gpu="A100"` based on your needs

## Troubleshooting

### Common Issues:

1. **Import Errors**:
   - Ensure all dependencies are listed in the Modal image
   - Check that file paths are correct in the deployment

2. **Secret Not Found**:
   - Verify secret names match exactly: `vision-api` and `auth-secrets`
   - Check that all required environment variables are in the secrets

3. **MongoDB Connection Issues**:
   - Verify MongoDB URL is correct
   - Check MongoDB Atlas IP whitelist (add Modal IPs if needed)
   - Ensure database exists

4. **Authentication Errors**:
   - Verify JWT_SECRET_KEY is set correctly
   - Check that JWT secret is the same across deployments

### Debug Commands:
```bash
# Check app status
modal app list

# View app details
modal app describe vision-ffe-api

# Check secrets
modal secret list
```

## Production Considerations

1. **Security**:
   - Use strong, unique JWT secrets
   - Enable MongoDB authentication
   - Consider rate limiting
   - Use HTTPS (Modal provides this automatically)

2. **Performance**:
   - Monitor GPU usage
   - Optimize model loading
   - Consider caching strategies

3. **Monitoring**:
   - Set up logging
   - Monitor error rates
   - Track response times

## Next Steps

1. **Deploy frontend**: Deploy your React frontend to Vercel, Netlify, or similar
2. **Set up domain**: Configure custom domain if needed
3. **Monitor**: Set up monitoring and alerting
4. **Scale**: Adjust resources based on usage

Your VisionFFE API is now deployed on Modal with full authentication support! 🚀
