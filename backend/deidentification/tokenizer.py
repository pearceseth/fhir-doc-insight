"""Consistent ID tokenization using HMAC-SHA256."""

import hashlib
import hmac
import os
from functools import lru_cache


class IDTokenizer:
    """
    Generates consistent pseudonymized tokens for identifiers.
    Uses HMAC-SHA256 for deterministic but non-reversible tokenization.
    """

    def __init__(self, secret_key: str | None = None):
        self._secret_key = (secret_key or os.environ.get("DEID_SECRET_KEY", "default-dev-key")).encode()

    def tokenize(self, identifier: str, prefix: str = "TOK") -> str:
        """
        Generate a consistent token for an identifier.
        Same identifier always produces the same token within a session.
        """
        if not identifier:
            return ""
        digest = hmac.new(self._secret_key, identifier.encode(), hashlib.sha256).hexdigest()[:12]
        return f"{prefix}-{digest.upper()}"

    @lru_cache(maxsize=10000)
    def tokenize_cached(self, identifier: str, prefix: str = "TOK") -> str:
        """Cached version for repeated lookups."""
        return self.tokenize(identifier, prefix)
