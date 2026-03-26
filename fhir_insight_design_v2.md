# ClinDoc Insight — Project Design Document

**A FHIR-native clinical documentation analytics platform with local LLM integration**

*Portfolio project — Seth Pearce*

---

## 1. Project Overview

ClinDoc Insight is a locally-hosted clinical analytics application that connects to FHIR R4-compliant EHR systems, analyzes clinical documentation patterns across patient encounters, and surfaces actionable workflow insights using a locally-hosted LLM. The application is designed to demonstrate FHIR fluency, SMART on FHIR authorization, healthcare data literacy, responsible AI architecture in a clinical context, and the kind of documentation burden analysis that clinical informatics teams perform daily.

The system is intentionally architected to mirror what a compliant, production-ready health system tool would look like — including a de-identification layer before any data touches an AI model, a local LLM to avoid PHI transmission to public APIs, and explicit references to HIPAA Safe Harbor throughout the codebase.

---

## 2. Problem Statement

Clinical documentation burden is one of the leading drivers of clinician burnout. Nurses and physicians spend a disproportionate amount of time in the EHR — charting, reconciling medications, completing flowsheets — rather than providing direct patient care. Clinical informatics analysts are tasked with identifying where this burden is heaviest and optimizing the workflows that cause it.

Today this analysis is largely manual: informatics teams review reports, interview staff, and rely on intuition built over years of experience. ClinDoc Insight demonstrates what a data-driven, AI-assisted version of that workflow could look like.

---

## 3. Core Features

### 3.1 FHIR Data Ingestion
- Connects to any FHIR R4-compliant server (Epic sandbox, HAPI public server, or local HAPI instance)
- Supports SMART on FHIR standalone launch (OAuth 2.0 authorization code flow) for Epic-compatible auth
- Also supports unauthenticated access for the HAPI public sandbox during development
- Fetches: Patient, Encounter, Observation, DocumentReference, MedicationRequest, MedicationAdministration, Condition
- Resources are cached in-memory on first fetch; subsequent accesses are served from cache (see Section 5)

### 3.2 De-identification Layer
- Strips all 18 HIPAA Safe Harbor identifiers before any data is passed to the LLM
- Replaces identifiers with consistent synthetic tokens (relational integrity preserved, actual identifiers gone)
- De-identification runs as a transformation step on the way out to the LLM — not as a separate storage operation
- Raw FHIR resources and de-identified versions never co-mingle; the boundary is enforced in code

### 3.3 Documentation Analytics Dashboard
- **Documentation completeness scoring** per encounter: checks presence of expected Observation categories (vitals, pain, nursing assessment, I/O) and surfaces gaps
- **Observation density by encounter type**: volume of observations recorded per encounter, broken down by category and unit
- **Medication reconciliation completeness**: presence of MedicationRequest records and linked MedicationAdministration records per encounter
- **Note coverage**: whether DocumentReference (clinical notes) exist per encounter type
- **Trend views**: metrics over time to identify systemic workflow issues vs. one-off gaps
- All analytics computed in Python over in-memory cached FHIR data — no database queries required

### 3.4 LLM Features (Ollama)

Three distinct LLM-powered features, all routed through a local Ollama instance. Only Feature c is a true agent in the technical sense — Features a and b are single-shot LLM pipelines.

**a) Clinical Note Summarization** *(pipeline — single Ollama call)*
- Input: de-identified DocumentReference free text
- Output: structured summary — chief complaint, key clinical findings, outstanding documentation items
- Mirrors what ambient documentation tools like Nuance DAX produce
- Implemented as a direct Ollama API call, not via LangChain

**b) Documentation Gap Narrative** *(pipeline — single Ollama call)*
- Input: an encounter's completeness gap list (missing Observations, incomplete med rec)
- Output: plain-English explanation of what's missing, why it matters clinically, and what workflow change could address it
- Output format suitable for sharing with nursing staff — non-technical, actionable
- Pairs naturally with Feature c: the agent's completeness tool produces the gap data; narrative is a second call on top
- Implemented as a direct Ollama API call, not via LangChain

