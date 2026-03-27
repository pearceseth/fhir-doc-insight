"""Structured FHIR field stripping for HIPAA Safe Harbor compliance."""

from typing import Any

from .tokenizer import IDTokenizer

# HIPAA Safe Harbor identifiers (18 categories) mapped to FHIR paths
# These are the common FHIR paths that may contain PHI
STRUCTURED_PHI_PATHS = {
    # Names
    "name",
    "patient.name",
    "subject.display",
    "participant.individual.display",
    "performer.display",
    "author.display",
    "recorder.display",
    "asserter.display",
    "requester.display",
    "informant.display",
    # Contact info
    "telecom",
    "address",
    "contact",
    # Identifiers (will be tokenized, not stripped)
    "identifier",
    # Dates (birth dates, death dates - keep clinical dates)
    "birthDate",
    "deceasedDateTime",
    # Geographic data (below state level)
    "address.line",
    "address.city",
    "address.district",
    "address.postalCode",
    # Device identifiers
    "device.identifier",
    # URLs and emails (within telecom)
    # Photos
    "photo",
    # SSN, MRN (within identifier)
    # Account numbers (within identifier)
}

# Fields to completely remove (no tokenization)
FIELDS_TO_REMOVE = {
    "name",
    "telecom",
    "address",
    "contact",
    "photo",
    "birthDate",
    "deceasedDateTime",
}

# Fields where we tokenize the value instead of removing
FIELDS_TO_TOKENIZE = {
    "identifier",
}


def strip_structured_fields(resource: dict, tokenizer: IDTokenizer) -> dict:
    """
    Strip or tokenize structured PHI fields from a FHIR resource.
    Returns a copy with sensitive fields redacted.
    """
    if not isinstance(resource, dict):
        return resource

    result = {}

    for key, value in resource.items():
        # Skip fields to completely remove
        if key in FIELDS_TO_REMOVE:
            continue

        # Tokenize identifier arrays
        if key in FIELDS_TO_TOKENIZE:
            result[key] = _process_identifiers(value, tokenizer)
            continue

        # Handle display names in references
        if key == "display" and _is_likely_name(value):
            result[key] = "[REDACTED]"
            continue

        # Recursively process nested structures
        if isinstance(value, dict):
            result[key] = strip_structured_fields(value, tokenizer)
        elif isinstance(value, list):
            result[key] = [
                strip_structured_fields(item, tokenizer) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def _process_identifiers(identifiers: Any, tokenizer: IDTokenizer) -> list[dict]:
    """Process identifier array, tokenizing values."""
    if not isinstance(identifiers, list):
        return []

    result = []
    for ident in identifiers:
        if not isinstance(ident, dict):
            continue
        processed = {
            "system": ident.get("system", ""),
            "value": tokenizer.tokenize(ident.get("value", ""), prefix="ID"),
        }
        if "type" in ident:
            processed["type"] = ident["type"]
        result.append(processed)

    return result


def _is_likely_name(value: Any) -> bool:
    """Heuristic to detect if a display string is likely a person's name."""
    if not isinstance(value, str):
        return False
    # Simple heuristic: contains comma or multiple capitalized words
    if "," in value:  # "LastName, FirstName" format
        return True
    words = value.split()
    if len(words) >= 2 and all(w[0].isupper() for w in words if w):
        # Could be a name or a clinical term, err on the side of caution
        # Check for common clinical terms
        clinical_terms = {"blood", "heart", "vital", "sign", "rate", "pressure", "lab"}
        if any(term in value.lower() for term in clinical_terms):
            return False
        return True
    return False
