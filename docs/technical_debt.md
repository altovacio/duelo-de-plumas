# Technical Debt and Future Improvements

This document lists known technical debt, areas for refactoring, and potential future improvements.

## ONGOING
-Test high load users, contests, texts, etc.

-Pagination in Contest list
-Dashboard
-Admin

Admin -> search for users when paginated
Contests oversight table redesign

## TODO

-Test deleting elements (users, contests, etc.)
-Header & pages redesign  (user flow)
-Footer
-Mobile responsiveness
-Login via email (cursor style)
-Credit purchasing
-What should we do when the parsing or AI execution fails? Retries, exceptions (if the platform is broken, prevent the users from spending resources? Refund?)
-initial setup
-Test high load users, contests, texts, etc.

-Credit spenditure revisit

-PDF stuff

-Better experience full page writer
   -marktwo migration

-style


-other optimizations
-Unit tests

-English/Spanish


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