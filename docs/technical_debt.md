# Technical Debt and Future Improvements

This document lists known technical debt, areas for refactoring, and potential future improvements.

## ONGOING
AI input/output log
Review Writer I/O
Review Judge I/O
When deleting a user the transactions are lost from admin

## TODO
purchase credits? verify. We have a function for that, but not an endpoint nor a defined method.

AI writer: remove from header??


### else
Login revamp
contest details display
Arrows in view all in home are counterintuitive
mobile responsiveness
dashboard links do not point to the tab in question
Submitting texts, grey out or at least return the already submitted error.
Change defaults for contest creations. 
Username display in user submissions and in contest author.
-About Terms Privacy Footer
select inload optimization
other optimizations


🔧 Alternative: Fix the SPA Routing Issue
If you want to fix the direct URL typing issue completely, you would need to configure your web server (nginx, Apache, etc.) to serve the React app for all routes that don't exist on the server. This is typically done with a "catch-all" rule that serves index.html for any route that doesn't match a file. 🎉


## Admin Backend Endpoints Needed

* **User Management**:
  * Endpoint to track last user activity - **PLANNED (Backend: Add `last_seen_at` to User model, update via middleware. Frontend: `AdminUsersPage.tsx` ready to display `user.last_seen`)**


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