import { LoginRequest, RegisterRequest, AuthTokens, User } from '../types/auth';
import { getTokens, storeTokens, removeTokens } from '../utils/tokenUtils';
import apiClient, { api } from '../utils/apiClient';
import { AUTH_ENDPOINTS } from '../utils/apiConfig';

/**
 * Logs in a user and stores their tokens
 */
export const login = async (credentials: LoginRequest): Promise<{ user: User; tokens: AuthTokens; isFirstLogin?: boolean }> => {
  try {
    // Use the api client with JSON data (standardized format)
    const response = await apiClient.post(AUTH_ENDPOINTS.LOGIN, {
      username: credentials.username,
      password: credentials.password
    });
    
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
    
    return { user, tokens, isFirstLogin: tokens.is_first_login };
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
    // Register the user using apiClient
    const response = await apiClient.post(AUTH_ENDPOINTS.SIGNUP, userData);
    const user = response.data;
    
    // After registration, log them in to get tokens
    const loginResponse = await apiClient.post(AUTH_ENDPOINTS.LOGIN, {
      username: userData.username,
      password: userData.password
    });
    
    const tokens = loginResponse.data;
    
    // Store tokens in localStorage
    storeTokens(tokens);
    
    return { user, tokens };
  } catch (error: any) {
    console.error('Registration error:', error);
    
    // Extract detailed error information from the response
    let errorMessage = 'Registration failed';
    
    if (error.response?.data) {
      const responseData = error.response.data;
      
      // Check for specific field errors first
      if (responseData.username) {
        errorMessage = `Username error: ${Array.isArray(responseData.username) ? responseData.username[0] : responseData.username}`;
      } else if (responseData.email) {
        errorMessage = `Email error: ${Array.isArray(responseData.email) ? responseData.email[0] : responseData.email}`;
      } 
      // Check for common error message fields
      else if (responseData.detail) {
        errorMessage = responseData.detail;
      } else if (responseData.message) {
        errorMessage = responseData.message;
      } else if (responseData.error) {
        errorMessage = responseData.error;
      } else if (typeof responseData === 'string') {
        errorMessage = responseData;
      } 
      // Handle multiple field errors
      else {
        const fieldErrors = [];
        for (const [field, errors] of Object.entries(responseData)) {
          if (Array.isArray(errors)) {
            fieldErrors.push(`${field}: ${errors[0]}`);
          } else if (typeof errors === 'string') {
            fieldErrors.push(`${field}: ${errors}`);
          }
        }
        if (fieldErrors.length > 0) {
          errorMessage = fieldErrors.join(', ');
        }
      }
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    throw new Error(errorMessage);
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
    
    // Use apiClient which will handle the Authorization header automatically
    const user = await api.get<User>(AUTH_ENDPOINTS.CURRENT_USER);
    
    return user;
  } catch (error) {
    console.error('Get current user error:', error);
    return null;
  }
}; 