# Technical Debt and Future Improvements

This document lists known technical debt, areas for refactoring, and potential future improvements.

## Frontend

* **API URL Configuration**: The current setup has issues with cross-origin requests between the frontend and backend. This needs to be properly configured to ensure seamless communication between the two services.
  * ~~**Fix hardcoded URLs**: Replace hardcoded `http://localhost:8000` URLs in authService.ts with environment variables or the configured Vite proxy. Create a centralized API URL configuration in a separate file (e.g., `apiConfig.ts`) that respects different environments (development/production).~~ (RESOLVED)
  * ~~**Standardize API requests**: Use the configured axios instance (`apiClient`) consistently for all API calls instead of direct axios calls. Ensure all API requests go through the same interceptors for proper token management.~~ (RESOLVED)
  * ~~**Missing logout endpoint**: The authService calls a logout endpoint that doesn't exist in the backend. Implement a proper logout endpoint on the backend to invalidate tokens.~~ (RESOLVED - Implemented frontend-only logout)
  * ~~**Inconsistent request formats**: Currently using form-encoded data for login but JSON for other requests. Standardize the request format across all endpoints.~~ (RESOLVED - Standardized on JSON for all API requests)


* **Security Improvements**:
  * **Token Storage**: Replace localStorage token storage with HttpOnly cookies to prevent XSS vulnerabilities.
  * **CSRF Protection**: Implement proper CSRF protection for API requests.
  * **Error Handling**: Improve error handling for authentication failures and API errors.
  * **API Types**: Ensure all API response types are properly typed for better type safety.
  * **Token refresh mechanism**: Enhance token refresh logic with proper error handling and recovery strategies.

## Backend

* **Security Configurations**:
  * **CORS Settings**: Replace overly permissive CORS configuration (`allow_methods=["*"]` and `allow_headers=["*"]`) with specific allowed methods and headers.

* **Authentication System**:
  * **Refresh Token Rotation**: Implement refresh token rotation to enhance security.
  * **JWT Configuration**: Review and optimize JWT token expiration settings.
  * **Password Policies**: Add password complexity requirements and account lockout mechanisms.
  * **Token Revocation**: Implement a token revocation mechanism and a logout endpoint that adds tokens to a blacklist or database of revoked tokens.

* **API Design**:
  * **Consistent Endpoints**: Standardize API endpoint structure and request formats (some use `/api` prefix, some don't).
  * **Request Validation**: Enhance validation for all incoming requests.
  * **Comprehensive Testing**: Increase test coverage for authentication flows and API endpoints. 