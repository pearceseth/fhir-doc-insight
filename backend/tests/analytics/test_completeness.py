"""Tests for analytics/completeness.py"""

import pytest
from analytics.completeness import calculate_completeness, REQUIRED_CATEGORIES


class TestCalculateCompleteness:
    """Tests for calculate_completeness function."""

    def test_empty_observations_returns_zero_score(self):
        """Empty observations should return score=0 with all categories missing."""
        result = calculate_completeness([])

        assert result["score"] == 0.0
        assert result["missing_categories"] == REQUIRED_CATEGORIES
        assert result["present_categories"] == []

    def test_all_categories_present_returns_full_score(
        self,
        observation_vital_signs,
        observation_laboratory,
        observation_survey,
        observation_procedure,
    ):
        """All 4 required categories present should return score=1.0."""
        observations = [
            observation_vital_signs,
            observation_laboratory,
            observation_survey,
            observation_procedure,
        ]

        result = calculate_completeness(observations)

        assert result["score"] == 1.0
        assert result["missing_categories"] == []
        assert set(result["present_categories"]) == set(REQUIRED_CATEGORIES)

    def test_one_category_present_returns_quarter_score(self, observation_vital_signs):
        """One category present should return score=0.25."""
        result = calculate_completeness([observation_vital_signs])

        assert result["score"] == 0.25
        assert "vital-signs" in result["present_categories"]
        assert "vital-signs" not in result["missing_categories"]
        assert len(result["missing_categories"]) == 3

    def test_two_categories_present_returns_half_score(
        self, observation_vital_signs, observation_laboratory
    ):
        """Two categories present should return score=0.5."""
        result = calculate_completeness([observation_vital_signs, observation_laboratory])

        assert result["score"] == 0.5
        assert set(result["present_categories"]) == {"vital-signs", "laboratory"}
        assert len(result["missing_categories"]) == 2

    def test_three_categories_present_returns_three_quarter_score(
        self, observation_vital_signs, observation_laboratory, observation_survey
    ):
        """Three categories present should return score=0.75."""
        result = calculate_completeness([
            observation_vital_signs,
            observation_laboratory,
            observation_survey,
        ])

        assert result["score"] == 0.75
        assert len(result["present_categories"]) == 3
        assert len(result["missing_categories"]) == 1

    def test_duplicate_categories_count_once(self, observation_vital_signs):
        """Multiple observations in same category should count the category once."""
        # Create a second vital signs observation
        second_vital = {
            "id": "obs-vitals-2",
            "category": [
                {"coding": [{"code": "vital-signs"}]}
            ],
        }

        result = calculate_completeness([observation_vital_signs, second_vital])

        assert result["score"] == 0.25
        assert result["present_categories"] == ["vital-signs"]

    def test_non_required_categories_ignored(self, observation_other):
        """Non-required categories should not affect the score."""
        result = calculate_completeness([observation_other])

        assert result["score"] == 0.0
        assert result["present_categories"] == []
        assert result["missing_categories"] == REQUIRED_CATEGORIES

    def test_mixed_required_and_non_required_categories(
        self, observation_vital_signs, observation_other
    ):
        """Mix of required and non-required categories counts only required."""
        result = calculate_completeness([observation_vital_signs, observation_other])

        assert result["score"] == 0.25
        assert result["present_categories"] == ["vital-signs"]

    def test_observation_missing_category_key(self):
        """Observation without category key should be handled gracefully."""
        observation = {"id": "obs-no-category", "code": {"coding": [{"code": "test"}]}}

        result = calculate_completeness([observation])

        assert result["score"] == 0.0
        assert result["present_categories"] == []

    def test_observation_empty_category_list(self):
        """Observation with empty category list should be handled gracefully."""
        observation = {"id": "obs-empty-category", "category": []}

        result = calculate_completeness([observation])

        assert result["score"] == 0.0

    def test_observation_missing_coding_key(self):
        """Observation with category but no coding should be handled gracefully."""
        observation = {"id": "obs-no-coding", "category": [{}]}

        result = calculate_completeness([observation])

        assert result["score"] == 0.0

    def test_observation_empty_coding_list(self):
        """Observation with empty coding list should be handled gracefully."""
        observation = {"id": "obs-empty-coding", "category": [{"coding": []}]}

        result = calculate_completeness([observation])

        assert result["score"] == 0.0

    def test_observation_coding_missing_code_key(self):
        """Observation with coding but no code key should be handled gracefully."""
        observation = {
            "id": "obs-no-code",
            "category": [{"coding": [{"system": "http://example.org"}]}],
        }

        result = calculate_completeness([observation])

        assert result["score"] == 0.0
