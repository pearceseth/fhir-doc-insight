from aiocache import Cache
from aiocache.serializers import JsonSerializer

from config import settings

cache = Cache(Cache.MEMORY, serializer=JsonSerializer(), ttl=settings.fhir_cache_ttl)


def patient_key(patient_id: str) -> str:
    return f"Patient:{patient_id}"


def encounter_key(encounter_id: str) -> str:
    return f"Encounter:{encounter_id}"


def patient_encounters_key(patient_id: str) -> str:
    return f"encounters:patient:{patient_id}"


def all_patients_key() -> str:
    return "patients:all"


def observation_encounter_key(encounter_id: str) -> str:
    return f"Observation:encounter:{encounter_id}"


def document_reference_encounter_key(encounter_id: str) -> str:
    return f"DocumentReference:encounter:{encounter_id}"


def medication_request_encounter_key(encounter_id: str) -> str:
    return f"MedicationRequest:encounter:{encounter_id}"


def medication_administration_encounter_key(encounter_id: str) -> str:
    return f"MedicationAdministration:encounter:{encounter_id}"


def condition_patient_key(patient_id: str) -> str:
    return f"Condition:patient:{patient_id}"
