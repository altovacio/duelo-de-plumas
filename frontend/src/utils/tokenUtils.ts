import { AuthTokens } from '../types/auth';

// Token storage keys
const ACCESS_TOKEN_KEY = 'dp_access_token';
const REFRESH_TOKEN_KEY = 'dp_refresh_token';
const TOKEN_TYPE_KEY = 'dp_token_type';

/**
 * Securely stores auth tokens in localStorage with expiration check
 */
export const storeTokens = (tokens: AuthTokens): void => {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  localStorage.setItem(TOKEN_TYPE_KEY, tokens.token_type);
};

/**
 * Retrieves auth tokens from localStorage
 */
export const getTokens = (): AuthTokens | null => {
  const access_token = localStorage.getItem(ACCESS_TOKEN_KEY);
  const refresh_token = localStorage.getItem(REFRESH_TOKEN_KEY);
  const token_type = localStorage.getItem(TOKEN_TYPE_KEY);
  
  if (!access_token || !refresh_token || !token_type) {
    return null;
  }
  
  return {
    access_token,
    refresh_token,
    token_type
  };
};

/**
 * Removes all auth tokens from localStorage
 */
export const removeTokens = (): void => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(TOKEN_TYPE_KEY);
};

/**
 * Checks if the access token is expired
 */
export const isTokenExpired = (token: string): boolean => {
  try {
    // JWT tokens consist of three parts: header, payload, and signature
    // We're only interested in the payload
    const payloadBase64 = token.split('.')[1];
    
    // Decode the Base64Url encoded payload
    const payload = JSON.parse(atob(payloadBase64));
    
    // Check if the token has an expiration time
    if (!payload.exp) {
      return false;
    }
    
    // Compare the expiration time with the current time
    // exp is in seconds, Date.now() is in milliseconds
    const currentTime = Math.floor(Date.now() / 1000);
    return payload.exp < currentTime;
  } catch (error) {
    console.error('Error parsing token:', error);
    // If we can't parse the token, assume it's expired
    return true;
  }
};

/**
 * Gets the authorization header value for API requests
 */
export const getAuthHeader = (): string | null => {
  const tokens = getTokens();
  if (!tokens) {
    return null;
  }
  
  return `${tokens.token_type} ${tokens.access_token}`;
}; 