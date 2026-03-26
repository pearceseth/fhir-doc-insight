import httpx
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.encounter import Encounter
from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.documentreference import DocumentReference
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.medicationadministration import MedicationAdministration
from fhir.resources.R4B.condition import Condition

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
            params={"subject": f"Patient/{patient_id}", "_sort": "-date"},
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

    def _normalize_datetime(self, dt_str: str | None) -> str | None:
        """Normalize FHIR datetime to valid format (milliseconds max, not microseconds)."""
        if not dt_str:
            return dt_str
        from dateutil import parser
        from datetime import timezone

        try:
            dt = parser.isoparse(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            # FHIR allows max 3 decimal places (milliseconds), not 6 (microseconds)
            # Also requires colon in timezone offset (+08:00 not +0800)
            tz_offset = dt.strftime("%z")
            if tz_offset:
                tz_offset = tz_offset[:3] + ":" + tz_offset[3:]  # +0800 -> +08:00
            return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}" + tz_offset
        except ValueError:
            return dt_str

    def _normalize_encounter(self, resource: dict) -> dict:
        """Normalize encounter data to pass FHIR validation."""
        # Add default status if missing (required field)
        if "status" not in resource or resource["status"] is None:
            resource["status"] = "unknown"
        # Add default class if missing (required field)
        if "class" not in resource:
            resource["class"] = {"code": "unknown", "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode"}

        # Normalize datetime fields in period
        if "period" in resource:
            if "start" in resource["period"]:
                resource["period"]["start"] = self._normalize_datetime(resource["period"]["start"])
            if "end" in resource["period"]:
                resource["period"]["end"] = self._normalize_datetime(resource["period"]["end"])

        return resource

    def _normalize_observation(self, resource: dict) -> dict:
        """Normalize observation data to pass FHIR validation."""
        if "effectiveDateTime" in resource:
            resource["effectiveDateTime"] = self._normalize_datetime(resource["effectiveDateTime"])
        return resource

    async def fetch_encounters_paginated(
        self,
        count: int = 20,
        offset: int = 0,
        missing_diagnosis: bool = False,
        missing_participant: bool = False,
        missing_reason: bool = False,
        missing_type: bool = False,
        missing_class: bool = False,
    ) -> tuple[list[Encounter], int | None]:
        """Fetch encounters with pagination. Returns (encounters, total)."""
        params = {"_sort": "-date", "_count": count}
        if offset > 0:
            params["_offset"] = offset
        if missing_diagnosis:
            params["diagnosis:missing"] = "true"
        if missing_participant:
            params["participant:missing"] = "true"
        if missing_reason:
            params["reason-code:missing"] = "true"
        if missing_type:
            params["type:missing"] = "true"
        if missing_class:
            params["class:missing"] = "true"

        response = await self.client.get(
            f"{self.base_url}/Encounter",
            params=params,
            headers={"Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        data = response.json()

        encounters = []
        for entry in data.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Encounter":
                normalized = self._normalize_encounter(resource)
                encounters.append(Encounter.model_validate(normalized))

        return encounters, data.get("total")

    async def fetch_observations_for_encounter(self, encounter_id: str) -> list[Observation]:
        response = await self.client.get(
            f"{self.base_url}/Observation",
            params={"encounter": f"Encounter/{encounter_id}"},
            headers={"Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        data = response.json()
        observations = []
        for entry in data.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Observation":
                normalized = self._normalize_observation(resource)
                observations.append(Observation.model_validate(normalized))
        return observations

    async def fetch_document_references_for_encounter(
        self, encounter_id: str
    ) -> list[DocumentReference]:
        response = await self.client.get(
            f"{self.base_url}/DocumentReference",
            params={"encounter": f"Encounter/{encounter_id}"},
            headers={"Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        bundle = Bundle.model_validate(response.json())
        doc_refs = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource:
                    doc_refs.append(DocumentReference.model_validate(entry.resource.model_dump()))
        return doc_refs

    async def fetch_medication_requests_for_encounter(
        self, encounter_id: str
    ) -> list[MedicationRequest]:
        response = await self.client.get(
            f"{self.base_url}/MedicationRequest",
            params={"encounter": f"Encounter/{encounter_id}"},
            headers={"Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        bundle = Bundle.model_validate(response.json())
        med_requests = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource:
                    med_requests.append(
                        MedicationRequest.model_validate(entry.resource.model_dump())
                    )
        return med_requests

    async def fetch_medication_administrations_for_encounter(
        self, encounter_id: str
    ) -> list[MedicationAdministration]:
        response = await self.client.get(
            f"{self.base_url}/MedicationAdministration",
            params={"context": f"Encounter/{encounter_id}"},
            headers={"Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        bundle = Bundle.model_validate(response.json())
        med_admins = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource:
                    med_admins.append(
                        MedicationAdministration.model_validate(entry.resource.model_dump())
                    )
        return med_admins

    async def fetch_conditions_for_patient(self, patient_id: str) -> list[Condition]:
        response = await self.client.get(
            f"{self.base_url}/Condition",
            params={"subject": f"Patient/{patient_id}"},
            headers={"Accept": "application/fhir+json"},
        )
        response.raise_for_status()
        bundle = Bundle.model_validate(response.json())
        conditions = []
        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource:
                    conditions.append(Condition.model_validate(entry.resource.model_dump()))
        return conditions

    async def close(self):
        await self.client.aclose()


fhir_client = FHIRClient()
