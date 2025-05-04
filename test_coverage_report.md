# API Test Coverage Report (E2E)

This report compares the endpoints exercised in the E2E tests (`/tests` directory) against the features defined in `api_roles_and_features.md` and the routers present in `backend/app/routers`.

## Tested Endpoint Paths Summary

The following base paths and specific actions were identified in `tests/test_ai_agents_e2e.py`, `tests/test_ai_costs_e2e.py`, and `tests/test_workflow_e2e.py`:

*   `/auth/register` (POST)
*   `/auth/token` (POST)
*   `/auth/users/me` (GET)
*   `/contests/` (GET, POST)
*   `/contests/{contest_id}` (GET (implicit), PUT, DELETE)
*   `/contests/{contest_id}/check-password` (POST)
*   `/contests/{contest_id}/submissions` (GET (non-judge), POST)
*   `/ai-writers/` (GET, POST, PUT, DELETE)
*   `/ai-writers/{writer_id}` (GET, PUT, DELETE)
*   `/ai-writers/{writer_id}/generate` (POST)
*   `/ai-judges/` (GET, POST, PUT, DELETE)
*   `/ai-judges/{judge_id}` (GET, PUT, DELETE)
*   `/ai-judges/{judge_id}/evaluate` (POST)
*   `/admin/users/{user_id}` (DELETE)
*   `/admin/users/{user_id}/credits` (PUT)
*   `/admin/users/{user_id}/credit-history` (GET)

## Comparison with `api_roles_and_features.md`

**Key:**
*   `[x]` - Feature listed in spec.
*   **(T)** - Tested (at least partially) by E2E tests.
*   **(U)** - Untested by E2E tests.
*   **(P)** - Partially tested (some aspects tested, others not).

### Public Features
*   `[x]` List All Contests (`GET /contests/`) - **(T)**
*   `[x]` View Public Contest Details (`GET /contests/{contest_id}`) - **(P)** (Implicitly tested)
*   `[x]` View Private Contest Details (with password) - **(P)** (`check-password` tested, GET with cookie not)
*   `[x]` Register New Account (`POST /auth/register`) - **(T)**
*   `[x]` Login (`POST /auth/token`) - **(T)**

### Authenticated Features (User, Admin)
*   **Account:**
    *   `[x]` View Own Basic User Info (`GET /auth/users/me`) - **(T)**
    *   `[ ]` View Own Credit Balance (Part of `GET /auth/users/me`) - **(T)**
*   **Contests:**
    *   `[x]` Create Contest (`POST /contests/`) - **(T)**
    *   `[ ]` Set Contest Restrictions - **(P)** (Private/password tested, others not)
    *   `[x]` Edit Own Contest (`PUT /contests/{contest_id}`) - **(T)**
    *   `[x]` Delete Own Contest (`DELETE /contests/{contest_id}`) - **(T)**
    *   `[t]` Submit Text to Open Contest (`POST /contests/{contest_id}/submissions`) - **(T)**
    *   `[ ]` Enforce Contest Restrictions (Submission limits) - **(U)**
    *   `[t]` Submit Votes/Evaluation (Human Judge) (`POST /contests/{contest_id}/evaluate`) - **(U)**
    *   `[t]` View Submissions (as Judge) (`GET /contests/{contest_id}/submissions`) - **(P)** (Non-judge 403 tested, judge view not)
    *   `[t]` Delete Own Text Submission (`DELETE /submissions/{submission_id}`) - **(U)**
*   **AI Agents (User-Owned):** (All marked `[t]` in spec)
    *   Create/List/View/Update/Delete Own AI Writer - **(T)**
    *   Create/List/View/Update/Delete Own AI Judge - **(T)**
    *   Execute AI Writer Action (`.../generate`) - **(T)**
    *   Execute AI Judge Action (`.../evaluate`) - **(T)**
*   **User Dashboard/View:** - **(U)**

### Admin-Only Features
*   **User Management:**
    *   `[t]` List Users (`GET /admin/users/`) - **(U)**
    *   `[p]` Create User (`POST /admin/users/`) - **(U)**
    *   `[ ]` Edit User (Roles/Details) - **(U)**
    *   `[t]` Assign/Modify User Credits (`PUT /admin/users/{user_id}/credits`) - **(T)**
    *   `[x]` Delete User (`DELETE /admin/users/{user_id}`) - **(T)**
