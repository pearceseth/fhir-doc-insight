"""Free-text de-identification using Microsoft Presidio NER."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy load Presidio to avoid import overhead when not used
_analyzer = None
_anonymizer = None


def _get_analyzer():
    """Lazy-load the Presidio analyzer."""
    global _analyzer
    if _analyzer is None:
        try:
            from presidio_analyzer import AnalyzerEngine

            _analyzer = AnalyzerEngine()
        except ImportError:
            logger.warning("presidio-analyzer not installed, free-text de-ID disabled")
            return None
    return _analyzer


def _get_anonymizer():
    """Lazy-load the Presidio anonymizer."""
    global _anonymizer
    if _anonymizer is None:
        try:
            from presidio_anonymizer import AnonymizerEngine

            _anonymizer = AnonymizerEngine()
        except ImportError:
            logger.warning("presidio-anonymizer not installed, free-text de-ID disabled")
            return None
    return _anonymizer


# FHIR paths that contain free-text clinical notes
FREE_TEXT_PATHS = {
    "text.div",
    "note",
    "content.attachment.data",
    "description",
    "comment",
    "interpretation.text",
    "valueString",
}


def deidentify_free_text(resource: dict) -> dict:
    """
    De-identify free-text fields in a FHIR resource using Presidio NER.
    Returns a copy with PHI in text fields redacted.
    """
    if not isinstance(resource, dict):
        return resource

    result = {}

    for key, value in resource.items():
        if key in FREE_TEXT_PATHS or (key == "div" and "text" in resource):
            result[key] = _anonymize_text(value)
        elif key == "note" and isinstance(value, list):
            result[key] = [_process_note(n) for n in value]
        elif key == "content" and isinstance(value, list):
            result[key] = [_process_content(c) for c in value]
        elif isinstance(value, dict):
            result[key] = deidentify_free_text(value)
        elif isinstance(value, list):
            result[key] = [
                deidentify_free_text(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def _anonymize_text(text: Any) -> str:
    """Run Presidio analysis and anonymization on text."""
    if not isinstance(text, str) or not text.strip():
        return text if isinstance(text, str) else ""

    analyzer = _get_analyzer()
    anonymizer = _get_anonymizer()

    if analyzer is None or anonymizer is None:
        # Presidio not available, return text as-is with warning
        return text

    try:
        # Detect PHI entities
        results = analyzer.analyze(
            text=text,
            language="en",
            entities=[
                "PERSON",
                "PHONE_NUMBER",
                "EMAIL_ADDRESS",
                "DATE_TIME",
                "LOCATION",
                "US_SSN",
                "US_DRIVER_LICENSE",
                "CREDIT_CARD",
                "IP_ADDRESS",
                "MEDICAL_LICENSE",
                "US_PASSPORT",
                "US_BANK_NUMBER",
            ],
        )

        if not results:
            return text

        # Anonymize detected entities
        anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
        return anonymized.text

    except Exception as e:
        logger.error(f"Presidio anonymization failed: {e}")
        return text


def _process_note(note: Any) -> dict:
    """Process a FHIR Annotation (note) element."""
    if not isinstance(note, dict):
        return note
    result = dict(note)
    if "text" in result:
        result["text"] = _anonymize_text(result["text"])
    if "authorString" in result:
        result["authorString"] = "[REDACTED]"
    return result


def _process_content(content: Any) -> dict:
    """Process a DocumentReference content element."""
    if not isinstance(content, dict):
        return content
    result = dict(content)
    if "attachment" in result and isinstance(result["attachment"], dict):
        attachment = dict(result["attachment"])
        if "data" in attachment:
            # Base64-encoded content, decode and anonymize if text
            attachment["data"] = "[REDACTED-CONTENT]"
        if "title" in attachment:
            attachment["title"] = _anonymize_text(attachment["title"])
        result["attachment"] = attachment
    return result
