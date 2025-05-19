# Frontend Implementation Plan

This document outlines the major frontend development tasks for Duelo de Plumas v3, aligning with the detailed project description.

**Phase 1: Core Structure & Authentication**

1.  **Project Setup:**
    *   [x] Scaffold React frontend with Vite.
    *   [x] Install core dependencies: React Router, Zustand (for state management), Tailwind CSS (for styling), React Hook Form (for form handling).
    *   [x] Set up project structure (components, pages, services, utils, assets).
    *   [x] Setup ESLint (with a standard React config like eslint-config-airbnb or community best practices) and Prettier for code linting and formatting.
    *   [x] Fix TypeScript configuration and dependency issues (May 16, A2023)
2.  **Layout & Navigation:**
    *   [x] Create main application layout (Header, Footer, Sidebar/Navigation).
    *   [x] Implement responsive navigation for different screen sizes.
3.  **Authentication & User Roles:**
    *   [x] **Visitor View:**
        *   [x] Registration Page (`/register`)
        *   [x] Login Page (`/login`)
    *   [x] **User Authentication Flow:**
        *   [x] Implement API calls for registration and login.
        *   [x] Token handling (storage, refresh, and secure transmission).
        *   [x] Protected routes for authenticated users.
        *   [ ] "Forgot Password" / "Reset Password" flow (deferred).
    *   [x] **Role-based Access Control (RBAC) Foundations:**
        *   [x] Mechanism to identify user roles (Visitor, User, Admin) after login.
        *   [x] Basic UI differentiation based on role (e.g., showing/hiding menu items).

**Phase 2: Public-Facing Pages & Contest Viewing**

1.  **Homepage (`/`):**
    *   [x] Welcome message section.
    *   [x] "Recently Opened Contests" highlight section (dynamic component).
    *   [x] "Recently Closed Contests" highlight section (dynamic component).
2.  **Contest Listing Page (`/contests`):**
    *   [x] Display all contests (public and private).
    *   [x] `ContestCard` component:
        *   Title, brief description, number of participants, last modification date, end date (if any), type (public/private), status (open/evaluation/closed).
        *   Visual indicator for contest type and status.
    *   [x] Filtering and Sorting options (e.g., by status, type, creation date).
    *   [ ] Pagination for large numbers of contests.
3.  **Contest Detail Page (`/contests/:id`):**
    *   [x] **Public View (Visitor/User not participating/not owner):**
        *   Display full contest details: title, full description, creator, dates, type, status, number of authors/texts.
        *   If private, prompt for password to view details/participate.
        *   If open: Placeholder/message about submissions.
        *   If evaluation: Display participating texts (anonymized).
        *   If closed: Display final ranking, texts (with author/owner revealed), and judge comments.
    *   [x] **Password entry modal/section for private contests.**

**Phase 3: User Workspace & Core Functionality**

1.  **User Dashboard/Workspace (`/workspace` or `/dashboard`):**
    *   [x] **Overview Section:**
        *   "Urgent Actions" list (e.g., contests to evaluate).
        *   Credit balance display.
    *   [x] **Contest Management (for owned contests):**
        *   [x] Create New Contest Page/Modal.
        *   [x] Edit Contest Page/Modal.
        *   [x] Delete Contest functionality.
        *   [x] View list of owned contests.
    *   [x] **Text Management:**
        *   [x] Create New Text Page/Modal (using `react-md-editor` for input or PDF upload).
        *   [x] Edit Text Page/Modal.
        *   [x] Delete Text functionality.
        *   [x] View list of owned texts.
    *   [x] **AI Agent Management (Writers & Judges):**
        *   [x] Create New AI Agent Page/Modal.
        *   [x] Edit AI Agent Page/Modal.
        *   [x] Delete AI Agent functionality.
        *   [x] View list of owned AI agents.
        *   [x] Section for Public AI Agents (copyable).
    *   [x] **Participation Tracking:**
        *   [x] List of contests where user is an author.
        *   [x] List of contests where user is a judge.
    *   [x] **Credit Management:**
        *   [x] Detailed credit transaction history.
        *   [x] Filters for transaction history.

**Phase 4: Contest Interaction & AI Execution**

