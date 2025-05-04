# API Roles and Feature Status

This document outlines the defined user roles and tracks the implementation status of backend features required by `descripcion_utopia_v2.md`.

## Defined Roles

*   **Visitor:** Anyone accessing the site without logging in.
*   **User:** A registered user with a free account. Can create/manage their own content and participate in contests.
*   **Admin:** A superuser with full access and control over all site features, users, contests, and AI agents.

## Feature Implementation Status

*(Based on `descripcion_utopia_v2.md` requirements and `endpoints_summary.md` analysis)*

**Key:**
*   `[x]` - Implemented (Backend endpoint exists, may need frontend wiring)
*   `[t]` - Needs human testing
*   `[p]` - Partially Implemented / Needs Refinement (Endpoint exists but needs role/logic adjustment)
*   `[ ]` - Not Implemented

### Public Features (Visitor, User, Admin)

*   `[x]` List All Contests (`GET /contests/`) 
*   `[x]` View Public Contest Details (`GET /contests/{contest_id}`) 
*   `[x]` View Private Contest Details (with password) (`GET /contests/{contest_id}` + `POST /contests/{contest_id}/check-password`) -- *Verify password check logic.*
*   `[x]` Register New Account (`POST /auth/register`)
*   `[x]` Login (`POST /auth/token`)

### Authenticated Features (User, Admin)
*   All Public Features plus:

*   **Account:**
    *   `[x]` View Own Basic User Info (`GET /auth/users/me`) 
    *   `[ ]` View Own Credit Balance (Part of `GET /auth/users/me`)
*   **Contests:**
    *   `[x]` Create Contest (`POST /contests/`)
    *   `[ ]` Set Contest Restrictions (Judge participation, submission limits) (Part of `POST /contests/` & `PUT /contests/{contest_id}`)
    *   `[x]` Edit Own Contest (`PUT /contests/{contest_id}`)
    *   `[x]` Delete Own Contest (`DELETE /contests/{contest_id}`)
    *   `[t]` Submit Text to Open Contest (`POST /contests/{contest_id}/submissions` - Needs user role check)
    *   `[ ]` Enforce Contest Restrictions (Judge participation, submission limits) (Part of `POST /contests/{contest_id}/submissions`)
    *   `[t]` Submit Votes/Evaluation (if assigned as Judge) (`POST /contests/{contest_id}/evaluate` - Needs check for user assignment as judge for the contest)
    *   `[t]` View Submissions (if assigned as Judge during Evaluation/Closed) (`GET /contests/{contest_id}/submissions` - Needs refinement for user-judge access based on contest state)
    *   `[t]` Delete Own Text Submission (`DELETE /submissions/{submission_id}` - Needs user/owner access check + state logic)
*   **AI Agents (User-Owned):**
    *   `[t]` Create Own AI Writer
    *   `[t]` List Own AI Writers
    *   `[t]` View Own AI Writer Details
    *   `[t]` Update Own AI Writer
    *   `[t]` Delete Own AI Writer
    *   `[t]` Create Own AI Judge
    *   `[t]` List Own AI Judges
    *   `[t]` View Own AI Judge Details
    *   `[t]` Update Own AI Judge
    *   `[t]` Delete Own AI Judge
    *   `[t]` Execute AI Writer Action (Consumes Credits) (`POST /ai-writers/{writer_id}/generate`) [Implemented]
    *   `[t]` Execute AI Judge Action (Consumes Credits) (`POST /ai-judges/{judge_id}/evaluate`) [Implemented]
*   **User Dashboard/View:**
    *   `[ ]` View contests participated in (as author/judge)
    *   `[ ]` View own submitted texts
    *   `[ ]` View urgent actions (e.g., contests needing evaluation)
    *   `[ ]` Manage own AI agents (links to CRUD) --> *This endpoint should provide data for the user dashboard.*

### Admin-Only Features

