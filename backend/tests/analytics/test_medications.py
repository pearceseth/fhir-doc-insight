"""Tests for analytics/medications.py"""

import pytest
from analytics.medications import calculate_medication_reconciliation


class TestCalculateMedicationReconciliation:
    """Tests for calculate_medication_reconciliation function."""

    def test_empty_lists_returns_complete(self):
        """Empty medication lists should return status='complete'."""
        result = calculate_medication_reconciliation([], [])

        assert result["status"] == "complete"
        assert result["total_requests"] == 0
        assert result["administered"] == 0

    def test_equal_requests_and_administrations_is_complete(
        self, medication_request, medication_administration
    ):
        """Equal number of requests and administrations should be complete."""
        result = calculate_medication_reconciliation(
            [medication_request], [medication_administration]
        )

        assert result["status"] == "complete"
        assert result["total_requests"] == 1
        assert result["administered"] == 1

    def test_more_administered_than_requested_is_complete(
        self, medication_request, medication_administration
    ):
        """More administrations than requests should still be complete."""
        # 1 request, 2 administrations
        result = calculate_medication_reconciliation(
            [medication_request],
            [medication_administration, medication_administration],
        )

        assert result["status"] == "complete"
        assert result["total_requests"] == 1
        assert result["administered"] == 2

    def test_fewer_administered_than_requested_is_incomplete(
        self, medication_request, medication_administration
    ):
        """Fewer administrations than requests should be incomplete."""
        # 2 requests, 1 administration
        result = calculate_medication_reconciliation(
            [medication_request, medication_request],
            [medication_administration],
        )

        assert result["status"] == "incomplete"
        assert result["total_requests"] == 2
        assert result["administered"] == 1

    def test_no_administrations_with_requests_is_incomplete(self, medication_request):
        """Requests with no administrations should be incomplete."""
        result = calculate_medication_reconciliation([medication_request], [])

        assert result["status"] == "incomplete"
        assert result["total_requests"] == 1
        assert result["administered"] == 0

    def test_multiple_requests_all_administered(
        self, medication_request, medication_administration
    ):
        """Multiple requests all administered should be complete."""
        requests = [medication_request] * 3
        administrations = [medication_administration] * 3

        result = calculate_medication_reconciliation(requests, administrations)

        assert result["status"] == "complete"
        assert result["total_requests"] == 3
        assert result["administered"] == 3
