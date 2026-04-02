# FHIR Doc Insight (WIP)

A clinical documentation viewer that aggregates patient and encounter data from FHIR-compliant healthcare systems.

## Overview

Connects to FHIR R4 servers to fetch and display clinical data in a unified dashboard. The application caches data locally for fast access and provides a clean interface for viewing patient encounters.

[Dashboard Screenshot](docs/images/dashboard.png)

[Agent Conversation Screenshot](docs/images/Screenshot 2026-04-02 at 1.14.08 PM.png)

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

## Local Development Setup

### Prerequisites

- Docker and Docker Compose
- Java 11+ (for Synthea data generation)

### Step 1 — Download Synthea

Download the Synthea JAR (~150MB) from GitHub releases:

```bash
curl -LO https://github.com/synthetichealth/synthea/releases/latest/download/synthea-with-dependencies.jar
```

### Step 2 — Generate Synthea data (one time)

Run Synthea locally to generate synthetic patient data:

```bash
java -jar synthea-with-dependencies.jar \
  -p 100 \
  --exporter.fhir.export true \
  --exporter.fhir.transaction_bundle true \
  Massachusetts

cp output/fhir/*.json synthea-data/
```

This generates approximately 100–150 JSON files. These are gitignored
and must be generated locally before first run.

**Tip:** To generate patients with recent encounters, use a reference date and keep module:

```bash
# Create keep module for patients with chronic conditions
cat > keep_active_patients.json << 'EOF'
{
  "name": "Keep Patients with Active Conditions",
  "states": {
    "Initial": { "type": "Initial", "direct_transition": "Check" },
    "Check": {
      "type": "Simple",
      "conditional_transition": [
        {
          "condition": {
            "condition_type": "Or",
            "conditions": [
              {"condition_type": "Active Condition", "codes": [{"system": "SNOMED-CT", "code": "44054006"}]},
              {"condition_type": "Active Condition", "codes": [{"system": "SNOMED-CT", "code": "38341003"}]},
              {"condition_type": "Active Condition", "codes": [{"system": "SNOMED-CT", "code": "195967001"}]}
            ]
          },
          "transition": "Keep"
        },
        {"transition": "Discard"}
      ]
    },
    "Keep": { "type": "Terminal" },
    "Discard": { "type": "Terminal" }
  }
}
EOF

# Generate with today's reference date
java -jar synthea-with-dependencies.jar \
  -p 50 \
  -r $(date +%Y%m%d) \
  -k keep_active_patients.json \
  --exporter.fhir.export true \
  --exporter.fhir.transaction_bundle true \
  --exporter.baseDirectory ./synthea-data \
  Massachusetts
```

### Step 3 — Start the stack

```bash
docker compose up
```

**First run:** HAPI FHIR starts, becomes healthy (~30–60 seconds),
then the loader POSTs all Synthea bundles (~2–5 minutes for 100
patients). The backend starts only after loading is complete.

**Subsequent runs:** The loader detects the `.loaded` marker and
exits immediately. Startup takes ~30 seconds.

### Step 4 — Verify

FHIR server: http://localhost:8080/fhir/metadata
Patient count: http://localhost:8080/fhir/Patient?_summary=count
Backend: http://localhost:8000/docs

### Resetting data

To wipe the FHIR server and reload from scratch:

```bash
docker compose down -v          # removes hapi-data volume
rm synthea-data/.loaded         # clears the loader marker
docker compose up               # reloads all bundles on next start
```
