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
*   `[p]` - Partially Implemented / Needs Refinement (Endpoint exists but needs role/logic adjustment)
*   `[ ]` - Not Implemented

### Visitor, User and Admin Features

*   `[p]` List All Contest (`GET /contests/`) --Remove login lock
*   `[p]` View Public Contest Details (`GET /contests/{contest_id}`) --Remove login lock
*   `[p]` View Private Contest Details (with password) (`GET /contests/{contest_id}` + `POST /contests/{contest_id}/check-password`) --Remove login lock
*   `[x]` Register New Account (`POST /auth/register`)
*   `[x]` Login (`POST /auth/token`)

### User and Admin Features
*   All previous plus:

*   **Account:**
    *   `[p]` View Own User Info (`GET /auth/users/me`) --Is this all the info we need?
*   **Contests:**
    *   `[p]` Create Contest (`POST /contests/` - Needs user access)
    *   `[p]` Edit Own Contest (`PUT /contests/{contest_id}` - Needs user/owner access)
    *   `[p]` Delete Own Contest (`DELETE /contests/{contest_id}` - Needs user/owner access)
    *   `[p]` Submit Text to Open Contest (`POST /contests/{contest_id}/submissions`) Needs user access
    *   `[p]` Submit Votes/Evaluation (if assigned as Judge) (`POST /contests/{contest_id}/evaluate` - Needs check for user assignment as judge)
    *   `[p]` View Submissions (if assigned as Judge during Evaluation/Closed) (`GET /contests/{contest_id}/submissions` - Needs refinement for user-judge access)
    *   `[p]` Delete Own Text Submission (`DELETE /admin/submissions/{submission_id}` - Needs user/owner access + state logic)
*   **AI Agents (User-Owned):**
    *   `[ ]` Create Own AI Writer
    *   `[ ]` List Own AI Writers
    *   `[ ]` View Own AI Writer Details
    *   `[ ]` Update Own AI Writer
    *   `[ ]` Delete Own AI Writer
    *   `[ ]` Create Own AI Judge
    *   `[ ]` List Own AI Judges
    *   `[ ]` View Own AI Judge Details
    *   `[ ]` Update Own AI Judge
    *   `[ ]` Delete Own AI Judge
    *   `[ ]` Request AI Writer Action (for Admin approval)
    *   `[ ]` Request AI Judge Action (for Admin approval)
*   **User Dashboard/View:**
    *   `[ ]` View contests participated in (as author/judge)
    *   `[ ]` View own submitted texts
    *   `[ ]` View urgent actions (e.g., contests needing evaluation)

### Admin Features

*   **User Management:**
    *   `[x]` List Users (`GET /admin/users/`)
    *   `[p]` Create User (`POST /admin/users/` - Currently creates 'Judge'. Now is only user or admin)
    *   `[ ]` Edit User (Roles/Details)
    *   `[ ]` Delete User
*   **Contest Management:**
    *   `[x]` View Any Contest Details overriding password (`GET /admin/contests/{contest_id}`)
    *   `[x]` Update Any Contest (`PUT /contests/{contest_id}`)
    *   `[x]` Delete Any Contest (`DELETE /contests/{contest_id}`)
    *   `[x]` Set Contest Status (`PUT /admin/contests/{contest_id}/status`)
    *   `[x]` Reset Private Contest Password (`PUT /admin/contests/{contest_id}/reset-password`)
    *   `[x]` Assign Human User as Judge (`POST /admin/contests/{contest_id}/human-judges/{user_id}`)
    *   `[x]` Unassign Human User as Judge (`DELETE /admin/contests/{contest_id}/human-judges/{user_id}`)
    *   `[x]` Assign AI Judge to Contest (`POST /admin/contests/{contest_id}/ai-judges/{ai_judge_id}`)
    *   `[x]` Unassign AI Judge from Contest (`DELETE /admin/contests/{contest_id}/ai-judges/{ai_judge_id}`)
    *   `[x]` Delete Any Submission (`DELETE /admin/submissions/{submission_id}`)
    *   `[p]` Add Submission Anytime (Requires logic check in `POST /contests/{contest_id}/submissions`)
    *   `[p]` Add Vote Anytime (Requires logic check in `POST /contests/{contest_id}/evaluate`)
*   **AI Agent Management (Global):**
    *   `[x]` List AI Writers (`GET /admin/ai-writers`)
    *   `[x]` Create AI Writer (`POST /admin/ai-writers`)
    *   `[x]` Get AI Writer Details (`GET /admin/ai-writers/{writer_id}`)
    *   `[x]` Update AI Writer (`PUT /admin/ai-writers/{writer_id}`)
    *   `[x]` Delete AI Writer (`DELETE /admin/ai-writers/{writer_id}`)
    *   `[x]` List AI Judges (`GET /admin/ai-judges`)
    *   `[x]` Create AI Judge (`POST /admin/ai-judges`)
    *   `[x]` Get AI Judge Details (`GET /admin/ai-judges/{ai_judge_id}`)
    *   `[x]` Update AI Judge (`PUT /admin/ai-judges/{ai_judge_id}`)
    *   `[x]` Delete AI Judge (`DELETE /admin/ai-judges/{ai_judge_id}`)
*   **AI Execution & Monitoring:**
    *   `[x]` Trigger AI Judge Evaluation (`POST /admin/contests/{contest_id}/ai-judges/{ai_judge_id}/evaluate`)
    *   `[x]` Trigger AI Submission Generation (`POST /admin/contests/{contest_id}/ai-submission`)
    *   `[x]` List AI Evaluation Results (`GET /admin/ai-evaluations`)
    *   `[x]` Get AI Evaluation Details (`GET /admin/ai-evaluations/{evaluation_id}`)
    *   `[x]` Get AI Costs Summary (`GET /admin/ai-costs-summary`)
    *   `[ ]` List User AI Action Requests
*   **Site Overview:**
    *   `[ ]` Site Summary/Dashboard (Num contests, frequent winners, etc.) 