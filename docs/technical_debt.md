# Technical Debt and Future Improvements

This document lists known technical debt, areas for refactoring, and potential future improvements.

## Frontend

* **API URL Configuration**: The current setup has issues with cross-origin requests between the frontend and backend. This needs to be properly configured to ensure seamless communication between the two services.

* **Development vs. Production Setup**: There are two approaches for development:
  1. **Local Development**: Running backend in Docker, frontend on host with Vite proxy configuration
  2. **Containerized Development**: Running both frontend and backend in Docker with proper network configuration

## Backend

*   *(No immediate items identified from recent work, but this section can be used as needed)* 