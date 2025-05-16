# Duelo de Plumas Frontend

This is the frontend for the Duelo de Plumas v3 literary contest platform.

## Features

- User authentication with JWT support
- Contest management
- Text submission
- AI agent integration
- Judging interface

## Technology Stack

- React + TypeScript
- Vite for bundling
- Zustand for state management
- React Router for navigation
- Tailwind CSS for styling
- React Hook Form for form handling
- Axios for API requests

## Getting Started

### Prerequisites

- Node.js (>= 16.x)
- npm or yarn

### Installation

1. Clone the repository
2. Install dependencies:

```bash
npm install
# or 
yarn install
```

3. Create a `.env` file in the root directory with the following content:

```
VITE_API_BASE_URL=http://localhost:8000
```

### Development

To start the development server:

```bash
npm run dev
# or
yarn dev
```

This will start the development server at http://localhost:3000.

### Building for Production

To build for production:

```bash
npm run build
# or
yarn build
```

This will generate a production build in the `dist` directory.

### Authentication

The application uses JWT for authentication with the following features:
- Secure token storage
- Automatic token refresh
- Protected routes
- Role-based access control

## Project Structure

```
src/
├── components/      # Reusable UI components
├── hooks/           # Custom React hooks
├── pages/           # Page components
├── services/        # API integration
├── store/           # Global state management
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
``` 