import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, LoginRequest, RegisterRequest, UserResponse, TokenResponse } from '../services/authService';

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = authService.isAuthenticated();

  // Initialize authentication state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      if (isAuthenticated) {
        try {
          const userData = await authService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('Failed to get current user:', error);
          // If we can't get user data, clear the auth state
          await authService.logout();
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      setIsLoading(true);
      const tokens: TokenResponse = await authService.login(credentials);
      const userData: UserResponse = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterRequest): Promise<void> => {
    try {
      setIsLoading(true);
      await authService.register(userData);
      // After successful registration, automatically log the user in
      await login({ username: userData.username, password: userData.password });
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      await authService.logout();
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails on server, clear local state
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUser = async (): Promise<void> => {
    if (isAuthenticated) {
      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);
      } catch (error) {
        console.error('Failed to refresh user:', error);
        await logout();
      }
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
