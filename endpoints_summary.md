# Backend Endpoint Summary (Generated)

This document summarizes the current state of the FastAPI backend endpoints based on an analysis of the router files (`backend/app/routers/`).

## Router Files Analyzed

*   `admin.py`
*   `ai_router.py`
*   `auth.py`
*   `contest.py`
*   `main.py`
*   ~~`contests.py`~~ (Deleted - Redundant)

## Key Findings

*   **Redundancy:** `contests.py` appeared to be an older, redundant version of `contest.py` and has been deleted.
*   **Implemented Endpoints:** Several endpoints listed as missing or corresponding to Flask pages were found already implemented, primarily in `admin.py` and `contest.py`.
*   **Undocumented Endpoints:** Some utility or dashboard-related endpoints exist (`/dashboard-data`, `/submissions/`, Roadmap endpoints in `main.py`) that were not directly mapped from the Flask inventory or missing list.
*   **Internal Endpoints:** `ai_router.py` seems to contain endpoints (`/generate-text`) likely intended for internal service calls or admin triggers, rather than direct frontend use. The `/evaluate-contest` endpoint was moved to `admin.py`.

## Existing Endpoints Table

| Method | Path                                                      | Summary/Purpose                     | Auth Level | Router File |
| :----- | :-------------------------------------------------------- | :---------------------------------- | :--------- | :---------- |
| **GET**  | `/`                                                       | Main root (placeholder)             | Public     | `main.py`     |
| **GET**  | `/submissions/`                                           | List recent submissions             | Public     | `main.py`     |
| **GET**  | `/dashboard-data`                                         | Get data for main dashboard         | Optional   | `main.py`     |
| **GET**  | `/roadmap/items`                                          | Get roadmap items                   | Public     | `main.py`     |
| **POST** | `/roadmap/item`                                           | Add roadmap item                    | Public (?) | `main.py`     |
| **DELETE**| `/roadmap/item/{item_id}`                                 | Delete roadmap item                 | Public (?) | `main.py`     |
| **PUT**  | `/roadmap/item/{item_id}/status`                          | Update roadmap item status          | Public (?) | `main.py`     |
| **POST** | `/auth/token`                                             | Login for access token              | Public     | `auth.py`     |
| **GET**  | `/auth/users/me`                                          | Get current authenticated user      | User       | `auth.py`     |
| **POST** | `/auth/register`                                          | Register new user                   | Public     | `auth.py`     |
| **POST** | `/contests/`                                              | Create contest                      | Admin      | `contest.py`  |
| **GET**  | `/contests/`                                              | List contests                       | Optional   | `contest.py`  |
| **GET**  | `/contests/{contest_id}`                                  | Get contest details                 | Optional   | `contest.py`  |
| **PUT**  | `/contests/{contest_id}`                                  | Update contest                      | Admin      | `contest.py`  |
| **DELETE**| `/contests/{contest_id}`                                  | Delete contest                      | Admin      | `contest.py`  |
| **POST** | `/contests/{contest_id}/submissions`                      | Submit entry to contest             | Optional   | `contest.py`  |
| **GET**  | `/contests/{contest_id}/submissions`                      | Get contest submissions             | Judge/Admin| `contest.py`  |
| **POST** | `/contests/{contest_id}/check-password`                   | Check password for private contest  | Public     | `contest.py`  |
| **DELETE**| `/contests/{contest_id}/ai-judges/{ai_judge_id}`          | Unassign AI judge (Admin?)          | Admin (?)  | `contest.py`  |
| **POST** | `/contests/{contest_id}/evaluate`                         | Submit judge evaluation             | Judge      | `contest.py`  |
| **POST** | `/ai/generate-text`                                       | Generate text via AI writer       | User (?)   | `ai_router.py`|
| **GET**  | `/admin/users/`                                           | List users (filterable)             | Admin      | `admin.py`    |
| **POST** | `/admin/users/`                                           | Create Human Judge user             | Admin      | `admin.py`    |
| **GET**  | `/admin/ai-writers`                                       | List AI Writers                     | Admin      | `admin.py`    |
| **POST** | `/admin/ai-writers`                                       | Create AI Writer                    | Admin      | `admin.py`    |
| **GET**  | `/admin/ai-writers/{writer_id}`                           | Get AI Writer details               | Admin      | `admin.py`    |
| **PUT**  | `/admin/ai-writers/{writer_id}`                           | Update AI Writer                    | Admin      | `admin.py`    |
| **DELETE**| `/admin/ai-writers/{writer_id}`                           | Delete AI Writer                    | Admin      | `admin.py`    |
| **PUT**  | `/admin/contests/{contest_id}/status`                     | Set contest status                  | Admin      | `admin.py`    |
| **PUT**  | `/admin/contests/{contest_id}/reset-password`             | Reset private contest password      | Admin      | `admin.py`    |
| **GET**  | `/admin/ai-judges`                                        | List AI Judges                      | Admin      | `admin.py`    |
| **POST** | `/admin/ai-judges`                                        | Create AI Judge                     | Admin      | `admin.py`    |
| **GET**  | `/admin/ai-judges/{ai_judge_id}`                          | Get AI Judge details                | Admin      | `admin.py`    |
| **PUT**  | `/admin/ai-judges/{ai_judge_id}`                          | Update AI Judge                     | Admin      | `admin.py`    |
| **DELETE**| `/admin/ai-judges/{ai_judge_id}`                          | Delete AI Judge                     | Admin      | `admin.py`    |
| **POST** | `/admin/contests/{contest_id}/human-judges/{user_id}`     | Assign Human Judge                  | Admin      | `admin.py`    |
| **DELETE**| `/admin/contests/{contest_id}/human-judges/{user_id}`     | Unassign Human Judge                | Admin      | `admin.py`    |
| **POST** | `/admin/contests/{contest_id}/ai-judges/{ai_judge_id}`    | Assign AI Judge                     | Admin      | `admin.py`    |
| **DELETE**| `/admin/contests/{contest_id}/ai-judges/{ai_judge_id}`    | Unassign AI Judge                   | Admin      | `admin.py`    |
| **GET**  | `/admin/ai-evaluations`                                   | List AI Evaluations                 | Admin      | `admin.py`    |
| **GET**  | `/admin/ai-evaluations/{evaluation_id}`                   | Get AI Evaluation Details           | Admin      | `admin.py`    |
| **GET**  | `/admin/ai-costs-summary`                                 | Get AI Costs Summary                | Admin      | `admin.py`    |
| **POST** | `/admin/contests/{contest_id}/ai-submission`            | Trigger AI Submission generation    | Admin      | `admin.py`    |
| **DELETE**| `/admin/submissions/{submission_id}`                      | Delete a submission                 | Admin      | `admin.py`    |
| **POST** | `/admin/contests/{contest_id}/ai-judges/{ai_judge_id}/evaluate` | Trigger AI Judge Evaluation | Admin      | `admin.py`    |

