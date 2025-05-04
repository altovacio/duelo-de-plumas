# Endpoint Definition vs. Test Usage Report

| Method | Path                       | Defined In (Routers)                  | Tested In (Tests)                     |
|--------|----------------------------|---------------------------------------|---------------------------------------|
| GET    | `/`                        | backend/app/routers/ai_agents.py, backend/app/routers/main.py | *None*                                |
| POST   | `/`                        | backend/app/routers/ai_agents.py      | *None*                                |
| GET    | `/admin/ai-costs-summary`  | backend/app/routers/admin.py          | *None*                                |
| GET    | `/admin/ai-evaluations`    | backend/app/routers/admin.py          | *None*                                |
| GET    | `/admin/ai-evaluations/{var}` | backend/app/routers/admin.py          | *None*                                |
| GET    | `/admin/ai-judges`         | backend/app/routers/admin.py          | *None*                                |
| POST   | `/admin/ai-judges`         | backend/app/routers/admin.py          | *None*                                |
| DELETE | `/admin/ai-judges/{var}`   | backend/app/routers/admin.py          | *None*                                |
| GET    | `/admin/ai-judges/{var}`   | backend/app/routers/admin.py          | *None*                                |
| PUT    | `/admin/ai-judges/{var}`   | backend/app/routers/admin.py          | *None*                                |
| GET    | `/admin/ai-writers`        | backend/app/routers/admin.py          | *None*                                |
| POST   | `/admin/ai-writers`        | backend/app/routers/admin.py          | *None*                                |
| DELETE | `/admin/ai-writers/{var}`  | backend/app/routers/admin.py          | *None*                                |
| GET    | `/admin/ai-writers/{var}`  | backend/app/routers/admin.py          | *None*                                |
| PUT    | `/admin/ai-writers/{var}`  | backend/app/routers/admin.py          | *None*                                |
| DELETE | `/admin/contests/{var}/ai-judges/{var}` | backend/app/routers/admin.py          | *None*                                |
| POST   | `/admin/contests/{var}/ai-judges/{var}` | backend/app/routers/admin.py          | *None*                                |
| POST   | `/admin/contests/{var}/ai-judges/{var}/evaluate` | backend/app/routers/admin.py          | *None*                                |
| POST   | `/admin/contests/{var}/ai-submission` | backend/app/routers/admin.py          | *None*                                |
| DELETE | `/admin/contests/{var}/human-judges/{var}` | backend/app/routers/admin.py          | *None*                                |
| POST   | `/admin/contests/{var}/human-judges/{var}` | backend/app/routers/admin.py          | *None*                                |
| PUT    | `/admin/contests/{var}/reset-password` | backend/app/routers/admin.py          | *None*                                |
| PUT    | `/admin/contests/{var}/status` | backend/app/routers/admin.py          | *None*                                |
| DELETE | `/admin/submissions/{var}` | backend/app/routers/admin.py          | *None*                                |
| GET    | `/admin/users`             | backend/app/routers/admin.py          | *None*                                |
| POST   | `/admin/users`             | backend/app/routers/admin.py          | *None*                                |
| DELETE | `/admin/users/{var}`       | backend/app/routers/admin.py          | tests/test_ai_agents_e2e.py, tests/test_workflow_e2e.py |
| GET    | `/admin/users/{var}/credit-history` | backend/app/routers/admin.py          | *None*                                |
| PUT    | `/admin/users/{var}/credits` | backend/app/routers/admin.py          | *None*                                |
| GET    | `/ai-judges`               | *None*                                | tests/test_ai_agents_e2e.py           |
| POST   | `/ai-judges`               | *None*                                | tests/test_ai_agents_e2e.py, tests/test_ai_costs_e2e.py |
| DELETE | `/ai-judges/{var}`         | *None*                                | tests/test_ai_agents_e2e.py           |
| GET    | `/ai-judges/{var}`         | *None*                                | tests/test_ai_agents_e2e.py           |
| PUT    | `/ai-judges/{var}`         | *None*                                | tests/test_ai_agents_e2e.py           |
| GET    | `/ai-writers`              | *None*                                | tests/test_ai_agents_e2e.py           |
| POST   | `/ai-writers`              | *None*                                | tests/test_ai_agents_e2e.py, tests/test_ai_costs_e2e.py |
| DELETE | `/ai-writers/{var}`        | *None*                                | tests/test_ai_agents_e2e.py           |
| GET    | `/ai-writers/{var}`        | *None*                                | tests/test_ai_agents_e2e.py           |
| PUT    | `/ai-writers/{var}`        | *None*                                | tests/test_ai_agents_e2e.py           |
| POST   | `/auth/register`           | backend/app/routers/auth.py           | tests/test_ai_agents_e2e.py, tests/test_ai_costs_e2e.py, tests/test_workflow_e2e.py |
| POST   | `/auth/token`              | backend/app/routers/auth.py           | tests/test_ai_agents_e2e.py, tests/test_ai_costs_e2e.py, tests/test_workflow_e2e.py |
| GET    | `/auth/users/me`           | backend/app/routers/auth.py           | tests/test_ai_agents_e2e.py, tests/test_ai_costs_e2e.py, tests/test_workflow_e2e.py |
| GET    | `/contests`                | backend/app/routers/contest.py        | tests/test_workflow_e2e.py            |
| POST   | `/contests`                | backend/app/routers/contest.py        | tests/test_ai_costs_e2e.py, tests/test_workflow_e2e.py |
| DELETE | `/contests/{var}`          | backend/app/routers/contest.py        | tests/test_workflow_e2e.py            |
| GET    | `/contests/{var}`          | backend/app/routers/contest.py        | *None*                                |
| PUT    | `/contests/{var}`          | backend/app/routers/contest.py        | tests/test_workflow_e2e.py            |
| POST   | `/contests/{var}/check-password` | backend/app/routers/contest.py        | tests/test_workflow_e2e.py            |
| POST   | `/contests/{var}/evaluate` | backend/app/routers/contest.py        | *None*                                |
| POST   | `/contests/{var}/join`     | backend/app/routers/contest.py        | *None*                                |
| GET    | `/contests/{var}/submissions` | backend/app/routers/contest.py        | tests/test_workflow_e2e.py            |
| POST   | `/contests/{var}/submissions` | backend/app/routers/contest.py        | tests/test_workflow_e2e.py            |
| GET    | `/dashboard-data`          | backend/app/routers/main.py           | *None*                                |
| POST   | `/evaluate-contest/{var}`  | backend/app/routers/ai_router.py      | *None*                                |
| POST   | `/generate-text`           | backend/app/routers/ai_router.py      | *None*                                |
| POST   | `/roadmap/item`            | backend/app/routers/main.py           | *None*                                |
| DELETE | `/roadmap/item/{var}`      | backend/app/routers/main.py           | *None*                                |
| PUT    | `/roadmap/item/{var}/status` | backend/app/routers/main.py           | *None*                                |
| GET    | `/roadmap/items`           | backend/app/routers/main.py           | *None*                                |
| GET    | `/submissions`             | backend/app/routers/main.py           | *None*                                |
| DELETE | `/submissions/{var}`       | backend/app/routers/submission.py     | *None*                                |
| DELETE | `/{var}`                   | backend/app/routers/ai_agents.py      | *None*                                |
| GET    | `/{var}`                   | backend/app/routers/ai_agents.py      | *None*                                |
| PUT    | `/{var}`                   | backend/app/routers/ai_agents.py      | *None*                                |
| POST   | `/{var}/evaluate`          | backend/app/routers/ai_agents.py      | *None*                                |
| POST   | `/{var}/generate`          | backend/app/routers/ai_agents.py      | *None*                                |
