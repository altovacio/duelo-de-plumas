# Duelo de Plumas - FastAPI Development Plan

## 1. Project Setup  
- Use FastAPI as the web framework and uvicorn as the ASGI server  
- Employ Pydantic to define request/response schemas  
- Use an ORM (e.g., SQLAlchemy) for managing the database  
- Implement JWT (or OAuth2) for token-based authentication  
- Configure middleware for error handling, logging, CORS, etc.

## 2. Endpoints Organization  

The RESTful endpoints will be grouped by resources. Each group will enforce proper role validations and business rules described in the project documentation.

### 2.1. Authentication (/auth)  
- POST `/auth/signup`  
  - Registers a new user (providing username, email, password, etc.)  
  - Available to guests  
- POST `/auth/login`  
  - Authenticates a user and returns a JWT token  
- POST `/auth/logout` (optional)  
  - Handles token invalidation

### 2.2. User Management (/users)  
- GET `/users/{user_id}`  
  - Returns user details (a user can view their own details; administrators can view all)  
- PUT `/users/{user_id}`  
  - Updates user profile information  
- DELETE `/users/{user_id}`  
  - Deletes a user (only administrators are allowed to perform deletions)  
  - Note: Upon deletion, all contests, texts, and agents created by the user are removed—but historical credit/cost records are preserved  
- GET `/users` (Admin only)  
  - Lists all users for management purposes

### 2.3. Text Management (/texts)  
- GET `/texts`  
  - Lists texts; includes optional query parameters to filter by owner or contest  
  - For texts associated with contests, enforce anonymity rules (if contest is open or under evaluation, hide author/owner details for non-admins)  
- POST `/texts`  
  - Creates a new text  
  - Input includes title, content (markdown)
- GET `/texts/{text_id}`  
  - Retrieves text details  
- PUT `/texts/{text_id}`  
  - Updates a text (only permitted for the owner)  
- DELETE `/texts/{text_id}`  
  - Deletes a text  
  - Allowed by the text's owner or an administrator

### 2.4. Contest Management (/contests)  
- GET `/contests`  
  - Lists all contests  
  - Supports query parameters for filtering by type (public or private) and state (open, under evaluation, closed)  
  - For private contests, ensure that access control (via password verification) is applied  
- POST `/contests`  
  - Creates a new contest (authenticated users only)  
  - Input: title, description (in Markdown), optional parameters (minimum votes, assigned judges, password if private, etc.)  
- GET `/contests/{contest_id}`  
  - Retrieves full contest details  
  - Adjusts payload based on contest state:  
    - In open contests, only the contest creator or administrator can view the full list of submissions  
    - In contests under evaluation or closed, submissions and their details (e.g., author names) become visible  
- PUT `/contests/{contest_id}`  
  - Updates contest details  
  - Only the contest creator or administrator can update  
- DELETE `/contests/{contest_id}`  
  - Deletes a contest  
  - Business rule: When a contest is deleted, associated votes are removed but texts are preserved  
- GET `/contests/{contest_id}/ranking`  
  - Retrieves the final ranking of texts (for contests in evaluation or closed states)  
  - Should include vote tallies and judges' comments

### 2.5. Contest Participation and Judge Management 
- POST `/contests/{contest_id}/submissions`  
  - Submits a text entry to a contest  
  - Input: text_id to be submitted
  - Validates that the contest is open, text belongs to the user, and checks contest restrictions (e.g., if authors can submit multiple texts)
- GET `/contests/{contest_id}/submissions`  
  - Lists all text submissions for a contest
  - Visibility rules: if the contest is open, only the creator/administrator sees full details; others view anonymized information

- POST `/contests/{contest_id}/judges`
  - Assigns a user as judge to a contest
  - Input: user_id to be assigned as judge
  - Only the contest creator or administrator can assign judges
  - Validates judge restrictions if configured (e.g., judges cannot be participants)
- GET `/contests/{contest_id}/judges`
  - Lists all judges assigned to a contest
  - Only visible to the contest creator, administrators, and assigned judges
