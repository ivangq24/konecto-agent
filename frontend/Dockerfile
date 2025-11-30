# Dockerfile optimized for DEVELOPMENT

FROM node:18-alpine

# Set environment variables for development
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1
ENV WATCHPACK_POLLING=true

# Set working directory
WORKDIR /app

# Install system dependencies required for development
RUN apk add --no-cache \
    libc6-compat \
    git \
    vim \
    curl \
    htop \
    procps

# Copy dependency files
COPY package*.json ./

# Install ALL dependencies (including devDependencies)
RUN npm install

# Create directory for development logs
RUN mkdir -p /app/logs

# Expose port
EXPOSE 3000

# Command to run the application in development mode with hot-reload
CMD ["npm", "run", "dev"]
