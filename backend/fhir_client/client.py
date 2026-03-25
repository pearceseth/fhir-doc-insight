import httpx
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.encounter import Encounter
from fhir.resources.R4B.bundle import Bundle

from config import settings


class FHIRClient:
    def __init__(self):
        self.base_url = settings.fhir_base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_patients(self, count: int | None = None) -> list[Patient]:
        count = count or settings.patient_fetch_count
        response = await self.client.get(
            f"{self.base_url}/Patient",
            params={"_count": count},
            headers={"Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        bundle = Bundle.model_validate(response.json())
        patients = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource:
                    patients.append(Patient.model_validate(entry.resource.model_dump()))
        return patients

    async def fetch_patient(self, patient_id: str) -> Patient:
        response = await self.client.get(
            f"{self.base_url}/Patient/{patient_id}",
            headers={"Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        return Patient.model_validate(response.json())

    async def fetch_encounters_for_patient(self, patient_id: str) -> list[Encounter]:
        response = await self.client.get(
            f"{self.base_url}/Encounter",
            params={"subject": f"Patient/{patient_id}"},
            headers={"Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        bundle = Bundle.model_validate(response.json())
        encounters = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource:
                    encounters.append(Encounter.model_validate(entry.resource.model_dump()))
        return encounters

    async def close(self):
        await self.client.aclose()


fhir_client = FHIRClient()