**c) Natural Language FHIR Query Agent** *(true ReAct agent — LangChain)*
- Accepts plain-English questions about the dataset
- LLM decides which tools to call, reasons over results, calls further tools as needed
- Example queries: *"Which encounter types have the lowest documentation completeness?"* / *"Show me patients with incomplete medication reconciliation from the last 30 days"*
- Constrained to exactly four tools — cannot make arbitrary API calls (see Section 7)
- Cache is pre-warmed on session start so all agent tool calls are fast in-memory lookups

### 3.5 SMART on FHIR Auth Flow
- Complete standalone launch implementation against Epic's public sandbox
- Authorization redirect construction with clinical scopes (`patient/Patient.read`, `patient/Observation.read`, etc.)
- Auth code exchange for access token
- Token refresh handling
- Tokens stored in application memory only — never persisted to disk
- Documented in README with sequence diagram

---

## 4. System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Browser  (React + TypeScript)              │
│   Dashboard │ Patient Explorer │ NL Query │ Note Summarizer  │
└───────────────────────────┬──────────────────────────────────┘
                            │  HTTP / REST
┌───────────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend  (Python)                    │
│                                                               │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │  FHIR Client │  │  De-ID Layer   │  │   LLM Agent     │  │
│  │  fhirclient  │  │  Safe Harbor   │  │   LangChain     │  │
│  │  SMART auth  │  │  Presidio NER  │  │  4 FHIR tools   │  │
│  └──────┬───────┘  └──────┬─────────┘  └────────┬────────┘  │
│         │                 │  de-identify          │           │
│         │                 │  on the way out       │           │
│  ┌──────▼─────────────────▼───────────────────────▼────────┐ │
│  │              aiocache  (in-memory, TTL-based)            │ │
│  │                                                          │ │
│  │  TTLCache: raw FHIR resources  (key: resource_type:id)  │ │
│  │  TTLCache: LLM outputs         (key: encounter_id)      │ │
│  │  App state: auth tokens        (memory only, no TTL)    │ │
│  └──────────────────────────────────────────────────────── ┘ │
│                                                               │
│  Analytics: pure Python + pandas over cached FHIR objects    │
└───────────────────────────────────────────────────────────────┘
              │                              │
 ┌────────────▼──────────┐      ┌────────────▼─────────┐
 │    FHIR Server         │      │   Ollama  (local)    │
 │  Epic Sandbox  OR      │      │   llama3 / mistral   │
 │  HAPI Public   OR      │      │   localhost:11434    │
 │  Local HAPI            │      └──────────────────────┘
 └───────────────────────┘
```

**Key architectural decisions:**

1. **No database.** All FHIR resources are cached in-memory via `aiocache`. Analytics are computed in Python over those cached objects. No SQLite, no DuckDB, no ORM. This is appropriate for a single-user local app with a read-only FHIR connection and a small synthetic dataset.

2. **De-identification as a transform, not storage.** De-identified versions of resources are not stored separately. They are produced on-demand by the de-identification pipeline when data is about to be passed to the LLM. The raw cached resource is never modified.

3. **Auth tokens in application memory only.** OAuth tokens are held in FastAPI application state (`app.state`). They are never written to disk, never cached via `aiocache`.

4. **Cache pre-warming.** On session start, the backend eagerly fetches the patient list and recent encounters into the cache. This ensures the NL Query agent's tool calls hit warm cache rather than making live FHIR API calls mid-reasoning chain.

---

## 5. Caching Design (Detail)

### Why in-memory rather than a database

The access patterns across all stored data don't warrant a database:

| Data | Access Pattern | Storage Choice |
|---|---|---|
| Raw FHIR resources | Write once on fetch, read by ID or patient ID | `aiocache` TTLCache |
| LLM outputs (summaries, narratives) | Write once after generation, read by encounter ID | `aiocache` TTLCache |
| Analytics results | Computed on-demand from cached FHIR objects | Not stored — recomputed |
| Auth tokens | Single record, read on every API call | FastAPI `app.state` |

For the analytics specifically: given a small synthetic dataset (hundreds of encounters), recomputing completeness scores and observation density over in-memory Python objects is fast enough that materialization into a database adds complexity with no measurable benefit.

### aiocache configuration

`aiocache` is async-native and works naturally with FastAPI's async model. Its key advantage over a plain Python `dict` or `cachetools` is interface compatibility with Redis — swapping the in-memory backend for Redis in a production deployment requires a single config change, not a code change.

```python
from aiocache import Cache
from aiocache.serializers import JsonSerializer

