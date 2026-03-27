"""FHIR query tools for the LangChain agent."""

import logging
from datetime import date, timedelta
from typing import Any

from langchain_core.tools import tool

from cache.fhir_cache import (
    cache,
    all_patients_key,
    patient_encounters_key,
    observation_encounter_key,
    document_reference_encounter_key,
    medication_request_encounter_key,
    medication_administration_encounter_key,
)
from fhir_client.client import fhir_client
from analytics.completeness import calculate_completeness
from analytics.medications import calculate_medication_reconciliation
from deidentification import DeidentificationPipeline

logger = logging.getLogger(__name__)

# Shared de-identification pipeline
_deid_pipeline = DeidentificationPipeline(enable_freetext=False)


async def _ensure_patients_loaded() -> list[dict]:
    """Ensure patients are loaded into cache, fetch if not."""
    patients = await cache.get(all_patients_key())
    if patients is None:
        logger.info("Fetching patients from FHIR server...")
        fetched = await fhir_client.fetch_patients()
        patients = [p.model_dump(mode="json", exclude_none=True) for p in fetched]
        await cache.set(all_patients_key(), patients)
    return patients


async def _ensure_encounters_loaded(patient_id: str) -> list[dict]:
    """Ensure encounters for a patient are loaded, fetch if not."""
    encounters = await cache.get(patient_encounters_key(patient_id))
    if encounters is None:
        logger.info(f"Fetching encounters for patient {patient_id}...")
        fetched = await fhir_client.fetch_encounters_for_patient(patient_id)
        encounters = [e.model_dump(mode="json", exclude_none=True) for e in fetched]
        await cache.set(patient_encounters_key(patient_id), encounters)
    return encounters


async def _ensure_observations_loaded(encounter_id: str) -> list[dict]:
    """Ensure observations for an encounter are loaded, fetch if not."""
    observations = await cache.get(observation_encounter_key(encounter_id))
    if observations is None:
        logger.info(f"Fetching observations for encounter {encounter_id}...")
        fetched = await fhir_client.fetch_observations_for_encounter(encounter_id)
        observations = [o.model_dump(mode="json", exclude_none=True) for o in fetched]
        await cache.set(observation_encounter_key(encounter_id), observations)
    return observations


async def _ensure_documents_loaded(encounter_id: str) -> list[dict]:
    """Ensure document references for an encounter are loaded, fetch if not."""
    docs = await cache.get(document_reference_encounter_key(encounter_id))
    if docs is None:
        logger.info(f"Fetching documents for encounter {encounter_id}...")
        fetched = await fhir_client.fetch_document_references_for_encounter(encounter_id)
        docs = [d.model_dump(mode="json", exclude_none=True) for d in fetched]
        await cache.set(document_reference_encounter_key(encounter_id), docs)
    return docs


async def _ensure_medications_loaded(encounter_id: str) -> tuple[list[dict], list[dict]]:
    """Ensure medication data for an encounter is loaded, fetch if not."""
    med_requests = await cache.get(medication_request_encounter_key(encounter_id))
    if med_requests is None:
        logger.info(f"Fetching medication requests for encounter {encounter_id}...")
        fetched = await fhir_client.fetch_medication_requests_for_encounter(encounter_id)
        med_requests = [m.model_dump(mode="json", exclude_none=True) for m in fetched]
        await cache.set(medication_request_encounter_key(encounter_id), med_requests)

    med_admins = await cache.get(medication_administration_encounter_key(encounter_id))
    if med_admins is None:
        logger.info(f"Fetching medication administrations for encounter {encounter_id}...")
        fetched = await fhir_client.fetch_medication_administrations_for_encounter(encounter_id)
        med_admins = [m.model_dump(mode="json", exclude_none=True) for m in fetched]
        await cache.set(medication_administration_encounter_key(encounter_id), med_admins)

    return med_requests, med_admins


MAX_DATE_RANGE_DAYS = 7


def _parse_date_range(date_from: str | None, date_to: str | None) -> tuple[date | None, date | None, str | None]:
    """
    Parse date strings into date objects. Handles relative dates.
    Returns (from_date, to_date, error_message).
    Defaults to last week if no range specified.
    Returns error if range exceeds MAX_DATE_RANGE_DAYS.
    """
    parsed_from = None
    parsed_to = None

    if date_from:
        if date_from == "last_week":
            parsed_from = date.today() - timedelta(days=7)
        elif date_from == "last_month":
            parsed_from = date.today() - timedelta(days=30)
        else:
            try:
                parsed_from = date.fromisoformat(date_from)
            except ValueError:
                pass

    if date_to:
        if date_to == "today":
            parsed_to = date.today()
        else:
            try:
                parsed_to = date.fromisoformat(date_to)
            except ValueError:
                pass

    # Default to last week if no date range specified
    if parsed_from is None and parsed_to is None:
        parsed_from = date.today() - timedelta(days=7)
        parsed_to = date.today()

    # Default end date to today if only start specified
    if parsed_from is not None and parsed_to is None:
        parsed_to = date.today()

    # Default start date to 7 days before end if only end specified
    if parsed_to is not None and parsed_from is None:
        parsed_from = parsed_to - timedelta(days=7)

    # Check if range exceeds limit
    if parsed_from and parsed_to:
        range_days = (parsed_to - parsed_from).days
        if range_days > MAX_DATE_RANGE_DAYS:
            return None, None, f"Date range of {range_days} days exceeds the maximum of {MAX_DATE_RANGE_DAYS} days. Please narrow your search to a week or less."

    return parsed_from, parsed_to, None


