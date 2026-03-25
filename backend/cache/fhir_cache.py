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