# Raw FHIR resources — 1 hour TTL
fhir_cache = Cache(Cache.MEMORY, serializer=JsonSerializer(), ttl=3600)

# LLM outputs — longer TTL, expensive to regenerate
llm_cache = Cache(Cache.MEMORY, serializer=JsonSerializer(), ttl=86400)
```

### Cache key conventions

```
Patient:{fhir_id}
Encounter:{fhir_id}
Observation:encounter:{encounter_id}       # all observations for an encounter
DocumentReference:encounter:{encounter_id}
MedicationRequest:encounter:{encounter_id}
MedicationAdministration:encounter:{encounter_id}
Condition:patient:{patient_id}
llm:summary:{document_reference_id}
llm:gap_narrative:{encounter_id}
encounters:patient:{patient_id}            # encounter list for a patient
```

### Cache pre-warming

```python
@app.on_event("startup")
async def warm_cache():
    """
    Pre-fetch top-level resources on startup so the NL Query agent
    has a warm cache for all tool calls. Detailed resources
    (Observations, etc.) are fetched lazily on first access.
    """
    patients = await fhir_client.fetch_patient_list()
    for patient in patients:
        await fhir_cache.set(f"Patient:{patient.id}", patient.dict(), ttl=3600)
        encounters = await fhir_client.fetch_encounters(patient.id)
        await fhir_cache.set(f"encounters:patient:{patient.id}", 
                             [e.dict() for e in encounters], ttl=3600)
```

### Consistency model

The cache is a read-through cache against a read-only FHIR server. There are no writes back to the FHIR server, so write consistency is not a concern. The only consistency consideration is **cache staleness**: a clinician could update a record on the FHIR server while the cache holds an older version. This is addressed by TTL expiration — after 1 hour, the cache entry expires and the next read fetches fresh data.

For the NL Query agent specifically: all tool calls within a single agent run access the same in-memory cache, so there is no possibility of inconsistency between tool calls mid-reasoning chain (no concurrent writers, no TTL expiration mid-flight on a local machine).

**Production upgrade path:** Replace `Cache.MEMORY` with `Cache.REDIS` in the aiocache config. No other code changes required. Redis adds persistence across restarts, cross-process cache sharing, and server-side TTL management.

---

## 6. De-identification Design (Detail)

### HIPAA Safe Harbor — 18 Identifiers

The pipeline removes or transforms all 18 Safe Harbor identifiers (45 CFR §164.514(b)):

1. Names → `[NAME_REDACTED]`
2. Geographic data smaller than state → `[GEO_REDACTED]`
3. Dates (except year) → year only, or relative offset
4. Phone numbers → `[PHONE_REDACTED]`
5. Fax numbers → `[FAX_REDACTED]`
6. Email addresses → `[EMAIL_REDACTED]`
7. SSNs → `[SSN_REDACTED]`
8. MRNs → consistent synthetic token (e.g., `MRN_4f2a`)
9. Health plan beneficiary numbers → `[PLAN_REDACTED]`
10. Account numbers → `[ACCT_REDACTED]`
11. Certificate/license numbers → `[LICENSE_REDACTED]`
12. Vehicle identifiers → `[VEHICLE_REDACTED]`
13. Device identifiers → `[DEVICE_REDACTED]`
14. URLs → `[URL_REDACTED]`
15. IP addresses → `[IP_REDACTED]`
16. Biometric identifiers → `[BIOMETRIC_REDACTED]`
17. Full-face photographs → N/A (not handling images)
18. Any other unique identifying numbers → `[ID_REDACTED]`

### Implementation approach

**Structured FHIR fields** — handled deterministically by FHIR resource path. The schema tells us exactly where names, dates, and identifiers live. No text scanning needed; fast and auditable.

**Free text** (clinical notes in DocumentReference, Observation value strings) — handled by Microsoft Presidio NER pipeline, augmented with custom recognizers for MRN patterns and Epic-specific ID formats.

**ID tokenization** — MRNs and patient IDs replaced with consistent synthetic tokens via HMAC-SHA256. Same patient gets the same token across all records; relational integrity preserved.

### Where de-identification runs

De-identification is not a storage step — it runs as a transform immediately before data is passed to the LLM:

```python
async def get_note_for_llm(document_id: str) -> dict:
    # 1. Fetch from cache (or live FHIR API on cache miss)
    raw = await fhir_cache.get(f"DocumentReference:{document_id}")
    if raw is None:
        raw = await fhir_client.fetch_document(document_id)
        await fhir_cache.set(f"DocumentReference:{document_id}", raw, ttl=3600)

    # 2. De-identify on the way out — raw cache is never modified
    return deidentification_pipeline.transform(raw)
