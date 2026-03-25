import logging

from fhir_client.client import fhir_client
from cache.fhir_cache import (
    cache,
    patient_key,
    encounter_key,
    patient_encounters_key,
    all_patients_key,
)

logger = logging.getLogger(__name__)


async def warm_cache() -> None:
    logger.info("Starting cache warm-up...")

    patients = await fhir_client.fetch_patients()
    logger.info(f"Fetched {len(patients)} patients from FHIR server")

    patient_list = []
    for patient in patients:
        patient_data = patient.model_dump(mode="json", exclude_none=True)
        patient_id = patient.id

        await cache.set(patient_key(patient_id), patient_data)
        patient_list.append(patient_data)

        try:
            encounters = await fhir_client.fetch_encounters_for_patient(patient_id)
            encounter_list = []
            for encounter in encounters:
                encounter_data = encounter.model_dump(mode="json", exclude_none=True)
                await cache.set(encounter_key(encounter.id), encounter_data)
                encounter_list.append(encounter_data)

            await cache.set(patient_encounters_key(patient_id), encounter_list)
            logger.info(f"Cached {len(encounters)} encounters for patient {patient_id}")
        except Exception as e:
            logger.warning(f"Failed to fetch encounters for patient {patient_id}: {e}")

    await cache.set(all_patients_key(), patient_list)
    logger.info("Cache warm-up complete")