*   All Public and Authenticated Features plus:
*   **User Management:**
    *   `[t]` List Users (`GET /admin/users/`) (Update to include credits)
    *   `[p]` Create User (`POST /admin/users/` - Needs update to create 'user' or 'admin' roles, not 'Judge', sets initial credits to 0)
    *   `[ ]` Edit User (Roles/Details) 
    *   `[t]` Assign/Modify User Credits (`PUT /admin/users/{user_id}/credits`)
    *   `[x]` Delete User (`DELETE /admin/users/{user_id}`)
*   **Contest Management:**
    *   `[p]` View Any Contest Details (`GET /contests/{contest_id}`) -- *Ensure Admin overrides privacy/password.*
    *   `[x]` Update Any Contest (`PUT /contests/{contest_id}`)
    *   `[x]` Delete Any Contest (`DELETE /contests/{contest_id}`)
    *   `[t]` Set Contest Status (`PUT /admin/contests/{contest_id}/status`)
    *   `[t]` Reset Private Contest Password (`PUT /admin/contests/{contest_id}/reset-password`)
    *   `[t]` Assign Human User as Judge (`POST /admin/contests/{contest_id}/human-judges/{user_id}`)
    *   `[t]` Unassign Human User as Judge (`DELETE /admin/contests/{contest_id}/human-judges/{user_id}`)
    *   `[t]` Assign AI Judge to Contest (`POST /admin/contests/{contest_id}/ai-judges/{ai_judge_id}`)
    *   `[t]` Unassign AI Judge from Contest (`DELETE /admin/contests/{contest_id}/ai-judges/{ai_judge_id}`)
    *   `[t]` Delete Any Submission (`DELETE /admin/submissions/{submission_id}`)
    *   `[p]` Add Submission Anytime (Requires logic check in `POST /contests/{contest_id}/submissions`)
    *   `[p]` Add Vote Anytime (Requires logic check in `POST /contests/{contest_id}/evaluate`)
*   **AI Agent Management (Global):**
    *   `[t]` List AI Writers (`GET /admin/ai-writers`)
    *   `[t]` Create AI Writer (`POST /admin/ai-writers`)
    *   `[t]` Get AI Writer Details (`GET /admin/ai-writers/{writer_id}`)
    *   `[t]` Update AI Writer (`PUT /admin/ai-writers/{writer_id}`)
    *   `[t]` Delete AI Writer (`DELETE /admin/ai-writers/{writer_id}`)
    *   `[t]` List AI Judges (`GET /admin/ai-judges`)
    *   `[t]` Create AI Judge (`POST /admin/ai-judges`)
    *   `[t]` Get AI Judge Details (`GET /admin/ai-judges/{ai_judge_id}`)
    *   `[t]` Update AI Judge (`PUT /admin/ai-judges/{ai_judge_id}`)
    *   `[t]` Delete AI Judge (`DELETE /admin/ai-judges/{ai_judge_id}`)
*   **AI Etecution & Monitoring:**
    *   `[t]` Trigger AI Judge Evaluation (`POST /admin/contests/{contest_id}/ai-judges/{ai_judge_id}/evaluate`)
    *   `[t]` Trigger AI Submission Generation (`POST /admin/contests/{contest_id}/ai-submission`)
    *   `[t]` List AI Evaluation Results (`GET /admin/ai-evaluations`)
    *   `[t]` Get AI Evaluation Details (`GET /admin/ai-evaluations/{evaluation_id}`)
    *   `[t]` Get AI Costs Summary (`GET /admin/ai-costs-summary`) 
    *   `[t]` View User Credit Consumption (`GET /admin/users/{user_id}/credit-history`)
*   **Site Overview:**
    *   `[ ]` Site Summary/Dashboard (Num contests, frequent winners, etc.)

### Miscellaneous / Out of Scope?

*   `[?t]` Get roadmap items (`GET /roadmap/items`)
*   `[?t]` Add roadmap item (`POST /roadmap/item`)
*   `[?t]` Delete roadmap item (`DELETE /roadmap/item/{item_id}`)
*   `[?t]` Update roadmap item status (`PUT /roadmap/item/{item_id}/status`)
*   `[?t]` List recent submissions (Global?) (`GET /submissions/` in `main.py`) -- *Likely redundant?*
*   `[?t]`