1.  **Submitting Texts to Contests:**
    *   [ ] Form to submit existing/new text.
        *   Implement form with text selection (from user's texts) or creation of new text
        *   Integration with `POST /contests/{contest_id}/submissions/` endpoint
        *   Handle password requirement for private contests
    *   [ ] Handle submission restrictions.
        *   Check contest status (must be "open")
        *   Implement validation for text length and format requirements
        *   Show appropriate error messages for submission failures
    *   [ ] Implementation of text withdrawal functionality using `DELETE /contests/{contest_id}/submissions/{submission_id}` endpoint

2.  **Judging Contests:**
    *   [ ] **Human Judging Interface:**
        *   Create voting form with placeholders for 1st, 2nd, 3rd place selections
        *   Add commentary fields for each text (both ranked and unranked)
        *   Implement validation for required rankings (at least min(3, total_texts))
        *   Integration with `POST /contests/{contest_id}/votes` endpoint
    *   [ ] **AI Judge Execution UI/flow:**
        *   Selection interface for AI judge agents
        *   Progress indicator during AI judging process
        *   Results display after completion
        *   Integration with `POST /agents/execute/judge` endpoint
    *   [ ] Display estimated credit cost before execution.
        *   Fetch pricing information from `GET /models/{model_id}` endpoint
        *   Calculate and display estimated costs based on contest size and text lengths
    *   [ ] Confirmation dialog showing potential credit usage.
        *   Modal with cost details and confirmation button
        *   Cancel option to prevent accidental credit usage

3.  **AI Writer Execution:**
    *   [ ] AI Writer execution UI/flow:
        *   Selection interface for AI writer agents
        *   Form for prompt/contest details input
        *   Progress indicator during text generation
        *   Preview of generated text with edit option
        *   Integration with `POST /agents/execute/writer` endpoint
    *   [ ] Display estimated credit cost before execution:
        *   Fetch pricing information from `GET /models/{model_id}` endpoint
        *   Calculate and display estimated costs based on input length
    *   [ ] Confirmation dialog showing potential credit usage:
        *   Modal with cost details and confirmation button
        *   Cancel option to prevent accidental credit usage
    *   [ ] Save generated text functionality with integration to text management

4.  **Viewing Contest Results:**
    *   [ ] Display ranked lists based on voting results:
        *   Fetch results using `GET /contests/{contest_id}/votes` endpoint
        *   Implement algorithm to calculate final rankings based on judge votes
        *   Create podium visualization for 1st, 2nd, and 3rd place
    *   [ ] Show author names and judge comments:
        *   Render comments using `react-markdown`
        *   Display author information only for closed contests
    *   [ ] Create detailed view for each text:
        *   Show all judge comments for a specific text
        *   Display voting breakdown
    *   [ ] Handle "TEXTO RETIRADO":
        *   Properly display placeholder for withdrawn texts
        *   Maintain ranking integrity when texts are withdrawn
    *   [ ] Create toggle views between different judge results:
        *   Allow switching between human and AI judge perspectives
        *   Implement filters for different voting criteria

**Phase 5: Administrator Panel**

1.  **Admin Dashboard (`/admin`).**
2.  **User Management (`/admin/users`):**
    *   [ ] Interface for assigning credits to users.
    *   [ ] Track and display credit allocation history.
3.  **Global AI Agent Management (`/admin/ai-agents`).**
4.  **Site & Credit Monitoring (`/admin/monitoring`):**
    *   [ ] Detailed reports of AI usage costs.
    *   [ ] Credit consumption analytics by user.
    *   [ ] Tools to analyze credit consumption patterns.
5.  **Contest Oversight (`/admin/contests`).**

**Phase 6: Styling, UX Enhancements & Finalization**

1.  **Global Styling & Theming** (Auric proportions, sleek, minimalistic using Tailwind CSS).
2.  **Markdown Editor Integration:**
    *   [ ] Ensure `react-markdown` is used for all Markdown rendering.
    *   [ ] Ensure `react-md-editor` is used for Markdown input where rich editing is provided.
3.  **Responsiveness.**
4.  **User Experience (UX) Polish** (feedback, intuitive flows, accessibility).
5.  **Error Handling.**
6.  **Performance Optimization.**

**Phase 7: Documentation & Deployment**

1.  **Frontend README.md.**
2.  **Testing** (Unit, Integration).
3.  **Dockerize Frontend.**
4.  **Deployment (CI/CD).** 