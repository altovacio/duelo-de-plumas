.
├── README.md
├── backend
│   ├── Dockerfile
│   ├── README.md
│   ├── alembic.ini
│   ├── app
│   │   ├── __init__.py
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   └── routes
│   │   │       ├── __init__.py
│   │   │       ├── admin.py
│   │   │       ├── agents.py
│   │   │       ├── auth.py
│   │   │       ├── contests.py
│   │   │       ├── dashboard.py
│   │   │       ├── debug_logs.py
│   │   │       ├── llm_models.py
│   │   │       ├── texts.py
│   │   │       ├── users.py
│   │   │       └── votes.py
│   │   ├── core
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   └── security.py
│   │   ├── db
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agent.py
│   │   │   │   ├── agent_execution.py
│   │   │   │   ├── ai_debug_log.py
│   │   │   │   ├── contest.py
│   │   │   │   ├── contest_judge.py
│   │   │   │   ├── contest_text.py
│   │   │   │   ├── credit_transaction.py
│   │   │   │   ├── text.py
│   │   │   │   ├── user.py
│   │   │   │   └── vote.py
│   │   │   └── repositories
│   │   │       ├── __init__.py
│   │   │       ├── agent_repository.py
│   │   │       ├── contest_repository.py
│   │   │       ├── credit_repository.py
│   │   │       ├── text_repository.py
│   │   │       ├── user_repository.py
│   │   │       └── vote_repository.py
│   │   ├── main.py
│   │   ├── schemas
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── contest.py
│   │   │   ├── credit.py
│   │   │   ├── text.py
│   │   │   ├── user.py
│   │   │   └── vote.py
│   │   ├── services
│   │   │   ├── __init__.py
│   │   │   ├── agent_service.py
│   │   │   ├── ai_provider_service.py
│   │   │   ├── ai_service.py
│   │   │   ├── ai_strategies
│   │   │   │   ├── base_strategy.py
│   │   │   │   ├── judge_prompts.py
│   │   │   │   ├── judge_strategies.py
│   │   │   │   ├── writer_prompts.py
│   │   │   │   └── writer_strategies.py
│   │   │   ├── auth_service.py
│   │   │   ├── contest_service.py
│   │   │   ├── credit_service.py
│   │   │   ├── judge_service.py
│   │   │   ├── text_service.py
│   │   │   ├── user_service.py
│   │   │   └── vote_service.py
│   │   └── utils
│   │       ├── __init__.py
│   │       ├── ai_model_costs.json
│   │       ├── ai_models.py
│   │       ├── debug_logger.py
│   │       ├── markdown_utils.py
│   │       ├── text_parsing.py
│   │       └── validation_utils.py
│   ├── docs
│   │   └── ai_logging_and_parsing_review.md
│   ├── generate_api_docs.py
│   ├── init-test-db.sh
│   ├── migrations
│   │   ├── README
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions
│   │       ├── 558cd0c633c1_initial_migration_with_clean_models.py
│   │       └── add_ai_debug_logs_table.py
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── scripts
│   │   ├── __init__.py
│   │   ├── create_admin.py
│   │   └── debug_init_script.py
│   ├── tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── debug_tests
│   │   ├── e2e_sec_01_setup_user_registration.py
│   │   ├── e2e_sec_02_ai_agent_creation.py
│   │   ├── e2e_sec_03_contest_creation_management.py
│   │   ├── e2e_sec_04_text_creation.py
│   │   ├── e2e_sec_05_text_submission.py
│   │   ├── e2e_sec_06_evaluation_phase.py
│   │   ├── e2e_sec_07_contest_closure_results.py
│   │   ├── e2e_sec_08_cost_usage_monitoring_pre_cleanup.py
│   │   ├── e2e_sec_09_cleanup_routine.py
│   │   ├── e2e_sec_10_final_state_verification_post_cleanup.py
│   │   ├── e2e_test_plan_config.py
│   │   ├── fix_remaining_variables.py
│   │   ├── fix_syntax_errors.py
│   │   ├── fix_user_endpoints.py
│   │   ├── outputs
│   │   │   └── ai_costs_summary_post_cleanup.json
│   │   └── shared_test_state.py
│   └── wait-for-it.sh
├── docker-compose.prod.yml
├── docker-compose.yml
├── docs
│   ├── DEBUGGING.md
│   ├── ai_logging_proposal.md
│   ├── api_endpoints_programmatically.md
│   ├── front_implementation_plan.md
│   ├── project_description.md
│   ├── technical_debt.md
│   └── tree.md
├── examples
│   ├── AsnosEstupidos.txt
│   ├── CierraLaUltimaPuerta.txt
│   ├── ElReinoDeLosColores.txt
│   └── LeccionDeCocina.txt
├── fix-ts-errors.sh
├── frontend
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── README.md
│   ├── dist
│   │   ├── assets
│   │   │   ├── index-BEJyc3C7.css
│   │   │   ├── index-BTAPwlsy.js
│   │   │   └── index-BTAPwlsy.js.map
│   │   └── index.html
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── public
│   ├── src
│   │   ├── App.tsx
│   │   ├── components
│   │   │   ├── Agent
│   │   │   │   └── AgentFormModal.tsx
│   │   │   ├── Common
│   │   │   │   └── FullTextModal.tsx
│   │   │   ├── Contest
│   │   │   │   ├── AIJudgeConfirmationModal.tsx
│   │   │   │   ├── AIJudgeExecutionForm.tsx
│   │   │   │   ├── AIWriterExecutionForm.tsx
│   │   │   │   ├── ContestCard.tsx
│   │   │   │   ├── ContestEditModal.tsx
│   │   │   │   ├── ContestFormModal.tsx
│   │   │   │   ├── ContestResults.tsx
│   │   │   │   ├── HumanJudgingForm.tsx
│   │   │   │   ├── JudgeManagementModal.tsx
│   │   │   │   └── TextSubmissionForm.tsx
│   │   │   ├── Dashboard
│   │   │   ├── Layout
│   │   │   │   └── MainLayout.tsx
│   │   │   ├── TextEditor
│   │   │   │   └── TextFormModal.tsx
│   │   │   ├── auth
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   ├── examples
│   │   │   └── ui
│   │   │       └── BackButton.tsx
│   │   ├── hooks
│   │   │   └── useAuth.ts
│   │   ├── index.css
│   │   ├── main.tsx
│   │   ├── pages
│   │   │   ├── Admin
│   │   │   │   ├── AdminAIDebugLogsPage.tsx
│   │   │   │   ├── AdminAgentsPage.tsx
│   │   │   │   ├── AdminContestsPage.tsx
│   │   │   │   ├── AdminDashboardPage.tsx
│   │   │   │   ├── AdminMonitoringPage.tsx
│   │   │   │   └── AdminUsersPage.tsx
│   │   │   ├── Auth
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   └── RegisterPage.tsx
│   │   │   ├── ContestDetail
│   │   │   │   └── ContestDetailPage.tsx
│   │   │   ├── ContestList
│   │   │   │   └── ContestListPage.tsx
│   │   │   ├── Dashboard
│   │   │   │   ├── AIWriterPage.tsx
│   │   │   │   ├── DashboardPage.tsx
│   │   │   │   └── MarkdownEditorPage.tsx
│   │   │   └── Home
│   │   │       └── HomePage.tsx
│   │   ├── services
│   │   │   ├── agentService.ts
│   │   │   ├── authService.ts
│   │   │   ├── contestService.ts
│   │   │   ├── creditService.ts
│   │   │   ├── dashboardService.ts
│   │   │   ├── modelService.ts
│   │   │   ├── textService.ts
│   │   │   ├── userService.ts
│   │   │   └── voteService.ts
│   │   ├── store
│   │   │   └── authStore.ts
│   │   ├── types
│   │   │   └── auth.ts
│   │   ├── types.d.ts
│   │   ├── utils
│   │   │   ├── apiClient.ts
│   │   │   ├── apiConfig.ts
│   │   │   └── tokenUtils.ts
│   │   └── vite-env.d.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── nginx.conf
│   └── default.conf
└── scripts
    ├── dev.sh
    ├── prod.sh
    ├── test-all-routes.sh
    └── test-routing.sh

51 directories, 188 files
