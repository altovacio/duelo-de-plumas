import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import { getTokens, storeTokens, isTokenExpired, removeTokens } from './tokenUtils';
import { API_BASE_URL, AUTH_ENDPOINTS } from './apiConfig';

// Create and export a singleton axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Function to refresh the access token
const refreshAccessToken = async (refreshToken: string) => {
  try {
    // Use the apiClient directly without interceptors to avoid infinite loops
    const response = await axios.post(
      `${API_BASE_URL}${AUTH_ENDPOINTS.REFRESH_TOKEN}`,
      { refresh_token: refreshToken },
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    const tokens = response.data;
    storeTokens(tokens);
    return tokens;
  } catch (error) {
    console.error('Token refresh error:', error);
    return null;
  }
};

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
  (error: AxiosError) => {
    // Handle unauthorized errors (401)
    if (error.response && error.response.status === 401) {
      // Clear tokens and redirect to login page
      removeTokens();
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

// Helper functions for common API request types
export const api = {
  get: <T>(url: string, config?: AxiosRequestConfig) => 
    apiClient.get<T>(url, config).then(response => response.data),
  
  post: <T>(url: string, data?: any, config?: AxiosRequestConfig) => 
    apiClient.post<T>(url, data, config).then(response => response.data),
  
  put: <T>(url: string, data?: any, config?: AxiosRequestConfig) => 
    apiClient.put<T>(url, data, config).then(response => response.data),
  
  patch: <T>(url: string, data?: any, config?: AxiosRequestConfig) => 
    apiClient.patch<T>(url, data, config).then(response => response.data),
  
  delete: <T>(url: string, config?: AxiosRequestConfig) => 
    apiClient.delete<T>(url, config).then(response => response.data),
};

export default apiClient; 