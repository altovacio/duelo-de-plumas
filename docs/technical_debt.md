# Technical Debt and Future Improvements

This document lists known technical debt, areas for refactoring, and potential future improvements.

## ONGOING

-Header & pages definition
  -Mobile responsiveness pt1

## TODO

-Proper onboarding

-style
  -Mobile responsiveness

-initial setup

-Test deleting elements (users, contests, etc.)

-Credit spenditure revisit (free nano? 1000 credits instead of 100?)
-Credit purchasing
-What should we do when the parsing or AI execution fails? Retries, exceptions (if the platform is broken, prevent the users from spending resources? Refund?)

-PDF stuff
-Better experience full page writer
   -marktwo migration

-English/Spanish

-Writer Robots Arena

-Login via email (cursor style)

-Footer

-testing 


## Frontend

* **Security Improvements**:
  * **Token Storage**: Replace localStorage token storage with HttpOnly cookies to prevent XSS vulnerabilities.
  * **CSRF Protection**: Implement proper CSRF protection for API requests.
  * **Error Handling**: Improve error handling for authentication failures and API errors.
  * **API Types**: Ensure all API response types are properly typed for better type safety.
  * **Token refresh mechanism**: Imlpement token refresh logic with proper error handling and recovery strategies.

## Backend

* **Authentication System**:
  * **Refresh Token Rotation**: Implement refresh token rotation to enhance security.
  * **JWT Configuration**: Review and optimize JWT token expiration settings.
  * **Password Policies**: Add password complexity requirements and account lockout mechanisms.
  * **Token Revocation**: Implement a token revocation mechanism and a logout endpoint that adds tokens to a blacklist or database of revoked tokens.

* **API Design**:
  * **Consistent Endpoints**: Standardize API endpoint structure and request formats (some use `/api` prefix, some don't).
  * **Request Validation**: Enhance validation for all incoming requests.
  * **Comprehensive Testing**: Increase test coverage for authentication flows and API endpoints. 