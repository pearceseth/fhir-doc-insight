"""Shared test fixtures for FHIR data."""

import pytest


@pytest.fixture
def observation_vital_signs() -> dict:
    """Sample vital signs observation."""
    return {
        "id": "obs-vitals-1",
        "category": [
            {
                "coding": [
                    {"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}
                ]
            }
        ],
        "code": {"coding": [{"code": "8867-4", "display": "Heart rate"}]},
        "valueQuantity": {"value": 72, "unit": "beats/minute"},
    }


@pytest.fixture
def observation_laboratory() -> dict:
    """Sample laboratory observation."""
    return {
        "id": "obs-lab-1",
        "category": [
            {
                "coding": [
                    {"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}
                ]
            }
        ],
        "code": {"coding": [{"code": "2093-3", "display": "Total Cholesterol"}]},
        "valueQuantity": {"value": 180, "unit": "mg/dL"},
    }


@pytest.fixture
def observation_survey() -> dict:
    """Sample survey observation."""
    return {
        "id": "obs-survey-1",
        "category": [
            {
                "coding": [
                    {"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "survey"}
                ]
            }
        ],
        "code": {"coding": [{"code": "72166-2", "display": "Tobacco smoking status"}]},
        "valueCodeableConcept": {"coding": [{"code": "266919005", "display": "Never smoker"}]},
    }


@pytest.fixture
def observation_procedure() -> dict:
    """Sample procedure observation."""
    return {
        "id": "obs-proc-1",
        "category": [
            {
                "coding": [
                    {"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "procedure"}
                ]
            }
        ],
        "code": {"coding": [{"code": "procedure-1", "display": "Procedure result"}]},
    }


@pytest.fixture
def observation_other() -> dict:
    """Sample observation with non-required category."""
    return {
        "id": "obs-other-1",
        "category": [
            {
                "coding": [
                    {"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "imaging"}
                ]
            }
        ],
        "code": {"coding": [{"code": "imaging-1", "display": "X-ray result"}]},
    }


@pytest.fixture
def encounter_ambulatory() -> dict:
    """Sample ambulatory encounter."""
    return {
        "id": "enc-amb-1",
        "status": "finished",
        "class": {"code": "AMB", "display": "ambulatory"},
        "period": {"start": "2024-01-15T09:00:00Z", "end": "2024-01-15T10:00:00Z"},
    }


@pytest.fixture
def encounter_emergency() -> dict:
    """Sample emergency encounter."""
    return {
        "id": "enc-emer-1",
        "status": "finished",
        "class": {"code": "EMER", "display": "emergency"},
        "period": {"start": "2024-01-20T14:30:00Z", "end": "2024-01-20T18:45:00Z"},
    }


@pytest.fixture
def encounter_inpatient() -> dict:
    """Sample inpatient encounter."""
    return {
        "id": "enc-inp-1",
        "status": "in-progress",
        "class": {"code": "IMP", "display": "inpatient"},
        "period": {"start": "2024-01-25T08:00:00Z"},
    }


@pytest.fixture
def medication_request() -> dict:
    """Sample medication request."""
    return {
        "id": "med-req-1",
        "status": "active",
        "medicationCodeableConcept": {"coding": [{"code": "1049502", "display": "Acetaminophen 325 MG"}]},
    }


@pytest.fixture
def medication_administration() -> dict:
    """Sample medication administration."""
    return {
        "id": "med-admin-1",
        "status": "completed",
        "medicationCodeableConcept": {"coding": [{"code": "1049502", "display": "Acetaminophen 325 MG"}]},
    }
