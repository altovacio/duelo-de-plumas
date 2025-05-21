# Technical Debt and Future Improvements

This document lists known technical debt, areas for refactoring, and potential future improvements.

## TODO

Login revamp
contest details display
Arrows in view all in home are counterintuitive
mobile responsiveness
My contest section behaviour
Front contest cards to display private/public
assign judges
contest creator stuck at fechting..
Error going from open to closed directly

unable to edit multiple submissions or judge aprticipating of a contest.

## Frontend

* **Security Improvements**:
  * **Token Storage**: Replace localStorage token storage with HttpOnly cookies to prevent XSS vulnerabilities.
  * **CSRF Protection**: Implement proper CSRF protection for API requests.
  * **Error Handling**: Improve error handling for authentication failures and API errors.
  * **API Types**: Ensure all API response types are properly typed for better type safety.
  * **Token refresh mechanism**: Imlpement token refresh logic with proper error handling and recovery strategies.

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