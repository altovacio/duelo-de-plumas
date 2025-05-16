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
    *   [ ] **Overview Section:**
        *   "Urgent Actions" list (e.g., contests to evaluate).
        *   Credit balance display.
    *   [ ] **Contest Management (for owned contests):**
        *   [ ] Create New Contest Page/Modal.
        *   [ ] Edit Contest Page/Modal.
        *   [ ] Delete Contest functionality.
        *   [ ] View list of owned contests.
    *   [ ] **Text Management:**
        *   [ ] Create New Text Page/Modal (using `react-md-editor` for input or PDF upload).
        *   [ ] Edit Text Page/Modal.
        *   [ ] Delete Text functionality.
        *   [ ] View list of owned texts.
    *   [ ] **AI Agent Management (Writers & Judges):**
        *   [ ] Create New AI Agent Page/Modal.
        *   [ ] Edit AI Agent Page/Modal.
        *   [ ] Delete AI Agent functionality.
        *   [ ] View list of owned AI agents.
        *   [ ] Section for Public AI Agents (copyable).
    *   [ ] **Participation Tracking:**
        *   [ ] List of contests where user is an author.
        *   [ ] List of contests where user is a judge.
    *   [ ] **Credit Management:**
        *   [ ] Detailed credit transaction history.
        *   [ ] Filters for transaction history.

**Phase 4: Contest Interaction & AI Execution**

1.  **Submitting Texts to Contests:**
    *   [ ] Form to submit existing/new text.
    *   [ ] Handle submission restrictions.
2.  **Judging Contests:**
    *   [ ] **Human Judging Interface.**
    *   [ ] **AI Judge Execution UI/flow.**
    *   [ ] Display estimated credit cost before execution.
    *   [ ] Confirmation dialog showing potential credit usage.
3.  **AI Writer Execution:**
    *   [ ] AI Writer execution UI/flow.
    *   [ ] Display estimated credit cost before execution.
    *   [ ] Confirmation dialog showing potential credit usage.
4.  **Viewing Contest Results:**
    *   [ ] Display ranked lists, author names, judge comments (rendered using `react-markdown`).
    *   [ ] Handle "TEXTO RETIRADO".

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