# Frontend - Konecto AI Agent

Next.js 15 frontend application for the Konecto AI Agent microservice.

## Tech Stack

- **Next.js 15**: React framework with App Router
- **React 18**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS** (optional): For styling

## Setup

```bash
npm install
npm run dev
```

The application will be available at http://localhost:3000

## Build

```bash
npm run build
npm start
```

## Development

```bash
# Run development server
npm run dev

# Run linting
npm run lint
```

## Docker

The frontend is containerized and can be run with:

```bash
docker build -t konecto-frontend .
docker run -p 3000:3000 konecto-frontend
```

Or use docker-compose from the root directory.
