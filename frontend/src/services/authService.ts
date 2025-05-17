import { LoginRequest, RegisterRequest, AuthTokens, User } from '../types/auth';
import { getTokens, storeTokens, removeTokens } from '../utils/tokenUtils';
import apiClient, { api } from '../utils/apiClient';
import { AUTH_ENDPOINTS } from '../utils/apiConfig';

/**
 * Logs in a user and stores their tokens
 */
export const login = async (credentials: LoginRequest): Promise<{ user: User; tokens: AuthTokens }> => {
  try {
    console.log('Attempting login with username:', credentials.username);
    
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    // Use the api client with form data
    const response = await apiClient.post(AUTH_ENDPOINTS.LOGIN, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    console.log('Login response received');
    const tokens = response.data;
    
    // Store tokens in localStorage
    storeTokens(tokens);
    
    // Fetch user info using the token
    const userResponse = await apiClient.get(AUTH_ENDPOINTS.CURRENT_USER, {
      headers: {
        'Authorization': `Bearer ${tokens.access_token}`
      }
    });
    
    const user = userResponse.data;
    
    return { user, tokens };
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

/**
 * Registers a new user
 */
export const register = async (userData: RegisterRequest): Promise<{ user: User; tokens: AuthTokens }> => {
  try {
    console.log('Attempting registration with username:', userData.username);
    
    // Register the user using apiClient
    const response = await apiClient.post(AUTH_ENDPOINTS.SIGNUP, userData);
    const user = response.data;
    
    // After registration, log them in to get tokens
    const formData = new URLSearchParams();
    formData.append('username', userData.username);
    formData.append('password', userData.password);
    
    const loginResponse = await apiClient.post(AUTH_ENDPOINTS.LOGIN, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    const tokens = loginResponse.data;
    console.log('Login after registration successful');
    
    // Store tokens in localStorage
    storeTokens(tokens);
    
    return { user, tokens };
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

/**
 * Logs out a user by removing tokens from localStorage
 * Frontend-only implementation that doesn't require a backend endpoint
 */
export const logout = (): void => {
  // Simply remove tokens locally
  removeTokens();
};

/**
 * Gets the current user profile
 */
export const getCurrentUser = async (): Promise<User | null> => {
  try {
    const tokens = getTokens();
    if (!tokens) {
      return null;
    }
    
    console.log('Fetching current user data');
    
    // Use apiClient which will handle the Authorization header automatically
    const user = await api.get<User>(AUTH_ENDPOINTS.CURRENT_USER);
    
    console.log('User data received');
    return user;
  } catch (error) {
    console.error('Get current user error:', error);
    return null;
  }
}; 