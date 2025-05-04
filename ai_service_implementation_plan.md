# AI Service Implementation Plan (FastAPI)

This document outlines the proposed plan for implementing the AI writer generation and AI judge evaluation logic within the FastAPI backend (`backend/`), drawing lessons from the previous Flask implementation (`app/`).

## 1. Goal

To create a robust, testable, and maintainable service layer for handling interactions with external Large Language Models (LLMs) for text generation and evaluation, integrating seamlessly with the new credit system and CostLedger.

## 2. Proposed Structure

### 2.1. Service Module

*   Create a dedicated service module: `backend/app/services/ai_service.py`.
    *   This module will contain the core logic for prompt construction, LLM API interaction, response parsing, and cost/token calculations, separate from the HTTP request/response handling in routers.

### 2.2. Configuration & Clients

*   **Configuration:**
    *   Migrate AI model details (provider, API name, features) and pricing information (e.g., cost per token/dollar) from the old `app/config/ai_judge_params.py` into the FastAPI settings management (e.g., `backend/config.py` using Pydantic `BaseSettings`).
    *   Define settings for the credit cost model (e.g., `CREDITS_PER_DOLLAR`, `CREDITS_PER_1K_TOKENS`, `MINIMUM_CREDIT_COST`).
*   **API Clients:**
    *   Utilize FastAPI's dependency injection for providing initialized AI clients (e.g., `openai.AsyncOpenAI`, `anthropic.AsyncAnthropic`) to service functions. Use the existing dependency providers in `backend/app/dependencies.py`. Clients should **not** be initialized globally within the service module itself.

### 2.3. Core Service Functions (`ai_service.py`)

These functions will handle specific, reusable tasks:

*   `get_model_info(model_id: str) -> dict`: Retrieves model configuration (provider, API name, etc.) from settings based on the provided `model_id`.
*   `count_tokens(text: str, model_id: str) -> int`: Calculates token count using `tiktoken` with appropriate fallbacks.
*   `calculate_monetary_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]`: Calculates the estimated monetary cost (e.g., in USD) based on token counts and pricing information from settings. Returns `None` if cost cannot be determined.
*   `calculate_credit_cost(monetary_cost: Optional[float], prompt_tokens: int, completion_tokens: int) -> int`: **New Function.** Translates monetary cost and/or token counts into the integer credit cost based on the configured credit cost model settings. Handles potential `None` for `monetary_cost` and ensures a minimum credit cost is applied.
*   `call_llm_api(prompt: str, model_id: str, client: Union[openai.AsyncOpenAI, anthropic.AsyncAnthropic], ...) -> dict`: Refactored function to call the appropriate LLM API (using the injected `client`). Returns a dictionary containing `{'success': bool, 'response_text': str, 'prompt_tokens': int, 'completion_tokens': int, 'monetary_cost': Optional[float], 'error': Optional[str]}`.
*   `construct_writer_prompt(writer: models.UserAIWriter, ...) -> str`: Builds the full prompt for the AI writer based on base instructions, personality, and context.
*   `construct_judge_prompt(judge: models.UserAIJudge, contest: models.Contest, submissions: List[models.Submission], ...) -> str`: Builds the full prompt for the AI judge.
*   `parse_judge_response(response_text: str, submissions: List[models.Submission]) -> List[dict]`: Adapts the regex logic from the Flask app to parse rankings and comments from the judge's response text. Returns structured data (e.g., list of dicts with `submission_id`, `place`, `comment`).

### 2.4. Main Service Functions (`ai_service.py`)

These functions orchestrate the core AI tasks but **do not** handle credit deduction or CostLedger logging directly:

*   `perform_ai_generation(writer: models.UserAIWriter, model_id: str, db: AsyncSession, ai_client, ...) -> dict`:
    *   Accepts writer object, model ID, DB session, injected AI client.
    *   Calls `construct_writer_prompt`.
    *   Calls `call_llm_api`.
    *   Returns a dictionary including `success`, `generated_text`, `prompt_tokens`, `completion_tokens`, `monetary_cost`, `error`.
