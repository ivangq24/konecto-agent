# Konecto AI Agent - Series 76 Electric Actuators

Intelligent AI agent microservice with frontend interface for technical expert assistance on Series 76 Electric Actuators.

## Project Structure

```text
konecto-agent/
├── backend/                      # FastAPI backend microservice
│   ├── app/
│   │   ├── agent/               # LangChain agent and tools
│   │   ├── api/                 # API routes
│   │   ├── models/              # Pydantic schemas
│   │   ├── services/            # Business logic (DataService)
│   │   ├── config.py            # Application configuration
│   │   └── main.py              # FastAPI entry point
│   ├── data/
│   │   ├── raw/                 # Raw PDF source files
│   │   └── processed/           # Generated CSVs, SQLite DB, Chroma DB
│   ├── scripts/                 # Data processing pipeline
│   │   ├── ingest.py            # PDF extraction (Gemini)
│   │   ├── rename_csv_files.py  # CSV file renaming
│   │   ├── build_sqlite_db.py   # SQLite builder
│   │   ├── build_vector_db.py   # ChromaDB builder
│   │   └── process_data.py      # Orchestrator script
│   ├── evaluation/              # Agent evaluation suite (Langfuse)
│   ├── tests/                   # Pytest test suite
│   ├── Dockerfile               # Backend Dockerfile
│   └── requirements.txt         # Python dependencies
├── frontend/                     # Next.js 15 + React frontend
│   ├── app/                     # App Router pages & API proxies
│   ├── components/              # React components (Chat UI)
│   ├── Dockerfile               # Frontend Dockerfile
│   └── package.json             # Node.js dependencies
├── docker-compose.yml            # Orchestration (Backend + Frontend)
└── README.md                     # Project documentation
```

## Setup Instructions

### Prerequisites

- Docker and Docker Compose installed
- Git installed
- Valid OpenAI API key
- Valid Google API key (for PDF extraction)
- (Optional) Langfuse Cloud account for observability

### 1. Clone the repository

```bash
git clone <repository-url>
cd konecto-agent
```

### 2. Configure environment variables

**Backend**:

```bash
cd backend
cp .env.example .env
# Edit backend/.env and set at least:
# OPENAI_API_KEY=sk-xxxx
# GOOGLE_API_KEY=xxxx
# (Optional) LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY for Langfuse Cloud
cd ..
```

**Frontend**:

```bash
cd frontend
cp .env.example .env
# Ensure NEXT_PUBLIC_API_URL points to the backend service
# For browser access, use localhost (not backend hostname):
# NEXT_PUBLIC_API_URL="http://localhost:8000"
cd ..
```

## How to Run

### 1. Build Docker Images

From the project root:

```bash
docker-compose build
```

### 2. Run Data Processing Pipeline

Before starting the API, you must process the raw PDF data. Run the orchestrator script inside the backend container:

```bash
# This runs the full pipeline:
# 1. Extract tables from PDF (ingest.py)
# 2. Rename CSV files with descriptive names (rename_csv_files.py)
# 3. Build SQLite database (build_sqlite_db.py)
# 4. Build vector database (build_vector_db.py)

docker-compose run --rm backend python scripts/process_data.py
```

### 3. Start Services

Once data is processed, start the backend and frontend:

```bash
docker-compose up
# Or in detached mode:
# docker-compose up -d
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Data Processing

The data pipeline is automated via `backend/scripts/process_data.py`. It performs four steps sequentially:

1.  **Ingestion**: Uses Google Gemini 2.5 Pro to extract tables from the PDF into structured CSVs.
2.  **File Renaming**: Renames CSV files with descriptive names based on `Context_Type` and `Enclosure_Type` (e.g., `220V_3_Phase_Power_WEATHERPROOF_CSA_CE_UKCA.csv`).
3.  **Structured Storage (SQLite)**: Consolidates all CSVs into a single SQLite table with a JSON column for flexible schema querying (exact match).
4.  **Vector Storage (ChromaDB)**: Chunks data row-by-row into text embeddings for semantic search.

You can re-run the pipeline at any time to update the databases if the source PDF changes.

## Architecture & Design Choices

### Architecture

1.  **Microservices**: Separated backend (FastAPI) and frontend (Next.js) allows independent scaling, technology choices, and deployment lifecycles.
2.  **Containerization**: Docker guarantees a consistent environment for both development and production.
3.  **RAG Strategy**: Hybrid search approach combining:
    *   **SQLite**: For precise part number lookups and filtering.
    *   **ChromaDB**: For semantic queries ("high torque actuator for 24V").

### Backend Design

*   **FastAPI**: High-performance, async-native framework.
*   **LangChain**: Orchestrates the agent reasoning loop and tool usage.
*   **Agent Pattern**: Uses a tool-calling agent that decides whether to query the database (exact) or the vector store (semantic) based on user intent.
*   **Observability**: Integrated with **Langfuse Cloud** for tracing agent steps, latency, and costs.

### Frontend Design

*   **Next.js 15 (App Router)**: Modern React framework for server-side rendering and efficient routing.
*   **Tailwind CSS**: Utility-first styling for a clean, responsive chat interface.
*   **Chat Interface**: Maintains conversation context (`conversation_id`) and handles real-time updates.

## Evaluation

The project includes an automated evaluation suite in `backend/evaluation/`.

To run the evaluation (requires Langfuse Cloud keys configured):

```bash
docker-compose run --rm backend python evaluation/evaluate_agent.py
```

This script runs a set of predefined test cases against the agent and logs scores (accuracy, tool usage, etc.) to Langfuse.

## Troubleshooting

### Port Conflicts
If ports 3000 or 8000 are busy, modify `docker-compose.yml` to map to different host ports (e.g., `"8080:8000"`).

### Data Not Found
If the agent returns no results, ensure:
1. The PDF was in `backend/data/raw/` before running the pipeline.
2. The pipeline `scripts/process_data.py` completed successfully.
3. `DATA_STORAGE` is set to `sqlite` (default) or `chroma` in `.env`.

### Langfuse Errors
If you see Langfuse connection errors, verify that `LANGFUSE_HOST` is set to `https://cloud.langfuse.com` and your keys are correct in `backend/.env`.
