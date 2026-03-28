# Spec: FHIR Development Infrastructure with Synthea Data Loading

## Overview

Set up the local development infrastructure for ClinDoc Insight. This includes a HAPI FHIR R4 server, a curl-based Synthea data loader that runs once on first startup, and wiring the FastAPI backend to wait for both before starting.

The goal is that `docker compose up` on a fresh clone results in a fully populated FHIR server ready for development, with no manual steps beyond pre-generating Synthea data.

---

## What to build

### 1. Directory structure

Create the following structure. Do not create files that already exist.

```
project-root/
├── docker-compose.yml
├── synthea-data/
│   └── .gitkeep              # empty placeholder — bundles go here
└── scripts/
    └── load_synthea.sh
```

---

### 2. `docker-compose.yml`

Three services: `hapi-fhir`, `fhir-loader`, `backend`.

**hapi-fhir**
- Image: `hapiproject/hapi:latest`
- Expose port `8080` on the host
- Environment:
  - `hapi.fhir.fhir_version=R4`
  - `hapi.fhir.allow_multiple_delete=true`
- Named volume `hapi-data` mounted at `/data/hapi` for persistence
- Healthcheck:
  - Test: `curl -f http://localhost:8080/fhir/metadata`
  - Interval: `10s`
  - Timeout: `5s`
  - Retries: `10`
  - Start period: `30s`

**fhir-loader**
- Image: `curlimages/curl:latest`
- Depends on `hapi-fhir` with condition `service_healthy`
- Mounts:
  - `./synthea-data` → `/synthea-data` (read-only)
  - `./scripts/load_synthea.sh` → `/load_synthea.sh` (read-only)
- Entrypoint: `["/bin/sh", "/load_synthea.sh"]`
- Restart policy: `no` — runs once and exits
- No exposed ports

**backend**
- This already exists but needs to be modified
- Build context: `./backend` (may not exist yet — that is fine, do not create it)
- Expose port `8000` on the host
- Depends on:
  - `hapi-fhir` with condition `service_healthy`
  - `fhir-loader` with condition `service_completed_successfully`
- Environment:
  - `FHIR_BASE_URL=http://hapi-fhir:8080/fhir`

**Volumes**

Declare a named volume `hapi-data` at the top level.

---

### 3. `scripts/load_synthea.sh`

Shell script that POSTs Synthea FHIR bundles to the HAPI server. Requirements:

**Skip if already loaded**

Check for a marker file at `/synthea-data/.loaded`. If it exists, print a message and exit 0 immediately. This prevents duplicate data on every `docker compose up`.

**Load all bundles**

Iterate over every `.json` file in `/synthea-data/`. For each file:
- POST it to `http://hapi-fhir:8080/fhir` with `Content-Type: application/fhir+json`
- Capture the HTTP status code using `curl -s -o /dev/null -w "%{http_code}"`
- If status is `200` or `201`, increment a loaded counter
- If any other status, print a warning with the filename and status code, increment a failed counter

**Write the marker**

After all bundles are processed, write the marker file at `/synthea-data/.loaded`. Do this even if some bundles failed — partial loads are recoverable by deleting the marker and re-running.

**Print a summary**

On completion print: `Done. Loaded: N, Failed: N`

**Exit codes**
- Exit `0` always. A partial failure should not prevent the backend from starting.

---

### 4. `.gitignore` additions

Append to `.gitignore` (create it if it does not exist):

```
# Synthea FHIR bundles — generate locally, do not commit
synthea-data/*.json

# Loader marker file
synthea-data/.loaded
```

The `synthea-data/` directory itself and the `.gitkeep` placeholder should be tracked. The generated JSON bundles and the marker file should not.

---

### 5. README section

Append a `## Local Development Setup` section to `README.md` (create it if it does not exist) with the following content:

````markdown
## Local Development Setup

### Prerequisites

- Docker and Docker Compose
- Java 11+ (for Synthea data generation)
- [Synthea](https://github.com/synthetichealth/synthea/releases) — download `synthea-with-dependencies.jar`

### Step 1 — Generate Synthea data (one time)

Run Synthea locally to generate synthetic patient data and copy the
output into `synthea-data/`:

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

### Step 2 — Start the stack

```bash
docker compose up
```

**First run:** HAPI FHIR starts, becomes healthy (~30–60 seconds),
then the loader POSTs all Synthea bundles (~2–5 minutes for 100
patients). The backend starts only after loading is complete.

**Subsequent runs:** The loader detects the `.loaded` marker and
exits immediately. Startup takes ~30 seconds.

### Step 3 — Verify

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
````

---

## Constraints and notes

- Do not modify any existing files other than appending to `.gitignore` and `README.md`
- Do not create the `backend/` directory or any Python files — that is out of scope for this spec
- The `synthea-data/` directory will be empty (except `.gitkeep`) when this spec is implemented — that is expected and correct
- The loader script must be `sh`-compatible, not `bash`-specific — the `curlimages/curl` image uses BusyBox sh
- Use `--data-binary` in the curl POST, not `--data` or `-d`, to handle large bundle files correctly
- The marker file path `/synthea-data/.loaded` must match between the shell script and the README reset instructions

---

## Acceptance criteria

- [ ] `docker compose up` starts without errors on a machine with Docker installed and Synthea bundles present in `synthea-data/`
- [ ] HAPI FHIR is reachable at `http://localhost:8080/fhir/metadata` after startup
- [ ] Running `docker compose up` a second time skips the loader (marker file check works)
- [ ] Running `docker compose down -v && rm synthea-data/.loaded && docker compose up` triggers a full reload
- [ ] The backend service does not start until both `hapi-fhir` is healthy and `fhir-loader` has completed
- [ ] `.json` files in `synthea-data/` are gitignored; the directory itself is tracked