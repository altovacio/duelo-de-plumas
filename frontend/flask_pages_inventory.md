# Flask Application Page Inventory

This document lists the user-facing pages identified in the original Flask application (`app/`) to guide the development of the new FastAPI frontend (`frontend/`).

## Main Blueprint (`app/main/routes.py`)

1.  **Route:** `/` or `/index` **[DONE]**
    *   **Template:** `main/index.html`
    *   **Purpose:** Main dashboard/homepage. Displays active/closed contests, judge evaluation queue, admin alerts (pending AI eval, expired open contests).
2.  **Route:** `/contests` **[DONE]**
    *   **Template:** `main/contests.html`
    *   **Purpose:** Public listing of all contests, categorized by status (Open, Expired Open, Evaluation, Closed). (Note: Evaluation contests need API update for full parity).
3.  **Route:** `/roadmap` **[DONE]**
    *   **Template:** `main/roadmap.html`
    *   **Purpose:** Internal/hidden page displaying the development roadmap.

## Auth Blueprint (`app/auth/routes.py`)

4.  **Route:** `/auth/login` **[DONE]**
    *   **Template:** `auth/login.html`
    *   **Purpose:** User login form (username/email + password).
5.  **Route:** `/auth/logout` **[DONE]**
    *   **Template:** None (Redirect)
    *   **Purpose:** Logs the current user out.
6.  **Route:** `/auth/register` **[DONE]**
    *   **Template:** `auth/register.html`
    *   **Purpose:** User registration form. First user becomes admin, others become judges.

## Contest Blueprint (`app/contest/routes.py`)

7.  **Route:** `/contest/<int:contest_id>` **[DONE - View]**
    *   **Template:** `contest/detail.html`
    *   **Purpose:** View contest details. Allows submission if open & user permitted (public/private password). Shows results/votes if closed. 
    *   **Notes:** Submission form needs wiring to the `POST /contests/{id}/submissions` backend endpoint.
8.  **Route:** `/contest/<int:contest_id>/password` **[BLOCKED]**
    *   **Template:** `contest/enter_password.html`
    *   **Purpose:** Form to enter the password for a private contest. (Needs Contest Password Check API).
9.  **Route:** `/contest/<int:contest_id>/check-password` (POST) **[BLOCKED]**
    *   **Template:** None (Redirect)
    *   **Purpose:** Handles password submission for private contests. (Needs Contest Password Check API).
10. **Route:** `/contest/<int:contest_id>/submissions` **[DONE]**
    *   **Template:** `contest/list_submissions.html`
    *   **Purpose:** Judge/Admin view to see all submissions for a contest (during evaluation or closed). Shows AI judge voting status.
11. **Route:** `/contest/<int:contest_id>/evaluate` **[BLOCKED]**
    *   **Template:** `contest/evaluate_contest.html`
    *   **Purpose:** Judge view to submit rankings/votes for all submissions in a contest. (Needs Submit Evaluation API).
12. **Route:** `/contest/<int:contest_id>/run_ai_evaluation/<int:judge_id>` (POST) **[TODO - Backend]**
    *   **Template:** None (Redirect/Background Task?)
    *   **Purpose:** Admin action to trigger AI evaluation for a specific AI judge. (Needs dedicated API, e.g., POST /admin/contests/{id}/trigger-ai-evaluation/{judge_id}).

## Admin Blueprint (`app/admin/routes.py`)

13. **Route:** `/admin/` **[DONE]**
    *   **Template:** `admin/index.html`
    *   **Purpose:** Main admin dashboard/landing page.
14. **Route:** `/admin/contests` **[DONE]**
    *   **Template:** `admin/list_contests.html`
    *   **Purpose:** List all contests with management options (edit, delete, status).
15. **Route:** `/admin/contests/create` **[DONE]**
    *   **Template:** `admin/edit_contest.html`
    *   **Purpose:** Form to create a new contest, including assigning judges (human/AI + model). (Note: Human judge list/assignment needs API).
16. **Route:** `/admin/contests/<int:contest_id>/edit` **[DONE]**
    *   **Template:** `admin/edit_contest.html`
    *   **Purpose:** Form to edit an existing contest. (Note: Human judge list/assignment needs API).