- DELETE `/contests/{contest_id}/judges/{user_id}`
  - Removes a judge from a contest
  - Only the contest creator or administrator can remove judges
  - Not allowed if the judge has already submitted votes

### 2.6. Voting (/contests/{contest_id}/votes)  
- POST `/contests/{contest_id}/votes`  
  - Allows a judge (human or AI) to cast a vote on a text within the contest  
  - Request body: text_id, vote value (3, 2, 1 points), justification/comment  
  - Enforce: Only assigned judges (or a user acting as judge) can vote  
  - Business rules:
    - A judge must vote for exactly three different texts (first, second, and third place)
    - Validates that the contest is in the "evaluation" state
- GET `/contests/{contest_id}/votes`  
  - Retrieves all votes for a contest  
  - Access constrained to contest administrators, judges, or the contest creator
- GET `/contests/{contest_id}/votes/{judge_id}`
  - Retrieves votes from a specific judge in a contest
  - Access limited to the judge themselves, contest creator, or administrators

### 2.7. Agents for AI (Judges and Writers) (/agents)  
For managing AI agents (both Judges and Writers), endpoints:  
- GET `/agents` – List available AI agents with optional type filter
  - Query parameters: `type` (judge or writer), `public` (boolean)
- POST `/agents` – Create a new AI agent (input includes name, description, prompt, type, etc.)
- PUT `/agents/{agent_id}` – Update AI agent details
- DELETE `/agents/{agent_id}` – Delete an AI agent  
- GET `/agents/{agent_id}` - Get detailed information about a specific agent
- POST `/agents/{agent_id}/execute` - Execute an agent with appropriate parameters
  - For judge agents: Provide contest_id to evaluate
    - The agent will evaluate all texts in a contest and submit votes
  - For writer agents: Provide optional title and description
    - The agent will generate a text based on its personality
  - Validates sufficient credits for the operation
  - Returns the operation result directly (votes or text)
  - Business rules:
    - Users must have sufficient credits for the operation
    - Credits are deducted based on execution
    - The result (text or votes) is associated with the agent owner

### 2.8. Dashboard Endpoint (/dashboard)  
- GET `/dashboard`  
  - Returns an aggregated summary for the current user  
  - Includes:  
    - Contests where the user participates as an author  
    - Contests where the user votes as a judge  
    - Text submissions
    - Credit balance and basic transaction history
- GET `/dashboard/credits/transactions`
  - Returns detailed credit transaction history for the current user
  - Supports filtering by date range, transaction type, and AI model

### 2.9. Administration Endpoints (/admin)  
- GET `/admin/users`  
  - Lists all user accounts with detail, for administrative oversight  
- PATCH `/admin/users/{user_id}/credits`  
  - Modifies a user's credit balance (only administrators can assign or adjust credits)  
- GET `/admin/agents`  
  - Lists all global AI agents  
- GET `/admin/metrics`  
  - Provides basic statistics such as number of users, contests, and texts
- GET `/admin/credits/usage`
  - Detailed monitoring of credit usage across the platform
  - Breaks down usage by AI model, user, time period, and transaction type
  - Provides aggregated statistics on token consumption and associated costs

## 3. Security, Middleware, and Business Logic  
- Secure API endpoints by implementing role-based access control via FastAPI dependencies  
- Use custom exception handlers to return appropriate HTTP status codes  
- Enforce business rules (e.g., contest state changes, anonymity for open contests, and text deletion nuances) within endpoint logic or dedicated service layers  
- Schedule background tasks (if needed) for monitoring contest deadlines and automatically transitioning contest states once vote criteria are met
- Implement state transition logic for contests:
  - "open" → "evaluation" (when end_date is reached or manually triggered)
  - "evaluation" → "closed" (when all required votes are collected)

## 4. Testing and Documentation  
- Write unit tests for each endpoint, covering both success and failure cases as per business logic  
- Generate automatic API docs using FastAPI's Swagger/OpenAPI support  
- Ensure endpoints are self-documented with descriptions and proper Pydantic models 