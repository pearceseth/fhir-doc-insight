## Compliance Architecture

This project is built against synthetic data only (Epic public
sandbox and HAPI public test server). No real patient data is
used at any point.

### De-identification before LLM

All data passed to the local LLM is de-identified per the
HIPAA Safe Harbor method (45 CFR §164.514(b)) before leaving
the analytics layer. This includes:

- Deterministic stripping of 18 Safe Harbor identifiers
  from structured FHIR fields by resource path
- NER-based PHI detection in free text via Microsoft Presidio
- Consistent tokenization of patient/encounter IDs via
  HMAC-SHA256 to preserve relational integrity without
  exposing actual identifiers

De-identification runs as a transform step immediately before
data reaches the LLM — not as a storage operation. Raw FHIR
resources are cached in memory and are never modified.

### Local LLM — No PHI Transmission

The LLM (Ollama, running locally) never receives raw FHIR
data. There is no call to any public LLM API (OpenAI,
Anthropic, etc.). This mirrors the architecture a health
system would require before any AI feature could be deployed
against real patient data.

In a production deployment, additional requirements would
include: BAA with any cloud AI vendor, security review,
data governance approval, and likely IRB review if used
for research purposes.

### SMART on FHIR

OAuth 2.0 authorization codes with clinical scopes
(patient/Patient.read, patient/Observation.read, etc.).
Tokens are held in FastAPI application state only —
never written to disk or persisted in any cache.

### No Database

No patient-adjacent data is written to disk. All FHIR
resources are held in an in-memory cache (aiocache) with
TTL expiration. All data is lost on process restart,
which is intentional for a local demo context.