```

Optionally cache the de-identified output under a separate key (`deid:DocumentReference:{id}`) to avoid re-running Presidio on repeated LLM calls for the same document.

```python
class DeidentificationPipeline:
    """
    Strips HIPAA Safe Harbor identifiers from FHIR resources
    before any data is passed to the LLM layer.

    Structured fields : deterministic by FHIR resource path
    Free text         : Microsoft Presidio NER + custom recognizers
    IDs               : consistent tokenization via HMAC-SHA256

    Reference: 45 CFR §164.514(b) — Safe Harbor method
    """
```

---

## 7. LLM Feature Design (Detail)

### Feature a — Clinical Note Summarization (pipeline)

Direct Ollama call. No LangChain.

```python
async def summarize_note(document_id: str) -> dict:
    # Check LLM output cache first
    cached = await llm_cache.get(f"llm:summary:{document_id}")
    if cached:
        return cached

    # De-identify, then call Ollama
    deid_text = await get_note_for_llm(document_id)
    prompt = build_summarization_prompt(deid_text)
    response = await ollama_client.complete(prompt)
    result = parse_structured_summary(response)

    # Cache the result — Ollama inference is slow
    await llm_cache.set(f"llm:summary:{document_id}", result, ttl=86400)
    return result
```

Output schema:
```json
{
  "chief_complaint": "...",
  "key_findings": ["...", "..."],
  "outstanding_items": ["...", "..."],
  "documentation_gaps": ["...", "..."]
}
```

### Feature b — Documentation Gap Narrative (pipeline)

Direct Ollama call. Accepts gap data already computed by the analytics layer — no additional FHIR fetching needed.

```python
async def generate_gap_narrative(encounter_id: str, gap_data: dict) -> str:
    cached = await llm_cache.get(f"llm:gap_narrative:{encounter_id}")
    if cached:
        return cached

    prompt = build_gap_narrative_prompt(gap_data)
    narrative = await ollama_client.complete(prompt)

    await llm_cache.set(f"llm:gap_narrative:{encounter_id}", narrative, ttl=86400)
    return narrative
```

Gap narrative pairs naturally with Feature c: the agent's `get_documentation_completeness` tool returns a gap list; Feature b turns that list into a plain-English narrative suitable for nursing staff.

### Feature c — Natural Language FHIR Query Agent (ReAct agent)

LangChain ReAct agent with exactly four tools. The agent decides which tools to call, reasons over results, and calls further tools as needed to answer the question.

**Tool definitions:**

```python
# tools.py — all tools operate against the in-memory cache
# Cache is pre-warmed on startup; tool calls are fast in-memory lookups

@tool
async def search_encounters(patient_id: str, date_range: tuple, 
                            encounter_type: str) -> list:
    """Returns de-identified encounter list with metadata."""
    encounters = await get_cached_or_fetch(f"encounters:patient:{patient_id}")
    return deidentify(filter_encounters(encounters, date_range, encounter_type))

@tool
async def get_documentation_completeness(encounter_id: str) -> dict:
    """Returns completeness score and gap list for one encounter."""
    observations = await get_cached_or_fetch(
        f"Observation:encounter:{encounter_id}")
    return compute_completeness_score(observations)

@tool
async def get_observation_summary(patient_id: str, category: str,
                                  date_range: tuple) -> dict:
    """Returns observation counts and categories."""
    observations = await get_cached_or_fetch(
        f"Observation:patient:{patient_id}")
    return summarize_observations(observations, category, date_range)