*   `perform_ai_evaluation(judge: models.UserAIJudge, contest_id: int, model_id: str, db: AsyncSession, ai_client, ...) -> dict`:
    *   Accepts judge object, contest ID, model ID, DB session, injected AI client.
    *   Fetches Contest and relevant Submissions from the database.
    *   Calls `construct_judge_prompt`, `call_llm_api`, `parse_judge_response`.
    *   Creates necessary `Vote` records **associated with the session but does not commit**.
    *   Returns a dictionary including `success`, `status_message`, `prompt_tokens`, `completion_tokens`, `monetary_cost`, `error`, and potentially information about the created `Vote` objects needed for the final commit step in the router.

### 2.5. Endpoint Logic (`backend/app/routers/ai_agents.py`)

The existing placeholder functions (`generate_text`, `evaluate_submissions`) will be updated to orchestrate the full process:

1.  Verify ownership of the AI agent.
2.  Start a database transaction (`try...except...finally` block with `await session.rollback()` in except/finally).
3.  Lock the user row using `select(...).with_for_update()`.
4.  Get the user's `current_balance`.
5.  **(Optional) Pre-check:** Perform a rough cost estimation using service helpers (`calculate_monetary_cost`, `calculate_credit_cost`) and check if `current_balance` is sufficient. Raise `402 Payment Required` if obviously insufficient based on estimate.
6.  Call the appropriate main service function (`perform_ai_generation` or `perform_ai_evaluation`), passing the DB session and injected AI clients.
7.  Receive the result dictionary from the service function.
8.  **If AI call successful:**
    *   Calculate the `actual_credit_cost` using `calculate_credit_cost()` with the actual `monetary_cost` and `token_counts` from the service result.
    *   Perform the **final credit check**: `if current_balance < actual_credit_cost: raise HTTPException(402)`.
    *   Deduct credits: `user.credits -= actual_credit_cost`. Add the updated user to the session.
    *   Create the `models.CostLedger` entry with all relevant details (`user_id`, `action_type`, `credits_change=-actual_credit_cost`, `real_cost=monetary_cost`, `resulting_balance`, `related_entity_*`, description). Add the ledger entry to the session.
    *   If performing evaluation, ensure any `Vote` objects created by the service are associated with the session (the service function should ideally have added them already).
    *   Commit the transaction: `await session.commit()`.
    *   Refresh objects if needed (`user`, `ledger_entry`).
    *   Return the appropriate success response schema (`AIWriterGenerateResponse` or `AIJudgeEvaluateResponse`).
9.  **If AI call failed:**
    *   Rollback the transaction: `await session.rollback()`.
    *   Return an appropriate HTTP error response based on the error from the service.
10. **Handle any other exceptions:** Ensure rollback on unexpected errors and return a 500 error.

## 3. Benefits

*   **Separation of Concerns:** Routers handle HTTP and transactions; Services handle AI logic.
*   **Testability:** Service functions can be unit-tested more easily.
*   **Reusability:** Core functions (token counting, cost calculation, API calls) are reusable.
*   **Configuration:** Centralized AI and credit cost model configuration.
*   **Maintainability:** Clearer structure makes future updates easier.

## 4. Next Steps

1.  Create `backend/app/services/ai_service.py`.
2.  Define/migrate AI model and pricing configuration into FastAPI settings.
3.  Implement the `calculate_credit_cost` function with the chosen credit model.
4.  Implement the core and main service functions outlined above.
5.  Refactor the placeholder endpoints in `backend/app/routers/ai_agents.py` to use the new service functions and implement the orchestration logic (transaction, credit check, ledger logging, commit/rollback).
6.  Add necessary dependencies (e.g., AI clients) to the endpoint functions.
7.  Thoroughly test the endpoints and service functions. 