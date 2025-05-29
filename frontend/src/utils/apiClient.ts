import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import { getTokens, removeTokens } from './tokenUtils';
import { API_BASE_URL } from './apiConfig';

// Create and export a singleton axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to attach tokens to requests
apiClient.interceptors.request.use(
  (config) => {
    const tokens = getTokens();
    
    if (!tokens) {
      return config;
    }
    
    // Add the token to the header
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
      // Clear tokens but let components handle navigation
      removeTokens();
      // Don't force navigation here - let React Router handle it
      // window.location.href = '/login';
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