@tool
async def get_medication_reconciliation_status(encounter_id: str) -> dict:
    """Returns med rec completeness for one encounter."""
    med_requests = await get_cached_or_fetch(
        f"MedicationRequest:encounter:{encounter_id}")
    med_admin = await get_cached_or_fetch(
        f"MedicationAdministration:encounter:{encounter_id}")
    return compute_med_rec_status(med_requests, med_admin)
```

**System prompt:**

```
You are a clinical informatics assistant helping analyze
documentation patterns in de-identified patient data.

You have access to four tools for querying encounter and
documentation data. All data you receive has been
de-identified per HIPAA Safe Harbor before reaching you.

When answering questions:
- Be specific about what the data shows
- Flag when sample sizes are too small to draw conclusions
- Use clinical terminology accurately
- When you identify a documentation gap, explain its
  clinical significance
- Do not speculate about individual patients
```

**Why four tools and no more:** In a clinical system, constraining the agent's tool surface is a security and governance principle — you define exactly what data the AI is permitted to query. This is worth explaining explicitly in an interview. Any expansion of tool access would require deliberate review, not just adding a function.

**Model selection:** Start with `llama3` (8B) via Ollama. Sufficient for instruction-following and tool calling on a laptop. Upgrade to `mistral` or `llama3:70b` if reasoning quality is insufficient (requires more RAM). Document the tradeoff in the README.

---

## 8. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React + TypeScript | Demonstrable in browser, screenshots well, industry standard |
| UI Components | shadcn/ui + Tailwind | Clean, professional look without heavy design work |
| Charts | Recharts | Lightweight, composable, React-native |
| Backend | Python 3.11 + FastAPI | Best-in-class FHIR and LLM library ecosystem |
| FHIR Client | `fhirclient` (Python) | Official Python SMART on FHIR client from Harvard |
| FHIR Models | `fhir.resources` | Pydantic-based FHIR R4 resource models, type-safe |
| De-identification | Microsoft Presidio + custom rules | Production-grade NER-based PHI detection |
| Caching | `aiocache` (in-memory backend) | Async-native, TTL support, Redis-compatible interface for future upgrade |
| Analytics | Python + pandas | Sufficient for synthetic dataset; no database needed |
| LLM Orchestration | LangChain (agent only) | ReAct agent + tool calling; Features a/b use direct Ollama calls |
| Local LLM | Ollama (`llama3` / `mistral`) | No PHI leaves local environment |
| Auth | SMART on FHIR (OAuth 2.0) | Standard Epic-compatible auth; tokens in `app.state` only |
| Testing | pytest + HAPI sandbox | Unit tests + integration tests against public FHIR data |

**No database.** There is no SQLite, DuckDB, or other persistence layer. This is a deliberate decision appropriate to the use case (see Section 5). The production upgrade path — Redis for the cache layer — requires one config line change in `aiocache`.

---

## 9. Repository Structure

```
clindoc-insight/
├── README.md                        # Setup, architecture, compliance notes
├── COMPLIANCE.md                    # De-identification approach, HIPAA Safe Harbor ref
├── docker-compose.yml               # Spins up backend + optional local HAPI
│
├── backend/
│   ├── main.py                      # FastAPI app, routes, startup cache warm
│   ├── fhir/
│   │   ├── client.py                # FHIR R4 client, resource fetchers
│   │   ├── smart_auth.py            # SMART on FHIR OAuth 2.0 implementation
│   │   └── resources.py             # Typed fetch functions per resource type
│   ├── cache/
│   │   ├── fhir_cache.py            # aiocache config, TTL constants, key helpers
│   │   └── warmup.py                # Session startup pre-fetch logic
│   ├── deidentification/
│   │   ├── pipeline.py              # Main de-ID orchestrator
│   │   ├── structured.py            # FHIR field-path stripping
│   │   ├── freetext.py              # Presidio NER pipeline
│   │   └── tokenizer.py             # Consistent ID tokenization (HMAC-SHA256)
│   ├── analytics/
│   │   ├── completeness.py          # Documentation completeness scoring
│   │   ├── observations.py          # Observation density analysis
│   │   └── medications.py           # Medication reconciliation analysis
│   ├── llm/
│   │   ├── ollama_client.py         # Direct Ollama API wrapper
│   │   ├── summarizer.py            # Feature a: note summarization pipeline
│   │   └── gap_narrator.py          # Feature b: gap narrative pipeline
│   └── agent/
│       ├── agent.py                 # Feature c: LangChain ReAct agent
│       ├── tools.py                 # Four constrained FHIR query tools
│       └── prompts.py               # System prompt, few-shot examples
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.tsx        # Main metrics overview
│       │   ├── PatientExplorer.tsx  # Per-patient encounter drill-down
│       │   ├── NLQuery.tsx          # Feature c: NL query interface
│       │   └── NoteSummarizer.tsx   # Feature a: note summarization UI
│       └── components/
│           ├── CompletenessChart.tsx
│           ├── ObservationHeatmap.tsx
│           └── GapExplainer.tsx     # Feature b: gap narrative display
│
└── tests/
    ├── test_deidentification.py     # Verify PHI is stripped — specific pattern tests
    ├── test_cache.py                # Cache hit/miss, TTL expiration, key conventions
    ├── test_fhir_client.py          # Integration tests vs HAPI public server
    ├── test_analytics.py            # Completeness scoring, observation density
    └── test_agent_tools.py          # Tool output contracts, cache interaction
