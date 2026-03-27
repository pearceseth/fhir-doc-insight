"""Main de-identification pipeline orchestrator."""

import copy
import logging
from typing import Any

from .freetext import deidentify_free_text
from .structured import strip_structured_fields
from .tokenizer import IDTokenizer

logger = logging.getLogger(__name__)


class DeidentificationPipeline:
    """
    Strips HIPAA Safe Harbor identifiers from FHIR resources
    before passing to LLM.

    - Structured fields: deterministic by FHIR path
    - Free text: Microsoft Presidio NER
    - IDs: consistent tokenization via HMAC-SHA256

    Usage:
        pipeline = DeidentificationPipeline()
        safe_resource = pipeline.transform(fhir_resource)
    """

    def __init__(self, secret_key: str | None = None, enable_freetext: bool = True):
        self.tokenizer = IDTokenizer(secret_key)
        self.enable_freetext = enable_freetext

    def transform(self, resource: dict) -> dict:
        """
        Transform a FHIR resource by removing/tokenizing PHI.
        Returns a new dict; original is not modified.
        """
        if not isinstance(resource, dict):
            return resource

        # Deep copy to avoid modifying original
        result = copy.deepcopy(resource)

        # Step 1: Strip structured PHI fields
        result = strip_structured_fields(result, self.tokenizer)

        # Step 2: De-identify free text (optional, can be slow)
        if self.enable_freetext:
            result = deidentify_free_text(result)

        # Step 3: Tokenize resource ID
        if "id" in result:
            result["id"] = self.tokenizer.tokenize(result["id"], prefix="RES")

        return result

    def transform_bundle(self, bundle: dict) -> dict:
        """Transform all resources in a FHIR Bundle."""
        if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
            return self.transform(bundle)

        result = copy.deepcopy(bundle)
        if "entry" in result:
            result["entry"] = [
                {**entry, "resource": self.transform(entry.get("resource", {}))}
                for entry in result["entry"]
                if isinstance(entry, dict)
            ]
        return result

    def transform_list(self, resources: list[dict]) -> list[dict]:
        """Transform a list of FHIR resources."""
        return [self.transform(r) for r in resources]

    def get_token_for_id(self, original_id: str, prefix: str = "RES") -> str:
        """Get the token that will be generated for a given ID."""
        return self.tokenizer.tokenize(original_id, prefix)

    def create_reverse_mapping(self, original_ids: list[str], prefix: str = "RES") -> dict[str, str]:
        """
        Create a mapping from tokens back to original IDs.
        Useful for resolving results back to actual resources.
        """
        return {
            self.tokenizer.tokenize(oid, prefix): oid
            for oid in original_ids
        }