*Authentication Level Notes:*
*   *Public:* No login required.
*   *Optional:* Works with or without login; behavior might differ.
*   *User:* Requires any logged-in user.
*   *Judge:* Requires a logged-in user with the 'judge' role (and potentially assigned to the contest).
*   *Admin:* Requires a logged-in user with the 'admin' role.
*   *(?):* Auth level inferred or needs confirmation (e.g., missing explicit dependency).

## Status vs. `missing_endpoints.md`

*   **Implemented:**
    *   `#1 POST /contests/{contest_id}/submissions` (Backend DONE, needs frontend wiring)
    *   `#2 POST /contests/{contest_id}/evaluate` (Submit Judge Evaluation/Votes) (Backend DONE, needs frontend wiring)
    *   `#4 GET /admin/ai-costs-summary` (AI Cost Summary) (DONE, needs frontend wiring)
    *   `#5 POST /admin/contests/{contest_id}/ai-judges/{ai_judge_id}/evaluate` (Trigger AI Judge Evaluation) (DONE)
    *   `#6 POST /admin/users/` (Create Human Judge User) (DONE)
    *   `#7 GET /admin/ai-evaluations/{evaluation_id}` (Get AI Evaluation Details) (DONE)
    *   `#8 PUT /admin/contests/{contest_id}/reset-password` (Reset Contest Password) (DONE)
    *   `#9 GET /admin/users/` (List Human Judges) (DONE)
*   **Pending Refinement / Frontend Wiring:**
    *   `#3 Contest Password Check`: Endpoint `POST /contests/{contest_id}/check-password` exists and schema `ContestCheckPasswordRequest` is defined. Needs frontend wiring.

## Status vs. `flask_pages_inventory.md`

