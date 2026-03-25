import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from cache.fhir_cache import (
    cache,
    patient_key,
    patient_encounters_key,
    all_patients_key,
)
from cache.warmup import warm_cache
from fhir_client.client import fhir_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await warm_cache()
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
        return {"patients": [], "count": 0}
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
async def list_all_encounters():
    patients = await cache.get(all_patients_key()) or []

    def get_patient_name(patient: dict) -> str:
        names = patient.get("name", [])
        if names:
            name = names[0]
            given = " ".join(name.get("given", []))
            family = name.get("family", "")
            return f"{given} {family}".strip()
        return "Unknown"

    patient_name_map = {p.get("id"): get_patient_name(p) for p in patients}

    all_encounters = []
    for patient in patients:
        patient_id = patient.get("id")
        encounters = await cache.get(patient_encounters_key(patient_id)) or []
        for encounter in encounters:
            encounter["_patient_name"] = patient_name_map.get(patient_id, "Unknown")
            all_encounters.append(encounter)

    return {"encounters": all_encounters, "count": len(all_encounters)}
