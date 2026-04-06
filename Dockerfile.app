# Build stage for React frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
RUN npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build

# The built files will be served by the API container
# This Dockerfile is kept for docker-compose compatibility