17. **Route:** `/admin/contests/<int:contest_id>/delete` (POST) **[DONE]**
    *   **Template:** None (Redirect)
    *   **Purpose:** Deletes a contest. (Backend exists: DELETE /contests/{id}, Frontend implemented in admin_contests.js).
18. **Route:** `/admin/contests/<int:contest_id>/reset-password` **[BLOCKED]**
    *   **Template:** `admin/reset_contest_password.html` (Likely)
    *   **Purpose:** Form to set/reset the password for a private contest. (Needs dedicated API? Or part of PUT /contests/{id}?).
19. **Route:** `/admin/contests/<int:contest_id>/set_status` (POST) **[DONE]**
    *   **Template:** None (Redirect)
    *   **Purpose:** Changes the status (open, evaluation, closed) of a contest. (Backend exists: PUT /contests/{id}, Frontend implemented in admin_contests.js).
20. **Route:** `/admin/contests/<int:contest_id>/submissions` **[DONE]**
    *   **Template:** `admin/list_submissions.html` (Likely)
    *   **Purpose:** Admin view of submissions for a contest (potentially with delete option). (Covered by Page 10 + Page 21 delete action).
21. **Route:** `/admin/submissions/<int:submission_id>/delete` (POST) **[DONE]**
    *   **Template:** None (Redirect)
    *   **Purpose:** Deletes a specific submission. (Backend exists: DELETE /admin/submissions/{id}, Frontend implemented in submissions.js).
22. **Route:** `/admin/users/add_judge` **[TODO - Backend]**
    *   **Template:** `admin/add_judge.html`
    *   **Purpose:** Form to create a new human judge user. (Needs POST /admin/users/ API or similar).
23. **Route:** `/admin/users/ai_judges` **[DONE]**
    *   **Template:** `admin/list_ai_judges.html`
    *   **Purpose:** List configured AI judge profiles.
24. **Route:** `/admin/users/add_ai_judge` **[DONE]**
    *   **Template:** `admin/add_ai_judge.html`
    *   **Purpose:** Form to create a new AI judge profile. (Note: Fix 405 error by restarting server).
25. **Route:** `/admin/users/edit_ai_judge/<int:judge_id>` **[DONE]**
    *   **Template:** `admin/edit_ai_judge.html`
    *   **Purpose:** Form to edit an existing AI judge profile.
26. **Route:** `/admin/users/delete_ai_judge/<int:judge_id>` (POST) **[DONE]**
    *   **Template:** None (Redirect)
    *   **Purpose:** Deletes an AI judge profile. (Backend exists: DELETE /admin/ai-judges/{id}, Frontend implemented).
27. **Route:** `/admin/ai_evaluation_costs` **[BLOCKED]**
    *   **Template:** `admin/ai_evaluation_costs.html`
    *   **Purpose:** Display calculated costs for AI judge evaluations. (Needs AI Cost Summary API).
28. **Route:** `/admin/ai_evaluation/<int:evaluation_id>` **[TODO - Backend]**
    *   **Template:** `admin/view_ai_evaluation.html`
    *   **Purpose:** View the details/results of a specific AI evaluation run. (Needs GET /admin/ai-evaluations/{id} API).
29. **Route:** `/admin/users/ai_writers` **[DONE]**
    *   **Template:** `admin/list_ai_writers.html`
    *   **Purpose:** List configured AI writer profiles.
30. **Route:** `/admin/users/add_ai_writer` **[DONE]**
    *   **Template:** `admin/add_ai_writer.html`
    *   **Purpose:** Form to create a new AI writer profile. (Note: Fix 405 error by restarting server).
31. **Route:** `/admin/users/edit_ai_writer/<int:writer_id>` **[DONE]**
    *   **Template:** `admin/edit_ai_writer.html`
    *   **Purpose:** Form to edit an existing AI writer profile.
32. **Route:** `/admin/users/delete_ai_writer/<int:writer_id>` (POST) **[DONE]**
    *   **Template:** None (Redirect)
    *   **Purpose:** Deletes an AI writer profile. (Backend exists: DELETE /admin/ai-writers/{id}, Frontend implemented).
33. **Route:** `/admin/contests/<int:contest_id>/ai_submission` **[TODO - Frontend]**
    *   **Template:** `admin/ai_submission.html`
    *   **Purpose:** Admin interface to trigger AI text generation for a submission within a specific contest. (Backend exists: POST /admin/contests/{id}/ai-submission). 