Many admin endpoints corresponding to Flask pages were found implemented in `admin.py` (CRUD for AI Writers, AI Judges, setting contest status, deleting submissions, assigning judges). Key points:

*   **Page #7 (Contest Detail):** Backend for submission exists, frontend needs wiring.
*   **Page #8/#9 (Private Contest Password):** Backend `POST /contests/{contest_id}/check-password` exists, schema defined, needs frontend wiring.
*   **Page #12 (Trigger AI Eval):** Covered by `POST /admin/contests/{contest_id}/ai-judges/{ai_judge_id}/evaluate`.
*   **Page #18 (Reset Contest Password):** Covered by `PUT /admin/contests/{contest_id}/reset-password`.
*   **Page #22 (Add Human Judge):** Covered by `POST /admin/users/` **[DONE]**.
*   **Page #27 (AI Costs):** Covered by `GET /admin/ai-costs-summary` (needs frontend wiring).
*   **Page #28 (View AI Eval):** Covered by `GET /admin/ai-evaluations/{evaluation_id}`.
*   **Page #33 (AI Submission):** Covered by `POST /admin/contests/{contest_id}/ai-submission`.

## Next Steps Recommended

1.  Review the endpoint table above for accuracy and potential cleanup (e.g., confirm inferred auth levels, check for unintended duplicates).
2.  Implement frontend wiring for required endpoints, starting with `#3 Contest Password Check`.

## Status vs. `missing_endpoints.md`

*   **Implemented:**
    *   `#1 POST /contests/{contest_id}/submissions` (Backend DONE, needs frontend wiring)
    *   `#2 POST /contests/{contest_id}/evaluate` (Submit Judge Evaluation/Votes) (Backend DONE, needs frontend wiring)
    *   `#4 GET /admin/ai-costs-summary` (AI Cost Summary) (DONE, needs frontend wiring)
    *   `#5 POST /admin/contests/{contest_id}/ai-judges/{ai_judge_id}/evaluate` (Trigger AI Judge Evaluation) (DONE)
    *   `#6 POST /admin/users/` (Create Human Judge User) (DONE)
    *   `#7 GET /admin/ai-evaluations/{evaluation_id}` (Get AI Evaluation Details) (DONE)
    *   `#8 PUT /admin/contests/{contest_id}/reset-password` (Reset Contest Password) (DONE)
    *   `#9 GET /admin/users/` (List Human Judges) (DONE)
*   **Pending Refinement / Frontend Wiring:**
    *   `#3 Contest Password Check`: Endpoint `POST /contests/{contest_id}/check-password` exists and schema `ContestCheckPasswordRequest` is defined. Needs frontend wiring.

## Status vs. `flask_pages_inventory.md`

Many admin endpoints corresponding to Flask pages were found implemented in `admin.py` (CRUD for AI Writers, AI Judges, setting contest status, deleting submissions, assigning judges). Key points:

*   **Page #7 (Contest Detail):** Backend for submission exists, frontend needs wiring.
*   **Page #8/#9 (Private Contest Password):** Backend `POST /contests/{contest_id}/check-password` exists, schema defined, needs frontend wiring.
*   **Page #12 (Trigger AI Eval):** Covered by `POST /admin/contests/{contest_id}/ai-judges/{ai_judge_id}/evaluate`.
*   **Page #18 (Reset Contest Password):** Covered by `PUT /admin/contests/{contest_id}/reset-password`.
*   **Page #22 (Add Human Judge):** Covered by `POST /admin/users/` **[DONE]**.
*   **Page #27 (AI Costs):** Covered by `GET /admin/ai-costs-summary` (needs frontend wiring).
*   **Page #28 (View AI Eval):** Covered by `GET /admin/ai-evaluations/{evaluation_id}`.
*   **Page #33 (AI Submission):** Covered by `POST /admin/contests/{contest_id}/ai-submission`.

## Next Steps Recommended

1.  Review the endpoint table above for accuracy and potential cleanup (e.g., confirm inferred auth levels, check for unintended duplicates).
2.  Implement frontend wiring for required endpoints, starting with `#3 Contest Password Check`.

## Next Steps Recommended

1.  Review the endpoint table above for accuracy and potential cleanup (e.g., confirm inferred auth levels, check for unintended duplicates).
2.  Implement frontend wiring for required endpoints, starting with `#3 Contest Password Check`. 