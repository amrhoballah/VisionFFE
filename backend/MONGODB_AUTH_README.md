# VisionFFE Authentication System (MongoDB Version)

This document describes the authentication and authorization system for the VisionFFE application using MongoDB as the database.

## Overview

The authentication system provides:
- **User Authentication**: JWT-based authentication with access and refresh tokens
- **Role-Based Access Control (RBAC)**: Users have roles with specific permissions
- **Protected Endpoints**: All API endpoints now require appropriate permissions
- **User Management**: Admin interface for managing users and roles
- **MongoDB Integration**: Uses Beanie ODM for MongoDB operations

## Database Schema (MongoDB Collections)

### Users Collection
```json
{
  "_id": "ObjectId",
  "username": "string (unique)",
  "email": "string (unique)",
  "hashed_password": "string",
  "is_active": "boolean",
  "is_verified": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime",
  "role_ids": ["ObjectId"]
}
```

### Roles Collection
```json
{
  "_id": "ObjectId",
  "name": "string (unique)",
  "description": "string",
  "created_at": "datetime",
  "permission_ids": ["ObjectId"]
}
```

### Permissions Collection
```json
{
  "_id": "ObjectId",
  "name": "string (unique)",
  "description": "string",
  "resource": "string",
  "action": "string",
  "created_at": "datetime"
}
```

### Tokens Collection
```json
{
  "_id": "ObjectId",
  "token": "string (unique)",
  "token_type": "string",
  "expires_at": "datetime",
  "is_revoked": "boolean",
  "created_at": "datetime",
  "user_id": "ObjectId"
}
```

## Default Roles and Permissions

### Admin Role
- **Full access** to all resources and actions
- Can manage users, roles, and permissions
- Can access all API endpoints

### User Role
- `search_images`: Search for similar images
- `upload_images`: Upload new images
- `view_stats`: View database statistics

### Viewer Role
- `search_images_view`: Search for similar images (read-only)
- `view_stats_view`: View database statistics (read-only)

## API Endpoints

### Authentication Endpoints (`/auth`)

#### POST `/auth/register`
Register a new user account.
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

#### POST `/auth/login`
Login and receive tokens.
```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```
Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST `/auth/refresh`
Refresh access token using refresh token.
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST `/auth/logout`
Logout and revoke all tokens (requires authentication).

#### POST `/auth/change-password`
Change user password (requires authentication).
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

#### GET `/auth/me`
Get current user information (requires authentication).

### Admin Endpoints (`/admin`)

All admin endpoints require admin role.

#### User Management
- `GET /admin/users` - List all users
- `GET /admin/users/{user_id}` - Get specific user
- `POST /admin/users` - Create new user
- `PUT /admin/users/{user_id}` - Update user
- `DELETE /admin/users/{user_id}` - Delete user

#### Role Management
- `GET /admin/roles` - List all roles
- `POST /admin/roles` - Create new role
- `PUT /admin/roles/{role_id}` - Update role
- `DELETE /admin/roles/{role_id}` - Delete role

#### Role Assignment
- `POST /admin/users/{user_id}/roles/{role_id}` - Assign role to user
- `DELETE /admin/users/{user_id}/roles/{role_id}` - Remove role from user

### Protected API Endpoints

All existing endpoints now require authentication and appropriate permissions:

#### POST `/api/search`
- **Permission Required**: `images:read`
- **Roles**: user, viewer, admin

#### POST `/api/upload`
- **Permission Required**: `images:write`
- **Roles**: user, admin

#### GET `/api/database/stats`
- **Permission Required**: `stats:read`
- **Roles**: user, viewer, admin

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=visionffe_auth

# Token Expiration (optional, defaults shown)
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Password Requirements

Passwords must meet these criteria:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

## Setup Instructions

1. **Install MongoDB**
   ```bash
   # On macOS with Homebrew
   brew install mongodb-community
   
   # Start MongoDB
   brew services start mongodb-community
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**
   Create a `.env` file with the required configuration.

4. **Create Admin User**
   ```bash
   python create_admin.py
   ```

5. **Start the Application**
   ```bash
   python main.py
   ```

## Usage Examples

### Frontend Integration

#### Login
```javascript
const response = await fetch('/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'johndoe',
    password: 'SecurePass123!'
  })
});

const data = await response.json();
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
```

#### Making Authenticated Requests
```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('/api/search', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
  },
  body: formData
});
```

#### Token Refresh
```javascript
const refreshToken = localStorage.getItem('refresh_token');

const response = await fetch('/auth/refresh', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    refresh_token: refreshToken
  })
});

const data = await response.json();
localStorage.setItem('access_token', data.access_token);
```

## MongoDB-Specific Features

### Advantages of MongoDB
- **Flexible Schema**: Easy to add new fields without migrations
- **Horizontal Scaling**: Can scale across multiple servers
- **Document Storage**: Natural fit for JSON-like data structures
- **Indexing**: Powerful indexing capabilities for fast queries
- **Aggregation**: Rich aggregation pipeline for complex queries

### Beanie ODM Features
- **Async/Await**: Native async support
- **Type Safety**: Full type hints and validation
- **Pydantic Integration**: Automatic validation and serialization
- **MongoDB Features**: Support for MongoDB-specific features like ObjectId

## Security Features

- **Password Hashing**: Bcrypt with salt
- **JWT Tokens**: Secure token-based authentication
- **Token Revocation**: Tokens can be revoked and tracked
- **Role-Based Access**: Granular permission system
- **Password Validation**: Strong password requirements
- **MongoDB Security**: Connection security and data validation
- **CORS Configuration**: Configurable cross-origin settings

## Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Check if token is valid and not expired
   - Verify token format: `Bearer <token>`
   - Check if user account is active

2. **"Insufficient permissions"**
   - Verify user has required role
   - Check role has required permission
   - Admin role has full access

3. **"Token has been revoked"**
   - User logged out or password changed
   - Token was manually revoked
   - Use refresh token to get new access token

4. **MongoDB Connection Issues**
   - Ensure MongoDB is running
   - Check connection string format
   - Verify database permissions

### Database Issues

If you need to reset the database:
1. Connect to MongoDB: `mongosh`
2. Switch to your database: `use visionffe_auth`
3. Drop collections: `db.users.drop()`, `db.roles.drop()`, etc.
4. Restart the application to recreate data
5. Run `create_admin.py` to create admin user

## Development Notes

- The system uses MongoDB with Beanie ODM
- All database operations are async
- ObjectIds are used as primary keys
- Indexes are automatically created for performance
- Consider implementing MongoDB Atlas for production
- JWT secret key should be strong and unique
- Consider implementing rate limiting for auth endpoints
- Add email verification for production use
