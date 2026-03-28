# FHIR Doc Insight (WIP)

A clinical documentation viewer that aggregates patient and encounter data from FHIR-compliant healthcare systems.

## Overview

ClinDoc Insight connects to FHIR R4 servers to fetch and display clinical data in a unified dashboard. The application caches data locally for fast access and provides a clean interface for viewing patient encounters.

## Prerequisites

- Docker and Docker Compose, or:
- Python 3.11+ and Node.js 22+

## Quick Start

### Using Docker (Recommended)

```bash
docker compose up -d
```

On first run, the llama3 model (~4GB) will be downloaded. Watch progress with:

```bash
docker compose logs -f ollama-pull
```

Once the model is pulled, the assistant will be available. Open http://localhost:5173 in your browser.

**GPU Support (Optional):** For NVIDIA GPU acceleration, uncomment the `deploy` section under the `ollama` service in `docker-compose.yml`.

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Configuration

Environment variables can be set in the backend:

| Variable | Default | Description |
|----------|---------|-------------|
| `FHIR_BASE_URL` | `http://hapi.fhir.org/baseR4` | FHIR server endpoint |
| `FHIR_CACHE_TTL` | `3600` | Cache time-to-live in seconds |
| `PATIENT_FETCH_COUNT` | `20` | Number of patients to fetch |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server endpoint |
| `OLLAMA_MODEL` | `llama3` | LLM model to use |
