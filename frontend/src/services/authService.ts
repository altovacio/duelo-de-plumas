import axios from 'axios';
import { LoginRequest, RegisterRequest, AuthTokens, User } from '../types/auth';
import { getTokens, storeTokens, isTokenExpired, removeTokens } from '../utils/tokenUtils';

// Use the proxy configured in Vite for local development
const API_BASE_URL = '';

// Create axios instance with base configuration
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to attach tokens to requests
apiClient.interceptors.request.use(
  async (config) => {
    const tokens = getTokens();
    
    if (!tokens) {
      return config;
    }
    
    // Check if access token is expired and refresh token is available
    if (isTokenExpired(tokens.access_token) && tokens.refresh_token) {
      try {
        // Try to refresh the token
        const newTokens = await refreshAccessToken(tokens.refresh_token);
        if (newTokens) {
          // Update the authorization header with the new token
          config.headers['Authorization'] = `${newTokens.token_type} ${newTokens.access_token}`;
          return config;
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
        // If refresh fails, log out the user
        removeTokens();
        window.location.href = '/login';
        return config;
      }
    }
    
    // Otherwise just add the token to the header
    config.headers['Authorization'] = `${tokens.token_type} ${tokens.access_token}`;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle common errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle unauthorized errors (401)
    if (error.response && error.response.status === 401) {
      // Clear tokens and redirect to login page
      removeTokens();
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

/**
 * Logs in a user and stores their tokens
 */
export const login = async (credentials: LoginRequest): Promise<{ user: User; tokens: AuthTokens }> => {
  try {
    // Try using a direct connection to the backend server
    console.log('Attempting direct login to backend server');
    
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    // Connect directly to the backend rather than through the proxy
    const response = await axios.post('http://localhost:8000/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    console.log('Login response received:', response.data);
    const tokens = response.data;
    
    // Store tokens in localStorage
    storeTokens(tokens);
    
    // Fetch user info using the token
    const userResponse = await axios.get('http://localhost:8000/users/me', {
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
    
    // Register the user - direct connection to backend
    const response = await axios.post('http://localhost:8000/auth/signup', userData);
    const user = response.data;
    
    // After registration, log them in to get tokens
    const formData = new URLSearchParams();
    formData.append('username', userData.username);
    formData.append('password', userData.password);
    
    const loginResponse = await axios.post('http://localhost:8000/auth/login', formData, {
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
 * Refreshes the access token using the refresh token
 */
export const refreshAccessToken = async (refreshToken: string): Promise<AuthTokens | null> => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/auth/refresh-token`,
      { refresh_token: refreshToken },
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    const tokens = response.data;
    
    // Store the new tokens
    storeTokens(tokens);
    
    return tokens;
  } catch (error) {
    console.error('Token refresh error:', error);
    return null;
  }
};

/**
 * Logs out a user by removing tokens and calling the logout endpoint
 */
export const logout = async (): Promise<void> => {
  try {
    const tokens = getTokens();
    if (tokens) {
      // Call logout endpoint to invalidate token on server
      await apiClient.post('/api/auth/logout', { refresh_token: tokens.refresh_token });
    }
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    // Always remove tokens locally, even if API call fails
    removeTokens();
  }
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
    
    const response = await axios.get('http://localhost:8000/users/me', {
      headers: {
        'Authorization': `Bearer ${tokens.access_token}`
      }
    });
    
    console.log('User data received');
    return response.data;
  } catch (error) {
    console.error('Get current user error:', error);
    return null;
  }
}; 