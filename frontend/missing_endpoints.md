# Missing Backend API Endpoints

This document lists backend API endpoints identified as missing or needing refinement during the development of the FastAPI frontend, based on the functionality present in the original Flask application.

## Pending Implementation / Refinement

3.  **Contest Password Check (Public Access to Private Contest)**
    *   **Frontend Page:** Contest Detail (`contest.html`), potentially Contest Password Entry (`enter_password.html`)
    *   **Purpose:** Allow users who are not admins or assigned judges to view a private contest if they provide the correct password.
    *   **Suggested Path:** Multiple options:
        *   Modify `GET /contests/{contest_id}` to accept an optional `X-Contest-Password` header or query parameter.
        *   Create a separate endpoint like `POST /contests/{contest_id}/verify-password`.
    *   **Expected Input:** Contest password.
    *   **Expected Output:** 
        *   If modifying GET: Contest details on success, 403 on failure.
        *   If separate POST: Success status (maybe setting a short-lived cookie/token specific to this contest) or 403 on failure.
    *   **Authorization:** Checks password against the specific contest's hash.
    *   **Notes:** Difficult to implement cleanly with standard token auth. Requires careful consideration of how access is granted temporarily. Backend `POST /contests/{contest_id}/check-password` exists, schema `ContestCheckPasswordRequest` defined. **Frontend wiring needed.**

---

## Implemented Endpoints

1.  **Create Submission** **[Backend DONE]**
    *   **Frontend Page:** Contest Detail (`contest.html`)
    *   **Purpose:** Allow users to submit text entries to an open contest.
    *   **Path:** `POST /contests/{contest_id}/submissions`
    *   **Input:** JSON body (e.g., `{ "author_name": "string", "title": "string", "text_content": "string" }` via `schemas.SubmissionCreate`)
    *   **Output:** 201 Created (`schemas.SubmissionRead`).
    *   **Authorization:** Contest status must be 'open', allows anonymous or authenticated users.
    *   **Notes:** Implemented in `contest.py`. **Frontend wiring needed.**

2.  **Submit Judge Evaluation/Votes** **[Backend DONE]**
    *   **Frontend Page:** Evaluate Contest (`evaluate.html`)
    *   **Purpose:** Allow assigned judges to submit their scores or rankings for all submissions in a contest.
    *   **Path:** `POST /contests/{contest_id}/evaluate`.
    *   **Input:** `List[schemas.VoteCreate]` (JSON array of objects with `submission_id`, `place`, `comment`).
    *   **Output:** 200 OK with success message.
    *   **Authorization:** Requires authenticated human judge user assigned to the specific contest, contest status must be 'evaluation'.
    *   **Notes:** Implemented in `contest.py`. **Frontend wiring needed.**

4.  **AI Cost Summary** **[DONE]**
    *   **Frontend Page:** AI Evaluation Costs (`admin_ai_costs.html`)
    *   **Purpose:** Display aggregated costs and token usage for AI judge evaluations and AI writing requests.
    *   **Path:** `GET /admin/ai-costs-summary`.
    *   **Input:** Optional `recent_limit` query parameter.
    *   **Output:** JSON object conforming to `schemas.AICostsSummary`.
    *   **Authorization:** Requires admin user.
    *   **Notes:** Implemented in `admin.py`. **Frontend wiring needed.**

5.  **Trigger AI Judge Evaluation** **[DONE]**
    *   **Frontend Page:** Admin Contest Detail (Future) or specific Admin Action
    *   **Purpose:** Allow an admin to manually trigger an AI judge's evaluation process for a contest.
    *   **Path:** `POST /admin/contests/{contest_id}/ai-judges/{ai_judge_id}/evaluate`.
    *   **Input:** None (Contest and Judge IDs from path).
    *   **Output:** `schemas.AIEvaluationDetail`.
    *   **Authorization:** Requires admin user.
    *   **Notes:** Refactored to `admin.py`. Corresponds to Flask page #12.

6.  **Create Human Judge User** **[DONE]**
    *   **Frontend Page:** Add Human Judge (`admin_add_judge.html` - To be created)
    *   **Purpose:** Allow admin to create a user with the 'judge' role and 'human' type.
    *   **Path:** `POST /admin/users/`.
    *   **Input:** JSON body via `schemas.UserCreate`.
    *   **Output:** 201 Created (`schemas.UserPublic`).
    *   **Authorization:** Requires admin user.
    *   **Notes:** Corresponds to Flask page #22. Implemented in `admin.py`.

7.  **Get AI Evaluation Details** **[DONE]**
    *   **Frontend Page:** View AI Evaluation (`admin_view_ai_evaluation.html` - To be created)
    *   **Purpose:** Allow admin to see the specifics of a single AI evaluation run (prompt, response, cost, votes created etc.).
    *   **Path:** `GET /admin/ai-evaluations/{evaluation_id}`
    *   **Input:** None (Path parameter).
    *   **Output:** `schemas.AIEvaluationDetail`.
    *   **Authorization:** Requires admin user.
    *   **Notes:** Implemented in `admin.py`. Corresponds to Flask page #28.

8.  **Reset/Set Contest Password** **[DONE]**
    *   **Frontend Page:** Reset Contest Password (`admin_reset_password.html` - To be created)
    *   **Purpose:** Allow admin to set or change the password for a private contest.
    *   **Path:** `PUT /admin/contests/{contest_id}/reset-password`.
    *   **Input:** JSON body via `schemas.ContestResetPasswordRequest`)
    *   **Output:** 200 OK.
    *   **Authorization:** Requires admin user.
    *   **Notes:** Implemented in `admin.py`. Corresponds to Flask page #18.

9.  **List Human Judges** **[DONE]**
    *   **Frontend Page:** Create/Edit Contest (`admin_contest_edit.html`)
    *   **Purpose:** Provide a list of available human judges to assign to a contest.
    *   **Path:** `GET /admin/users/`.
    *   **Input:** Optional query parameters (`role=judge`, `judge_type=human`).
    *   **Output:** List of `schemas.UserPublic`.
    *   **Authorization:** Requires admin user.
    *   **Notes:** Implemented in `admin.py`.