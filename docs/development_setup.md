# Development Setup Guide

This document describes how to set up and run the Duelo de Plumas application for development.

## Overview

Duelo de Plumas consists of:
- A FastAPI backend (Python)
- A React/TypeScript frontend
- A PostgreSQL database

There are two recommended approaches for development:

## Approach 1: Local Frontend Development (Recommended)

This approach runs the backend and database in Docker, while the frontend runs directly on your local machine. This enables faster frontend development with hot reloading.

### Steps:

1. **Start the backend and database with Docker Compose:**
   ```bash
   docker-compose up -d backend db
   ```

2. **Run the frontend locally:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Access the application:**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### How It Works:

The frontend runs on port 3001 and uses Vite's built-in proxy to forward API requests to the backend running in Docker on port 8000. This avoids CORS issues while keeping the frontend development experience smooth.

## Approach 2: Fully Containerized Development

This approach runs all components (frontend, backend, and database) in Docker containers. This ensures a consistent environment but may be slower for frontend development.

### Steps:

1. **Start all services with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

2. **Access the application:**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Troubleshooting

### CORS Issues

If you encounter CORS errors when the frontend tries to communicate with the backend:

1. Ensure the backend is running and accessible
2. Check that the frontend's Vite configuration has the correct proxy settings
3. Verify that the backend's CORS configuration in `backend/app/core/config.py` includes your frontend's origin

### API Connection Issues

If the frontend cannot connect to the API:

1. Check that the backend container is running (`docker-compose ps`)
2. Ensure the frontend is using the correct API URL (localhost:8000 for local development)
3. Check backend logs for any errors: `docker-compose logs -f backend` 