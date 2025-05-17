FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy source files
COPY . .

# Generate env-config.js
RUN echo "window.env = { VITE_API_BASE_URL: '${VITE_API_BASE_URL:-http://localhost:8000}' };" > /app/public/env-config.js

EXPOSE 3001

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3001"] 