// Authentication service for handling API calls to backend auth endpoints
import config from '../config';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  title: string;
  officeName?: string;
  supplierName?: string;
  location: string;
  phone: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  title: string;
  officeName?: string;
  supplierName?: string;
  location: string;
  phone: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  role_ids: string[];
}

export interface AuthError {
  detail: string;
}

class AuthService {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(baseUrl: string = config.api.baseUrl) {
    this.baseUrl = baseUrl;
    this.loadTokensFromStorage();
    
    // Set up automatic token refresh
    this.setupTokenRefresh();
  }
  
  private setupTokenRefresh(): void {
    // Run periodic token refresh check every 5 minutes
    if (typeof window !== 'undefined') {
      setInterval(async () => {
        if (this.refreshToken && this.accessToken) {
          try {
            // Try to refresh token if we have valid refresh token
            const isExpiring = await this.isTokenExpiringSoon();
            if (isExpiring) {
              await this.refreshAccessToken();
            }
          } catch (error) {
            console.warn('Background token refresh failed:', error);
          }
        }
      }, 5 * 60 * 1000); // Check every 5 minutes
    }
  }
  
  private async isTokenExpiringSoon(): Promise<boolean> {
    // Simple check: If token exists and refresh token exists, consider refreshing
    // In a real implementation, you'd decode the JWT and check expiration
    return this.refreshToken !== null && this.accessToken !== null;
  }

  // Token management
  private loadTokensFromStorage(): void {
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token');
      this.refreshToken = localStorage.getItem('refresh_token');
    }
  }

  private saveTokensToStorage(tokens: TokenResponse): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      this.accessToken = tokens.access_token;
      this.refreshToken = tokens.refresh_token;
    }
  }

  private clearTokensFromStorage(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      this.accessToken = null;
      this.refreshToken = null;
    }
  }

  // Authentication methods
  async register(userData: RegisterRequest): Promise<UserResponse> {
    const response = await fetch(`${this.baseUrl}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData: AuthError = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }

    return response.json();
  }

  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData: AuthError = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }

    const tokens = await response.json();
    this.saveTokensToStorage(tokens);
    return tokens;
  }

  async refreshAccessToken(): Promise<TokenResponse> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${this.baseUrl}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (!response.ok) {
      this.clearTokensFromStorage();
      throw new Error('Token refresh failed');
    }

    const tokens = await response.json();
    this.saveTokensToStorage(tokens);
    return tokens;
  }

  async logout(): Promise<void> {
    if (!this.accessToken) {
      this.clearTokensFromStorage();
      return;
    }

    try {
      await fetch(`${this.baseUrl}/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      this.clearTokensFromStorage();
    }
  }

  async getCurrentUser(): Promise<UserResponse> {
    if (!this.accessToken) {
      throw new Error('No access token available');
    }

    const response = await fetch(`${this.baseUrl}/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token might be expired, try to refresh
        try {
          await this.refreshAccessToken();
          // Retry the request with new token
          return this.getCurrentUser();
        } catch (refreshError) {
          this.clearTokensFromStorage();
          throw new Error('Session expired. Please login again.');
        }
      }
      const errorData: AuthError = await response.json();
      throw new Error(errorData.detail || 'Failed to get user info');
    }

    return response.json();
  }

  // Utility methods
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  // Method to make authenticated API calls
  async authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
    if (!this.accessToken) {
      throw new Error('No access token available');
    }

    // Don't set Content-Type for FormData - browser will set it with boundary
    const isFormData = options.body instanceof FormData;
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${this.accessToken}`,
    };
    
    // Only set Content-Type if it's not FormData
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    
    // Merge with any existing headers
    Object.assign(headers, options.headers);

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle token expiration
    if (response.status === 401) {
      try {
        await this.refreshAccessToken();
        // Retry the request with new token
        return this.authenticatedFetch(url, options);
      } catch (refreshError) {
        this.clearTokensFromStorage();
        throw new Error('Session expired. Please login again.');
      }
    }

    return response;
  }
}

// Create and export a singleton instance
export const authService = new AuthService();
