/**
 * API Configuration
 * 
 * Centralized API URL configuration that adapts to different environments
 */

// Use /api prefix for development (handled by Vite proxy)
// In production, this would be the full backend URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Auth endpoints
export const AUTH_ENDPOINTS = {
  LOGIN: '/auth/login/json',
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