```

Note: `db/` directory removed. No SQLAlchemy, no database models, no migration tooling.

---

## 10. Build Phases & Timeline

### Phase 1 — Foundation
- [x] Project scaffold: FastAPI backend, React frontend, Ollama running locally
- [x] `aiocache` in-memory cache wired into FastAPI app state
- [x] HAPI public FHIR server connection — unauthenticated, fetch Patient + Encounter
- [x] Cache warm-up on startup — patients and encounters pre-fetched
- [x] Basic React shell with a data table showing fetched encounters
- [x] Confirm end-to-end data flow before building anything else

**Milestone:** Data flows HAPI → FastAPI → in-memory cache → React browser

### Phase 2 — FHIR Data Model & Analytics 
- [x] Implement all resource fetchers with cache-aside pattern: Observation, DocumentReference, MedicationRequest, MedicationAdministration, Condition
- [x] Analytics layer in Python/pandas: completeness scoring, observation density, med rec status
- [x] Wire analytics to frontend charts (Recharts)
- [x] Verify cache key conventions are consistent across all fetchers

**Milestone:** Dashboard showing real metrics computed over cached HAPI synthetic data

### Phase 3 — De-identification 
- [ ] Install and configure Microsoft Presidio
- [ ] Implement structured field stripping by FHIR resource path
- [ ] Implement free-text NER pipeline for clinical notes
- [ ] Implement consistent ID tokenization (HMAC-SHA256)
- [ ] Write unit tests verifying specific PHI patterns are stripped
- [ ] Wire de-identification into the LLM data path (`get_note_for_llm`, etc.)

**Milestone:** De-identification pipeline tested — PHI never reaches Ollama

### Phase 4 — LLM Features 
- [ ] Confirm Ollama running locally, test basic completions with `llama3`
- [ ] Feature a: note summarization pipeline (direct Ollama call, structured output)
- [ ] Feature b: gap narrative pipeline (direct Ollama call, paired with completeness output)
- [ ] Feature c: LangChain ReAct agent with four constrained tools
- [ ] Wire all three features to React UI
- [ ] LLM output caching via `aiocache` to avoid redundant Ollama calls

**Milestone:** All three LLM features working end-to-end against local Ollama

### Phase 5 — SMART on FHIR 
- [ ] Register app on fhir.epic.com developer portal
- [ ] Implement SMART standalone launch OAuth flow
- [ ] Handle token exchange and refresh; store in `app.state` only
- [ ] Test against Epic public sandbox with synthetic patients
- [ ] Document auth flow with sequence diagram in README

**Milestone:** Full SMART auth flow working against Epic sandbox

### Phase 6 — Polish 
- [ ] Screenshot/screen recording for portfolio
- [ ] Code cleanup, meaningful inline comments throughout


