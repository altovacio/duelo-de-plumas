# Duelo de Plumas API

API for literary contests with AI assistance

**Version:** 3.0.0

## Table of Contents

- [Other](#other)
- [admin](#admin)
- [agents](#agents)
- [authentication](#authentication)
- [contests](#contests)
- [dashboard](#dashboard)
- [llm_models](#llm_models)
- [texts](#texts)
- [users](#users)
- [votes](#votes)

## Other

### GET /

**Summary:** Root

### GET /health

**Summary:** Health Check


## admin

### GET /admin/users

**Summary:** Get All Users

Get all users (admin only).

### PATCH /admin/users/{user_id}/credits

**Summary:** Update User Credits

Update a user's credit balance (admin only).

### GET /admin/credits/transactions

**Summary:** Get Credit Transactions

Get filtered credit transactions (admin only).

### GET /admin/credits/usage

**Summary:** Get Credit Usage Summary

Get a summary of credit usage across the system (admin only).


## agents

### POST /agents

**Summary:** Create Agent

Create a new AI agent.
Only admins can create public agents.

### GET /agents

**Summary:** Get Agents

Get a list of AI agents.
- If public=True, returns only public agents.
- If public=False, returns only private agents owned by the user (or all private for admin).
- If public is not provided (None), returns public agents AND private agents owned by the user (or all agents for admin).

### POST /agents/execute/judge

**Summary:** Execute Judge Agent

Execute a judge agent on a contest.
- The agent must be a judge agent
- The contest must be in evaluation state
- User must have sufficient credits

### POST /agents/execute/writer

**Summary:** Execute Writer Agent

Execute a writer agent to generate a text.
- The agent must be a writer agent
- User must have sufficient credits

### GET /agents/executions

**Summary:** Get Agent Executions

Get a list of agent executions performed by the current user.

### GET /agents/{agent_id}

**Summary:** Get Agent

Get details of a specific AI agent.
User must be the owner of the agent or the agent must be public, or user is admin.

### PUT /agents/{agent_id}

**Summary:** Update Agent

Update an AI agent.
User must be the owner of the agent or admin to update it.
Only admins can make agents public.

### DELETE /agents/{agent_id}

**Summary:** Delete Agent

Delete an AI agent.
User must be the owner of the agent or admin to delete it.

### POST /agents/{agent_id}/clone

**Summary:** Clone Agent

Clone a public agent to the user's account.
The agent must be public to be cloned.


## authentication

### POST /auth/signup

**Summary:** Signup

Register a new user.

### POST /auth/signup

**Summary:** Signup

Register a new user.

### POST /auth/login

**Summary:** Login

Authenticate and login a user.

### POST /auth/login

**Summary:** Login

Authenticate and login a user.

### POST /auth/login/json

**Summary:** Login Json

Authenticate and login a user using JSON payload.

### POST /auth/login/json

**Summary:** Login Json

Authenticate and login a user using JSON payload.


## contests

### POST /contests/

**Summary:** Create Contest

Create a new contest

### POST /contests/

**Summary:** Create Contest

Create a new contest

### GET /contests/

**Summary:** Get Contests

Get list of contests with optional filtering.
If 'creator=me' is passed, only contests created by the current user are returned.
Otherwise, all users (authenticated or visitor) see all contests listed (unless other filters apply).
Access to details of private contests is handled by the GET /{contest_id} endpoint.

### GET /contests/

**Summary:** Get Contests

Get list of contests with optional filtering.
If 'creator=me' is passed, only contests created by the current user are returned.
Otherwise, all users (authenticated or visitor) see all contests listed (unless other filters apply).
Access to details of private contests is handled by the GET /{contest_id} endpoint.

### GET /contests/my-submissions/

**Summary:** Get All My Submissions

Get all text submissions made by the current authenticated user across all contests.
This endpoint provides a complete view of all the user's contest participation.

### GET /contests/my-submissions/

**Summary:** Get All My Submissions

Get all text submissions made by the current authenticated user across all contests.
This endpoint provides a complete view of all the user's contest participation.

### GET /contests/{contest_id}

**Summary:** Get Contest

Get contest details including participant and text counts

For private contests, provide the password unless you're the creator or admin

### GET /contests/{contest_id}

**Summary:** Get Contest

Get contest details including participant and text counts

For private contests, provide the password unless you're the creator or admin

### PUT /contests/{contest_id}

**Summary:** Update Contest

Update contest details

Only the contest creator or admin can update a contest

### PUT /contests/{contest_id}

**Summary:** Update Contest

Update contest details

Only the contest creator or admin can update a contest

### DELETE /contests/{contest_id}

**Summary:** Delete Contest

Delete a contest

Only the contest creator or admin can delete a contest
When a contest is deleted, associated votes are removed but texts are preserved

### DELETE /contests/{contest_id}

**Summary:** Delete Contest

Delete a contest

Only the contest creator or admin can delete a contest
When a contest is deleted, associated votes are removed but texts are preserved

### POST /contests/{contest_id}/submissions/

**Summary:** Submit Text To Contest

Submit a text to a contest

For private contests, provide the password unless you're the creator or admin

### POST /contests/{contest_id}/submissions/

**Summary:** Submit Text To Contest

Submit a text to a contest

For private contests, provide the password unless you're the creator or admin

### GET /contests/{contest_id}/submissions/

**Summary:** Get Contest Submissions

Get all text submissions for a contest

For private contests, provide the password unless you're the creator or admin
For open contests, only the creator and admins can see submissions
For evaluation/closed contests, anyone with access can see submissions with full details

### GET /contests/{contest_id}/submissions/

**Summary:** Get Contest Submissions

Get all text submissions for a contest

For private contests, provide the password unless you're the creator or admin
For open contests, only the creator and admins can see submissions
For evaluation/closed contests, anyone with access can see submissions with full details

### GET /contests/{contest_id}/my-submissions/

**Summary:** Get My Contest Submissions

Get all text submissions made by the current authenticated user for a specific contest.
This allows users to see their own submissions even in open contests where general
submission visibility is restricted to creators/admins.

### GET /contests/{contest_id}/my-submissions/

**Summary:** Get My Contest Submissions

Get all text submissions made by the current authenticated user for a specific contest.
This allows users to see their own submissions even in open contests where general
submission visibility is restricted to creators/admins.

### DELETE /contests/{contest_id}/submissions/{submission_id}

**Summary:** Remove Submission From Contest

Remove a text submission from a contest using the submission ID.

Can be done by:
- The text owner (owner of the text submitted)
- The contest creator
- An admin

### DELETE /contests/{contest_id}/submissions/{submission_id}

**Summary:** Remove Submission From Contest

Remove a text submission from a contest using the submission ID.

Can be done by:
- The text owner (owner of the text submitted)
- The contest creator
- An admin

### POST /contests/{contest_id}/judges

**Summary:** Assign Judge To Contest

Assign a judge (user or AI agent) to a contest.

Only the contest creator or admin can assign judges.

### POST /contests/{contest_id}/judges

**Summary:** Assign Judge To Contest

Assign a judge (user or AI agent) to a contest.

Only the contest creator or admin can assign judges.

### GET /contests/{contest_id}/judges

**Summary:** Get Contest Judges

Get all judges assigned to a contest

Accessible to:
- The contest creator
- Assigned judges
- Admins

### GET /contests/{contest_id}/judges

**Summary:** Get Contest Judges

Get all judges assigned to a contest

Accessible to:
- The contest creator
- Assigned judges
- Admins

### DELETE /contests/{contest_id}/judges/{judge_id}

**Summary:** Remove Judge From Contest

Remove a judge from a contest

Only the contest creator or admin can remove judges
Cannot remove a judge who has already voted (unless you're an admin)

### DELETE /contests/{contest_id}/judges/{judge_id}

**Summary:** Remove Judge From Contest

Remove a judge from a contest

Only the contest creator or admin can remove judges
Cannot remove a judge who has already voted (unless you're an admin)


## dashboard

### GET /dashboard

**Summary:** Get User Dashboard

Get the current user's dashboard data.

### GET /dashboard/credits/transactions

**Summary:** Get User Credit Transactions

Get the current user's credit transaction history.


## llm_models

### GET /models

**Summary:** Get Available Llm Models

Get all available LLM models.
Returns models that are currently enabled in the system with their pricing information.

### GET /models/{model_id}

**Summary:** Get Llm Model Details

Get technical details and pricing information about a specific LLM model.
Returns id, name, provider, context window size, and pricing information.


## texts

### POST /texts/

**Summary:** Create Text

Create a new text with the current user as owner.

### POST /texts/

**Summary:** Create Text

Create a new text with the current user as owner.

### GET /texts/

**Summary:** Get Texts

Get all texts, with optional filtering by owner.

### GET /texts/

**Summary:** Get Texts

Get all texts, with optional filtering by owner.

### GET /texts/my

**Summary:** Get My Texts

Get texts belonging to the current user.

### GET /texts/my

**Summary:** Get My Texts

Get texts belonging to the current user.

### GET /texts/{text_id}

**Summary:** Get Text

Get a specific text by ID.
During evaluation or closed phase, anyone can view the text content.

### GET /texts/{text_id}

**Summary:** Get Text

Get a specific text by ID.
During evaluation or closed phase, anyone can view the text content.

### PUT /texts/{text_id}

**Summary:** Update Text

Update a text. Only the owner or an admin can update a text.

### PUT /texts/{text_id}

**Summary:** Update Text

Update a text. Only the owner or an admin can update a text.

### DELETE /texts/{text_id}

**Summary:** Delete Text

Delete a text. Only the owner or an admin can delete a text.

### DELETE /texts/{text_id}

**Summary:** Delete Text

Delete a text. Only the owner or an admin can delete a text.


## users

### GET /users/me

**Summary:** Read Users Me

Get current user details.

### GET /users/me

**Summary:** Read Users Me

Get current user details.

### GET /users

**Summary:** Get Users

Get all users. Only administrators can access this endpoint.

### GET /users

**Summary:** Get Users

Get all users. Only administrators can access this endpoint.

### GET /users/{user_id}/public

**Summary:** Get User Public

Get public user information (username only). 
This endpoint is public and doesn't require authentication.

### GET /users/{user_id}/public

**Summary:** Get User Public

Get public user information (username only). 
This endpoint is public and doesn't require authentication.

### GET /users/{user_id}

**Summary:** Get User

Get a specific user. Users can view their own details, administrators can view all.

### GET /users/{user_id}

**Summary:** Get User

Get a specific user. Users can view their own details, administrators can view all.

### PUT /users/{user_id}

**Summary:** Update User

Update a user. Users can only update their own details, administrators can update all.

### PUT /users/{user_id}

**Summary:** Update User

Update a user. Users can only update their own details, administrators can update all.

### DELETE /users/{user_id}

**Summary:** Delete User

Delete a user. Only administrators can delete users.

### DELETE /users/{user_id}

**Summary:** Delete User

Delete a user. Only administrators can delete users.

### PATCH /users/{user_id}/credits

**Summary:** Update User Credits

Update a user's credits. Only administrators can update user credits.

### PATCH /users/{user_id}/credits

**Summary:** Update User Credits

Update a user's credits. Only administrators can update user credits.

### GET /users/judge-contests

**Summary:** Get User Judge Contests

Get all contests where the current user is a judge.

### GET /users/judge-contests

**Summary:** Get User Judge Contests

Get all contests where the current user is a judge.


## votes

### POST /contests/{contest_id}/votes

**Summary:** Create a vote in a contest

Create a new vote in a contest.

- The contest must be in the evaluation state
- The user must be a judge for the contest
- The text must be part of the contest

**Voting System:**
- Judges assign places (1st, 2nd, 3rd) to texts and provide commentary for each
- Judges can also provide commentary for texts that didn't make the podium (no place assigned)

**Human Votes:**
- A judge must assign places to at least min(3, total_texts) different texts
- A judge can comment on any number of texts that didn't make the podium
- When a judge votes for the same place again, the previous vote for that place is replaced

**AI Votes:**
- Users can submit multiple votes using different AI judges (agents)
- When voting with an AI model that was previously used, all previous votes with that model are deleted first
- The same restrictions apply to each AI model
- The same user can have multiple sets of votes in a contest: one as a human judge and multiple as AI judges

**Small Contests:**
- For contests with fewer than 3 texts, judges only need to assign all possible places
- For example, in a contest with 2 texts, only 1st and 2nd places are required

### POST /contests/{contest_id}/votes

**Summary:** Create a vote in a contest

Create a new vote in a contest.

- The contest must be in the evaluation state
- The user must be a judge for the contest
- The text must be part of the contest

**Voting System:**
- Judges assign places (1st, 2nd, 3rd) to texts and provide commentary for each
- Judges can also provide commentary for texts that didn't make the podium (no place assigned)

**Human Votes:**
- A judge must assign places to at least min(3, total_texts) different texts
- A judge can comment on any number of texts that didn't make the podium
- When a judge votes for the same place again, the previous vote for that place is replaced

**AI Votes:**
- Users can submit multiple votes using different AI judges (agents)
- When voting with an AI model that was previously used, all previous votes with that model are deleted first
- The same restrictions apply to each AI model
- The same user can have multiple sets of votes in a contest: one as a human judge and multiple as AI judges

**Small Contests:**
- For contests with fewer than 3 texts, judges only need to assign all possible places
- For example, in a contest with 2 texts, only 1st and 2nd places are required

### GET /contests/{contest_id}/votes

**Summary:** Get all votes for a contest

Get all votes for a specific contest.

- Only the contest creator, assigned judges, and admins can view votes for a contest

### GET /contests/{contest_id}/votes

**Summary:** Get all votes for a contest

Get all votes for a specific contest.

- Only the contest creator, assigned judges, and admins can view votes for a contest

### GET /contests/{contest_id}/votes/{judge_id}

**Summary:** Get votes by a specific judge in a contest

Get votes submitted by a specific judge in a contest.

- Only the contest creator, the judge themselves, and admins can view a judge's votes
- Will return all votes by the judge, including both human and AI votes

### GET /contests/{contest_id}/votes/{judge_id}

**Summary:** Get votes by a specific judge in a contest

Get votes submitted by a specific judge in a contest.

- Only the contest creator, the judge themselves, and admins can view a judge's votes
- Will return all votes by the judge, including both human and AI votes

### DELETE /votes/{vote_id}

**Summary:** Delete a vote

Delete a vote.

- Only the judge who created the vote or an admin can delete it
- Votes cannot be deleted from closed contests

### DELETE /votes/{vote_id}

**Summary:** Delete a vote

Delete a vote.

- Only the judge who created the vote or an admin can delete it
- Votes cannot be deleted from closed contests


---

*This document was generated automatically by capturing the FastAPI OpenAPI schema from the API server.*