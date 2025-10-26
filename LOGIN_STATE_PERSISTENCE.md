# Login State Persistence

## Overview
The application now has improved login state persistence that keeps users logged in across page refreshes and browser sessions.

## How It Works

### 1. Token Storage (`authService.ts`)
- **Access Token**: Stored in `localStorage` as `access_token`
- **Refresh Token**: Stored in `localStorage` as `refresh_token`
- **Automatic Refresh**: Tokens are automatically refreshed every 5 minutes if the refresh token is still valid

### 2. User Data Storage (`AuthContext.tsx`)
- **User Information**: Stored in `localStorage` as `user_data`
- **Initial Load**: User data is loaded from localStorage immediately on app start
- **Auto-sync**: User data is saved to localStorage whenever updated

### 3. Authentication Flow

#### On App Load:
1. **Load Tokens**: Access and refresh tokens are loaded from localStorage
2. **Load User Data**: User data is loaded from localStorage for instant display
3. **Validate Tokens**: If tokens exist, fetch fresh user data from backend
4. **Update State**: Update user data in context if validation succeeds

#### On Login:
1. **Authenticate**: Send credentials to backend
2. **Receive Tokens**: Store access and refresh tokens in localStorage
3. **Fetch User Data**: Get user information from backend
4. **Save User Data**: Store user data in localStorage
5. **Update State**: Update AuthContext with user data

#### On Logout:
1. **Revoke Tokens**: Send logout request to backend
2. **Clear Storage**: Remove tokens and user data from localStorage
3. **Update State**: Clear user from AuthContext

#### On Page Refresh:
1. **Load from Cache**: Instantly display cached user data
2. **Validate in Background**: Check if tokens are still valid
3. **Update if Needed**: Refresh user data from backend

## Features

### ✅ Token Management
- **Persistent Storage**: Tokens survive page refreshes and browser restarts
- **Automatic Refresh**: Tokens are refreshed before expiration
- **Secure Storage**: Tokens are stored in localStorage with no automatic expiration (until logout)

### ✅ User Data Caching
- **Fast Loading**: User data loads instantly from cache
- **Background Sync**: Fresh data is fetched in background to ensure accuracy
- **Offline Support**: Partial offline support with cached data

### ✅ Session Management
- **Long-lived Sessions**: Users stay logged in until they explicitly log out
- **Multi-tab Support**: Login state is shared across browser tabs
- **Auto-logout**: Automatically logs out if tokens become invalid

## Configuration

### Token Expiration
- **Access Token**: Typically expires in 15-30 minutes (configurable on backend)
- **Refresh Token**: Typically expires in 7 days (configurable on backend)
- **Auto-refresh**: Tokens are checked and refreshed every 5 minutes

### Storage Keys
- `access_token`: JWT access token
- `refresh_token`: JWT refresh token
- `user_data`: Complete user profile information

## Security Considerations

### ✅ Benefits
- **No Password Storage**: Passwords are never stored locally
- **Token-based Auth**: Secure JWT-based authentication
- **Backend Validation**: All requests validated on backend
- **Auto-cleanup**: Invalid tokens automatically cleared

### ⚠️ Security Notes
- **localStorage**: Data is stored in browser's localStorage (accessible to JavaScript)
- **XSS Protection**: Ensure your app is protected against XSS attacks
- **HTTPS**: Always use HTTPS in production to encrypt tokens in transit

## Implementation Details

### AuthService (`services/authService.ts`)
```typescript
// Automatic token refresh every 5 minutes
private setupTokenRefresh(): void {
  setInterval(async () => {
    if (this.refreshToken && this.accessToken) {
      try {
        const isExpiring = await this.isTokenExpiringSoon();
        if (isExpiring) {
          await this.refreshAccessToken();
        }
      } catch (error) {
        console.warn('Background token refresh failed:', error);
      }
    }
  }, 5 * 60 * 1000);
}
```

### AuthContext (`contexts/AuthContext.tsx`)
```typescript
// Load user data from localStorage on initial render
const getInitialUser = (): UserResponse | null => {
  if (typeof window !== 'undefined') {
    const storedUser = localStorage.getItem('user_data');
    if (storedUser) {
      try {
        return JSON.parse(storedUser);
      } catch (error) {
        localStorage.removeItem('user_data');
      }
    }
  }
  return null;
};

const [user, setUser] = useState<UserResponse | null>(getInitialUser());
```

## Testing

### To Test Login Persistence:
1. Log in to the application
2. Refresh the page - you should remain logged in
3. Close and reopen the browser - you should still be logged in
4. Log out - you should be logged out
5. Refresh page - you should stay logged out

### To Test Token Refresh:
1. Log in to the application
2. Wait 5 minutes (or modify the interval in code)
3. Make an API request - token should be refreshed automatically
4. Check browser console for any refresh errors

### To Test Multi-tab Support:
1. Log in to the application
2. Open the same site in a new tab
3. Both tabs should show you as logged in
4. Log out from one tab
5. Both tabs should show you as logged out

## Troubleshooting

### User stays logged in even after logout
- **Solution**: Check if localStorage.clear() is being called
- **Check**: Ensure logout function removes all tokens

### User is logged out after refresh
- **Solution**: Check if tokens are being loaded from localStorage
- **Check**: Check browser console for token errors

### User data not showing immediately
- **Solution**: User data now loads instantly from cache
- **Check**: If issue persists, check localStorage in browser DevTools

### Token refresh not working
- **Solution**: Check if backend refresh endpoint is working
- **Check**: Check browser console for refresh errors

## Environment Variables

No additional environment variables needed for login persistence. The feature uses existing token storage mechanisms.

## Future Enhancements

### Potential Improvements:
1. **Session Expiry Warning**: Warn users before session expires
2. **Remember Me Option**: Add option for longer sessions (30 days)
3. **Device Management**: Show list of logged-in devices
4. **Activity Tracking**: Track last activity timestamp
5. **Session Management**: Allow users to manage active sessions

