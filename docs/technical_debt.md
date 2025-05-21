# Technical Debt and Future Improvements

This document lists known technical debt, areas for refactoring, and potential future improvements.

## ONGOING
assign judges


## TODO

Login revamp
contest details display
Arrows in view all in home are counterintuitive
mobile responsiveness
Front contest cards to display private/public
Error going from eval to open
Error going from open to closed directly
dashboard links do not point to the tab in question
Submitting texts, grey out or at least return the already submitted error.
Change defaults for contest creations. 
Make easier change contest status
Contest creator unknown
Username display in user submissions and in contest author.

## Admin Backend Endpoints Needed

* **User Management**:
  * Endpoint to fetch user's created contest count
  * Endpoint to track last user activity
  * Endpoint to delete a user

* **Credit Monitoring**:
  * Endpoint to track real USD cost per AI execution
  * Additional date filtering capabilities for credit usage (yearly)

* **Contests Management**:
  * Dedicated admin endpoints for contest management (delete, edit)
  * Contest text submissions count tracking

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