def _extract_encounter_date(encounter: dict) -> date | None:
    """Extract date from encounter period."""
    period = encounter.get("period", {})
    start = period.get("start")
    if start:
        try:
            return date.fromisoformat(start[:10])
        except ValueError:
            pass
    return None


def _get_encounter_class(encounter: dict) -> str:
    """Extract encounter class code."""
    enc_class = encounter.get("class", {})
    if isinstance(enc_class, dict):
        return enc_class.get("code", "unknown")
    return "unknown"


@tool
async def search_encounters(
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    encounter_type: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Search for encounters with optional filters. Limited to 7 days max.

    Args:
        status: Filter by status (e.g., "finished", "in-progress", "planned")
        date_from: Start date (YYYY-MM-DD) or "last_week". Defaults to 7 days ago.
        date_to: End date (YYYY-MM-DD) or "today". Defaults to today.
        encounter_type: Filter by encounter class (e.g., "AMB", "IMP", "EMER")
        limit: Maximum number of encounters to return (default 50)

    Returns:
        Dictionary with encounters list and count. Error if date range > 7 days.
    """
    # Parse and validate date range (max 7 days)
    parsed_from, parsed_to, error = _parse_date_range(date_from, date_to)
    if error:
        return {
            "error": error,
            "encounters": [],
            "count": 0,
        }

    # Ensure patients are loaded, fetch if needed
    patients = await _ensure_patients_loaded()
    all_encounters = []

    for patient in patients:
        patient_id = patient.get("id")
        encounters = await _ensure_encounters_loaded(patient_id)
        all_encounters.extend(encounters)

    # Apply filters
    filtered = []
    for enc in all_encounters:
        # Status filter
        if status and enc.get("status") != status:
            continue

        # Date range filter
        enc_date = _extract_encounter_date(enc)
        if enc_date:
            if parsed_from and enc_date < parsed_from:
                continue
            if parsed_to and enc_date > parsed_to:
                continue

        # Encounter type filter
        if encounter_type:
            enc_class = _get_encounter_class(enc)
            if enc_class.upper() != encounter_type.upper():
                continue

        filtered.append(enc)

    # Apply limit
    filtered = filtered[:limit]

    # Return encounter summaries (no PHI, keep real IDs for subsequent tool calls)
    encounter_summaries = []
    for enc in filtered:
        enc_class = _get_encounter_class(enc)
        enc_date = _extract_encounter_date(enc)
        encounter_summaries.append({
            "id": enc.get("id"),
            "status": enc.get("status"),
            "class": enc_class,
            "date": enc_date.isoformat() if enc_date else None,
        })

    return {
        "encounters": encounter_summaries,
        "count": len(encounter_summaries),
        "date_range": {
            "from": parsed_from.isoformat() if parsed_from else None,
            "to": parsed_to.isoformat() if parsed_to else None,
        },
        "filters_applied": {
            "status": status,
            "encounter_type": encounter_type,
        },
    }


@tool
async def get_documentation_completeness(encounter_id: str) -> dict[str, Any]:
    """
    Get documentation completeness score and gaps for an encounter.

    Args:
        encounter_id: The encounter ID to check (required, from search_encounters results)

    Returns:
        Dictionary with score (0-1), missing categories, and present categories
    """
    if not encounter_id or not encounter_id.strip():
        return {"error": "encounter_id is required. Use search_encounters first to get encounter IDs."}

    observations = await _ensure_observations_loaded(encounter_id)
    doc_refs = await _ensure_documents_loaded(encounter_id)

    completeness = calculate_completeness(observations)

    return {
        "encounter_id": encounter_id,
        "score": completeness["score"],
        "missing_categories": completeness["missing_categories"],
        "present_categories": completeness["present_categories"],
        "has_clinical_notes": len(doc_refs) > 0,
        "clinical_note_count": len(doc_refs),
        "observation_count": len(observations),
    }


@tool
async def get_observation_summary(
    encounter_id: str,
    category: str | None = None,
) -> dict[str, Any]:
    """
    Get observation counts by category for an encounter.

    Args:
        encounter_id: The encounter ID to check (required, from search_encounters results)
        category: Optional category to filter by (e.g., "vital-signs", "laboratory")

    Returns:
        Dictionary with observation counts by category
    """
    if not encounter_id or not encounter_id.strip():
        return {"error": "encounter_id is required. Use search_encounters first to get encounter IDs."}

    observations = await _ensure_observations_loaded(encounter_id)

    # Count by category
    category_counts: dict[str, int] = {}
    for obs in observations:
        categories = obs.get("category", [])
        for cat in categories:
            codings = cat.get("coding", [])
            for coding in codings:
                code = coding.get("code", "other")
                category_counts[code] = category_counts.get(code, 0) + 1

    # Filter by category if specified
    if category:
        category_counts = {k: v for k, v in category_counts.items() if k == category}

    return {
        "encounter_id": encounter_id,
        "total_observations": len(observations),
        "by_category": category_counts,
        "filter_category": category,
    }


@tool
async def get_medication_reconciliation_status(encounter_id: str) -> dict[str, Any]:
    """
    Get medication reconciliation status for an encounter.

    Args:
        encounter_id: The encounter ID to check (required, from search_encounters results)

    Returns:
        Dictionary with total requests, administered count, and reconciliation status
    """
    if not encounter_id or not encounter_id.strip():
        return {"error": "encounter_id is required. Use search_encounters first to get encounter IDs."}

    med_requests, med_admins = await _ensure_medications_loaded(encounter_id)

    reconciliation = calculate_medication_reconciliation(med_requests, med_admins)

    return {
        "encounter_id": encounter_id,
        "total_requests": reconciliation["total_requests"],
        "administered": reconciliation["administered"],
        "status": reconciliation["status"],
        "unreconciled_count": max(0, reconciliation["total_requests"] - reconciliation["administered"]),
    }


@tool
async def get_documentation_statistics(
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """
    Get aggregate documentation statistics across encounters. Use this for questions like
    "What percentage of encounters have clinical notes?" or "How many encounters have complete documentation?"

    Args:
        status: Filter by encounter status (e.g., "finished", "in-progress")
        date_from: Start date (YYYY-MM-DD). Defaults to 7 days ago.
        date_to: End date (YYYY-MM-DD). Defaults to today.

    Returns:
        Dictionary with counts and percentages for documentation completeness
    """
    # Parse and validate date range
    parsed_from, parsed_to, error = _parse_date_range(date_from, date_to)
    if error:
        return {"error": error}

    # Get encounters
    patients = await _ensure_patients_loaded()
    all_encounters = []

    for patient in patients:
        patient_id = patient.get("id")
        encounters = await _ensure_encounters_loaded(patient_id)
        all_encounters.extend(encounters)

    # Filter encounters
    filtered = []
    for enc in all_encounters:
        if status and enc.get("status") != status:
            continue
        enc_date = _extract_encounter_date(enc)
        if enc_date:
            if parsed_from and enc_date < parsed_from:
                continue
            if parsed_to and enc_date > parsed_to:
                continue
        filtered.append(enc)

    if not filtered:
        return {
            "total_encounters": 0,
            "message": "No encounters found matching the criteria",
            "date_range": {
                "from": parsed_from.isoformat() if parsed_from else None,
                "to": parsed_to.isoformat() if parsed_to else None,
            },
        }

    # Calculate statistics
    total = len(filtered)
    with_notes = 0
    with_vitals = 0
    with_labs = 0
    complete_docs = 0  # Has all required categories

    for enc in filtered:
        enc_id = enc.get("id")
        if not enc_id:
            continue

        # Check for clinical notes
        docs = await _ensure_documents_loaded(enc_id)
        if docs:
            with_notes += 1

        # Check observations
        observations = await _ensure_observations_loaded(enc_id)
        completeness = calculate_completeness(observations)

        if "vital-signs" in completeness["present_categories"]:
            with_vitals += 1
        if "laboratory" in completeness["present_categories"]:
            with_labs += 1
        if completeness["score"] == 1.0:
            complete_docs += 1

    return {
        "total_encounters": total,
        "with_clinical_notes": with_notes,
        "with_clinical_notes_pct": round(with_notes / total * 100, 1) if total else 0,
        "with_vital_signs": with_vitals,
        "with_vital_signs_pct": round(with_vitals / total * 100, 1) if total else 0,
        "with_laboratory": with_labs,
        "with_laboratory_pct": round(with_labs / total * 100, 1) if total else 0,
        "complete_documentation": complete_docs,
        "complete_documentation_pct": round(complete_docs / total * 100, 1) if total else 0,
        "date_range": {
            "from": parsed_from.isoformat() if parsed_from else None,
            "to": parsed_to.isoformat() if parsed_to else None,
        },
        "status_filter": status,
    }


def get_all_tools() -> list:
    """Get all available tools for the agent."""
    return [
        search_encounters,
        get_documentation_completeness,
        get_observation_summary,
        get_medication_reconciliation_status,
        get_documentation_statistics,
    ]
