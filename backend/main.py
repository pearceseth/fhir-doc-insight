import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from cache.fhir_cache import (
    cache,
    patient_key,
    patient_encounters_key,
    all_patients_key,
    observation_encounter_key,
    document_reference_encounter_key,
    medication_request_encounter_key,
    medication_administration_encounter_key,
    condition_patient_key,
)
from fhir_client.client import fhir_client
from analytics.completeness import calculate_completeness
from analytics.observations import calculate_observation_density
from analytics.medications import calculate_medication_reconciliation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await fhir_client.close()


app = FastAPI(title="ClinDoc Insight API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/patients")
async def list_patients():
    patients = await cache.get(all_patients_key())
    if patients is None:
        # Fetch from FHIR and cache
        fetched = await fhir_client.fetch_patients()
        patients = [p.model_dump(mode="json", exclude_none=True) for p in fetched]
        await cache.set(all_patients_key(), patients)
        for p in patients:
            await cache.set(patient_key(p["id"]), p)
    return {"patients": patients, "count": len(patients)}


@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    patient = await cache.get(patient_key(patient_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.get("/api/patients/{patient_id}/encounters")
async def get_patient_encounters(patient_id: str):
    encounters = await cache.get(patient_encounters_key(patient_id))
    if encounters is None:
        return {"encounters": [], "count": 0}
    return {"encounters": encounters, "count": len(encounters)}


@app.get("/api/encounters")
async def list_all_encounters(
    page: int = 1,
    page_size: int = 20,
    missing_diagnosis: bool = False,
    missing_participant: bool = False,
    missing_reason: bool = False,
    missing_type: bool = False,
    missing_class: bool = False,
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    offset = (page - 1) * page_size
    encounters, total = await fhir_client.fetch_encounters_paginated(
        count=page_size,
        offset=offset,
        missing_diagnosis=missing_diagnosis,
        missing_participant=missing_participant,
        missing_reason=missing_reason,
        missing_type=missing_type,
        missing_class=missing_class,
    )

    encounter_list = []
    for enc in encounters:
        enc_dict = enc.model_dump(mode="json", exclude_none=True)
        enc_dict["_patient_name"] = enc.subject.display if enc.subject and enc.subject.display else "Unknown"
        encounter_list.append(enc_dict)

    return {
        "encounters": encounter_list,
        "count": len(encounter_list),
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": (total + page_size - 1) // page_size if total else None,
    }


@app.get("/api/encounters/{encounter_id}/observations")
async def get_encounter_observations(encounter_id: str):
    observations = await cache.get(observation_encounter_key(encounter_id))
    if observations is None:
        fetched = await fhir_client.fetch_observations_for_encounter(encounter_id)
        observations = [o.model_dump(mode="json", exclude_none=True) for o in fetched]
        await cache.set(observation_encounter_key(encounter_id), observations)
    return {"observations": observations, "count": len(observations)}


@app.get("/api/encounters/{encounter_id}/document-references")
async def get_encounter_document_references(encounter_id: str):
    doc_refs = await cache.get(document_reference_encounter_key(encounter_id))
    if doc_refs is None:
        fetched = await fhir_client.fetch_document_references_for_encounter(encounter_id)
        doc_refs = [d.model_dump(mode="json", exclude_none=True) for d in fetched]
        await cache.set(document_reference_encounter_key(encounter_id), doc_refs)
    return {"documentReferences": doc_refs, "count": len(doc_refs)}


@app.get("/api/encounters/{encounter_id}/medication-requests")
async def get_encounter_medication_requests(encounter_id: str):
    med_requests = await cache.get(medication_request_encounter_key(encounter_id))
    if med_requests is None:
        fetched = await fhir_client.fetch_medication_requests_for_encounter(encounter_id)
        med_requests = [m.model_dump(mode="json", exclude_none=True) for m in fetched]
        await cache.set(medication_request_encounter_key(encounter_id), med_requests)
    return {"medicationRequests": med_requests, "count": len(med_requests)}


@app.get("/api/encounters/{encounter_id}/medication-administrations")
async def get_encounter_medication_administrations(encounter_id: str):
    med_admins = await cache.get(medication_administration_encounter_key(encounter_id))
    if med_admins is None:
        fetched = await fhir_client.fetch_medication_administrations_for_encounter(encounter_id)
        med_admins = [m.model_dump(mode="json", exclude_none=True) for m in fetched]
        await cache.set(medication_administration_encounter_key(encounter_id), med_admins)
    return {"medicationAdministrations": med_admins, "count": len(med_admins)}


# Limit concurrent FHIR requests (increase for production with private FHIR server)
_fhir_semaphore = asyncio.Semaphore(2)


@app.get("/api/encounters/{encounter_id}/details")
async def get_encounter_details(encounter_id: str):
    """Fetch all encounter details in one request with rate-limit-friendly pacing."""

    async def get_or_fetch(cache_key, fetcher, serializer):
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached
        async with _fhir_semaphore:
            # Double-check cache after acquiring semaphore
            cached = await cache.get(cache_key)
            if cached is not None:
                return cached
            fetched = await fetcher()
            result = [serializer(item) for item in fetched]
            await cache.set(cache_key, result)
            return result

    observations, document_references, medication_requests, medication_administrations = await asyncio.gather(
        get_or_fetch(
            observation_encounter_key(encounter_id),
            lambda: fhir_client.fetch_observations_for_encounter(encounter_id),
            lambda o: o.model_dump(mode="json", exclude_none=True),
        ),
        get_or_fetch(
            document_reference_encounter_key(encounter_id),
            lambda: fhir_client.fetch_document_references_for_encounter(encounter_id),
            lambda d: d.model_dump(mode="json", exclude_none=True),
        ),
        get_or_fetch(
            medication_request_encounter_key(encounter_id),
            lambda: fhir_client.fetch_medication_requests_for_encounter(encounter_id),
            lambda m: m.model_dump(mode="json", exclude_none=True),
        ),
        get_or_fetch(
            medication_administration_encounter_key(encounter_id),
            lambda: fhir_client.fetch_medication_administrations_for_encounter(encounter_id),
            lambda m: m.model_dump(mode="json", exclude_none=True),
        ),
    )

    return {
        "observations": observations,
        "documentReferences": document_references,
        "medicationRequests": medication_requests,
        "medicationAdministrations": medication_administrations,
    }


@app.get("/api/patients/{patient_id}/conditions")
async def get_patient_conditions(patient_id: str):
    conditions = await cache.get(condition_patient_key(patient_id))
    if conditions is None:
        return {"conditions": [], "count": 0}
    return {"conditions": conditions, "count": len(conditions)}


@app.get("/api/analytics/documentation-completeness")
async def get_documentation_completeness():
    """Calculate documentation completeness scores for all encounters."""
    patients = await cache.get(all_patients_key()) or []
    results = []

    for patient in patients:
        patient_id = patient.get("id")
        encounters = await cache.get(patient_encounters_key(patient_id)) or []

        for encounter in encounters:
            encounter_id = encounter.get("id")
            observations = await cache.get(observation_encounter_key(encounter_id)) or []
            score = calculate_completeness(observations)

            enc_class = encounter.get("class", {})
            encounter_type = enc_class.get("code", "unknown") if isinstance(enc_class, dict) else "unknown"

            results.append(
                {
                    "encounterId": encounter_id,
                    "encounterType": encounter_type,
                    "patientId": patient_id,
                    **score,
                }
            )

    return {"completeness": results, "count": len(results)}


@app.get("/api/analytics/observation-density")
async def get_observation_density():
    """Calculate observation density grouped by encounter type."""
    patients = await cache.get(all_patients_key()) or []
    all_encounters = []
    observations_by_encounter: dict[str, list[dict]] = {}

    for patient in patients:
        patient_id = patient.get("id")
        encounters = await cache.get(patient_encounters_key(patient_id)) or []
        all_encounters.extend(encounters)

        for encounter in encounters:
            encounter_id = encounter.get("id")
            observations = await cache.get(observation_encounter_key(encounter_id)) or []
            observations_by_encounter[encounter_id] = observations

    density = calculate_observation_density(all_encounters, observations_by_encounter)
    return {"density": density, "count": len(density)}


@app.get("/api/analytics/medication-reconciliation")
async def get_medication_reconciliation():
    """Calculate medication reconciliation status for all encounters."""
    patients = await cache.get(all_patients_key()) or []
    results = []

    for patient in patients:
        patient_id = patient.get("id")
        encounters = await cache.get(patient_encounters_key(patient_id)) or []

        for encounter in encounters:
            encounter_id = encounter.get("id")
            med_requests = (
                await cache.get(medication_request_encounter_key(encounter_id)) or []
            )
            med_admins = (
                await cache.get(medication_administration_encounter_key(encounter_id)) or []
            )
            reconciliation = calculate_medication_reconciliation(med_requests, med_admins)

            enc_class = encounter.get("class", {})
            encounter_type = enc_class.get("code", "unknown") if isinstance(enc_class, dict) else "unknown"

            results.append(
                {
                    "encounterId": encounter_id,
                    "encounterType": encounter_type,
                    "patientId": patient_id,
                    **reconciliation,
                }
            )

    return {"reconciliation": results, "count": len(results)}
