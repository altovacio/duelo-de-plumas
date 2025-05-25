# Technical Debt and Future Improvements

This document lists known technical debt, areas for refactoring, and potential future improvements.

## ONGOING
credits - In admin dashboard, they are starting to work but no transactions are being shown. Also the total spent is rounded and misaligned
Credits- The total in admin dashboard is reduced when the users spend them. 
## TODO
### Dashboard
My PArticipation: is broken


AI writer: remove from header??

#### Credit Monitoring Implementation Plan

The Credit Monitoring page needs to be fully implemented to provide administrators with insights into credit usage across the platform. Here is the implementation plan:

1. **Backend API Endpoints**
   - Ensure `/admin/credits/transactions` endpoint is working properly with filtering by user, date range, and transaction type
   - Implement `/admin/credits/usage` endpoint to provide summary statistics on credit usage by user and agent type
   - Add proper pagination and sorting capabilities to both endpoints

2. **Frontend Implementation**
   - Complete the `AdminMonitoringPage.tsx` component by:
     - Replacing mock data with real API calls to fetch credit usage information
     - Implementing proper date range filtering
     - Adding user and model filtering capabilities
     - Creating visual charts/graphs showing usage trends over time
     - Adding export functionality for CSV/Excel download of credit usage data

3. **Credit Transaction History**
   - Implement the transaction history view in the user dashboard's credit tab
   - Show detailed information about credit additions, deductions, and usage
   - Allow users to filter their own transaction history

4. **Real-time Credit Monitoring**
   - Add WebSocket support for real-time updates on credit usage
   - Create notifications for administrators when credit usage exceeds certain thresholds
   - Implement automatic alerting when system-wide credit consumption increases abnormally

5. **Cost Analysis Tools**
   - Develop tools to analyze the relationship between credits and actual costs
   - Provide recommendations for optimizing credit usage based on patterns
   - Create forecasting tools to predict future credit needs

This implementation will enable administrators to properly monitor and manage the credit system, ensuring both transparency for users and cost control for the platform.




### else
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
Username display in user submissions and in contest author.
-About Terms Privacy Footer


## Admin Backend Endpoints Needed

* **User Management**:
  * Endpoint to fetch user's created contest count - **NEEDS VERIFICATION (Backend to provide `contests_created` in `/admin/users` response; Frontend `AdminUsersPage.tsx` ready to display `user.contests_created || 0`)**
  * Endpoint to track last user activity - **PLANNED (Backend: Add `last_seen_at` to User model, update via middleware. Frontend: `AdminUsersPage.tsx` ready to display `user.last_seen`)**
  * ~~Endpoint to delete a user - **EXISTS (`DELETE /users/{user_id}` for admins)**~~ **DONE (Frontend Connected)**

* **Credit Monitoring**:
  * Endpoint to track real USD cost per AI execution - **PARTIALLY EXISTS (Data available via `GET /admin/credits/usage`, `GET /admin/credits/transactions`, and `GET /models/{model_id}` for pricing; direct per-execution USD cost might be a new derived data point)**
  * Additional date filtering capabilities for credit usage (yearly) - **POTENTIALLY EXISTS (via `GET /admin/credits/transactions` if filtering is flexible); otherwise, an ENHANCEMENT**

* **Contests Management**:
  * ~~Dedicated admin endpoints for contest management (delete, edit) - **EXIST (`PUT /contests/{contest_id}` and `DELETE /contests/{contest_id}` for admins)**~~ **DONE (Frontend Connected)**
  * ~~Contest text submissions count tracking - **EXISTS (`GET /contests/{contest_id}` returns text counts)**~~ **DONE (Covered by existing Contest type and display)**

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