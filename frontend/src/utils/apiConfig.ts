/**
 * API Configuration
 * 
 * Centralized API URL configuration that adapts to different environments
 */

// Default to empty base URL which will be handled by the Vite proxy in development
// In production, this would be automatically populated by environment variables
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// Auth endpoints
export const AUTH_ENDPOINTS = {
  LOGIN: '/auth/login',
  SIGNUP: '/auth/signup',
  REFRESH_TOKEN: '/auth/refresh-token',
  LOGOUT: '/auth/logout',
  CURRENT_USER: '/users/me',
};

// User endpoints
export const USER_ENDPOINTS = {
  PROFILE: '/users/me',
  UPDATE_PROFILE: '/users/me',
};

// Other endpoints can be added here as the app grows 