*   **Contest Management:**
    *   `[p]` View Any Contest Details (`GET /contests/{contest_id}`) - **(U)**
    *   `[x]` Update Any Contest (`PUT /contests/{contest_id}`) - **(U)**
    *   `[x]` Delete Any Contest (`DELETE /contests/{contest_id}`) - **(P)** (Tested only implicitly via user cascade delete)
    *   `[t]` Set Contest Status (`PUT /admin/contests/{contest_id}/status`) - **(U)**
    *   `[t]` Reset Private Contest Password (`PUT /admin/contests/{contest_id}/reset-password`) - **(U)**
    *   `[t]` Assign/Unassign Human User as Judge - **(U)**
    *   `[t]` Assign/Unassign AI Judge to Contest - **(U)**
    *   `[t]` Delete Any Submission (`DELETE /admin/submissions/{submission_id}`) - **(U)**
    *   `[p]` Add Submission Anytime (Admin) - **(U)**
    *   `[p]` Add Vote Anytime (Admin) - **(U)**
*   **AI Agent Management (Global):** (Admin actions via non-admin paths tested)
    *   `[t]` List AI Writers/Judges (Admin) - **(T)**
    *   `[t]` Create AI Writer/Judge (Admin) (`POST /admin/...`) - **(U)**
    *   `[t]` Get AI Writer/Judge Details (Admin) - **(T)**
    *   `[t]` Update AI Writer/Judge (Admin) - **(T)**
    *   `[t]` Delete AI Writer/Judge (Admin) - **(T)**
*   **AI Execution & Monitoring:**
    *   `[t]` Trigger AI Judge Evaluation (Admin) - **(U)**
    *   `[t]` Trigger AI Submission Generation (Admin) - **(U)**
    *   `[t]` List/Get AI Evaluation Results - **(U)**
    *   `[t]` Get AI Costs Summary - **(U)**
    *   `[t]` View User Credit Consumption (`GET /admin/users/{user_id}/credit-history`) - **(T)**
*   **Site Overview:** - **(U)**
*   **Miscellaneous:** (`/roadmap/...`, etc) - **(U)**

## Missing Coverage & Potential Improvements

*   **Admin Functionality:** The most significant gap is in testing admin-specific endpoints and permissions, particularly for contest management, explicit user management (list, create, edit), AI execution/monitoring, and global AI agent management via designated `/admin/...` paths.
*   **Role-Specific Logic:** Tests covering specific user roles (like Judges viewing/evaluating submissions) and contest restriction enforcement (submission limits) are missing.
*   **Submission Management:** Deleting submissions (by users or admins) is untested.
*   **Edge Cases:** Current tests focus on primary workflows. Adding tests for error conditions, invalid inputs, race conditions, and specific status code verification would improve robustness.
*   **Dashboard & Miscellaneous:** Endpoints supporting the user dashboard and miscellaneous features (like roadmap) are not covered.

## Untested Routers

Based on the tested endpoints and the router files present:

*   **`backend/app/routers/admin.py`:** While some user-related admin actions are tested, the majority of endpoints defined in this router (contest management, full user management, AI monitoring, etc.) lack corresponding E2E tests.
*   **`backend/app/routers/submission.py`:** Specific endpoints for managing individual submissions (like DELETE `/submissions/{id}`) are likely defined here and are not tested.
*   **`backend/app/routers/main.py`:** Contains untested endpoints, potentially including root paths, site summaries, or miscellaneous features like `/roadmap`.

## Recommendations

1.  **Prioritize Admin Tests:** Create dedicated E2E tests for the `/admin/...` routes covering user management, contest management, AI monitoring, and global AI agent actions.
2.  **Test Judge Role:** Implement tests simulating a user assigned as a judge to verify contest evaluation (`POST /contests/{id}/evaluate`), submission viewing (`GET /contests/{id}/submissions`), and potentially other judge-specific actions.
3.  **Test Submission Deletion:** Add tests for `DELETE /submissions/{submission_id}` for both users (own submission) and admins.
4.  **Expand Contest Logic Tests:** Include tests for contest restrictions like submission limits.
5.  **Cover `main.py`:** Investigate endpoints in `main.py` and add tests if necessary.
6.  **Enhance Existing Tests:** Add more assertions for specific response data, error codes, and edge-case scenarios to existing tests. 