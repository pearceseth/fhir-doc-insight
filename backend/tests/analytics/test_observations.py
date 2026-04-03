"""Tests for analytics/observations.py"""

import pytest
from analytics.observations import get_observation_category, calculate_observation_density


class TestGetObservationCategory:
    """Tests for get_observation_category function."""

    def test_returns_vital_signs(self, observation_vital_signs):
        """Should return 'vital-signs' for vital signs observation."""
        result = get_observation_category(observation_vital_signs)
        assert result == "vital-signs"

    def test_returns_laboratory(self, observation_laboratory):
        """Should return 'laboratory' for laboratory observation."""
        result = get_observation_category(observation_laboratory)
        assert result == "laboratory"

    def test_returns_survey(self, observation_survey):
        """Should return 'survey' for survey observation."""
        result = get_observation_category(observation_survey)
        assert result == "survey"

    def test_returns_procedure(self, observation_procedure):
        """Should return 'procedure' for procedure observation."""
        result = get_observation_category(observation_procedure)
        assert result == "procedure"

    def test_returns_other_for_unknown_category(self, observation_other):
        """Should return 'other' for non-standard category."""
        result = get_observation_category(observation_other)
        assert result == "other"

    def test_returns_other_for_missing_category(self):
        """Should return 'other' when category key is missing."""
        observation = {"id": "obs-1", "code": {"coding": [{"code": "test"}]}}
        result = get_observation_category(observation)
        assert result == "other"

    def test_returns_other_for_empty_category_list(self):
        """Should return 'other' when category list is empty."""
        observation = {"id": "obs-1", "category": []}
        result = get_observation_category(observation)
        assert result == "other"

    def test_returns_other_for_missing_coding(self):
        """Should return 'other' when coding key is missing."""
        observation = {"id": "obs-1", "category": [{}]}
        result = get_observation_category(observation)
        assert result == "other"

    def test_returns_other_for_empty_coding_list(self):
        """Should return 'other' when coding list is empty."""
        observation = {"id": "obs-1", "category": [{"coding": []}]}
        result = get_observation_category(observation)
        assert result == "other"

    def test_returns_other_for_missing_code_key(self):
        """Should return 'other' when code key is missing in coding."""
        observation = {"id": "obs-1", "category": [{"coding": [{"system": "test"}]}]}
        result = get_observation_category(observation)
        assert result == "other"


class TestCalculateObservationDensity:
    """Tests for calculate_observation_density function."""

    def test_empty_encounters_returns_empty_list(self):
        """Empty encounters list should return empty result."""
        result = calculate_observation_density([], {})
        assert result == []

    def test_single_encounter_no_observations(self, encounter_ambulatory):
        """Single encounter with no observations should return zeroes."""
        result = calculate_observation_density([encounter_ambulatory], {})

        assert len(result) == 1
        assert result[0]["encounter_type"] == "AMB"
        assert result[0]["total"] == 0
        assert result[0]["counts"]["vital_signs"] == 0

    def test_single_encounter_with_observations(
        self,
        encounter_ambulatory,
        observation_vital_signs,
        observation_laboratory,
    ):
        """Single encounter with observations should count categories."""
        observations_by_encounter = {
            "enc-amb-1": [observation_vital_signs, observation_laboratory]
        }

        result = calculate_observation_density([encounter_ambulatory], observations_by_encounter)

        assert len(result) == 1
        assert result[0]["encounter_type"] == "AMB"
        assert result[0]["total"] == 2
        assert result[0]["counts"]["vital_signs"] == 1
        assert result[0]["counts"]["laboratory"] == 1

    def test_multiple_encounters_same_type_aggregates(
        self,
        observation_vital_signs,
    ):
        """Multiple encounters of same type should aggregate counts."""
        enc1 = {"id": "enc-1", "class": {"code": "AMB"}}
        enc2 = {"id": "enc-2", "class": {"code": "AMB"}}
        observations_by_encounter = {
            "enc-1": [observation_vital_signs],
            "enc-2": [observation_vital_signs],
        }

        result = calculate_observation_density([enc1, enc2], observations_by_encounter)

        assert len(result) == 1
        assert result[0]["encounter_type"] == "AMB"
        assert result[0]["counts"]["vital_signs"] == 2
        assert result[0]["total"] == 2

    def test_multiple_encounter_types(
        self,
        encounter_ambulatory,
        encounter_emergency,
        observation_vital_signs,
        observation_laboratory,
    ):
        """Different encounter types should be grouped separately."""
        observations_by_encounter = {
            "enc-amb-1": [observation_vital_signs],
            "enc-emer-1": [observation_laboratory],
        }

        result = calculate_observation_density(
            [encounter_ambulatory, encounter_emergency], observations_by_encounter
        )

        assert len(result) == 2
        types = {r["encounter_type"]: r for r in result}

        assert "AMB" in types
        assert "EMER" in types
        assert types["AMB"]["counts"]["vital_signs"] == 1
        assert types["EMER"]["counts"]["laboratory"] == 1

    def test_encounter_missing_class_uses_unknown(self, observation_vital_signs):
        """Encounter without class should use 'unknown' type."""
        encounter = {"id": "enc-1", "status": "finished"}
        observations_by_encounter = {"enc-1": [observation_vital_signs]}

        result = calculate_observation_density([encounter], observations_by_encounter)

        assert len(result) == 1
        assert result[0]["encounter_type"] == "unknown"

    def test_encounter_with_non_dict_class_uses_unknown(self, observation_vital_signs):
        """Encounter with non-dict class should use 'unknown' type."""
        encounter = {"id": "enc-1", "class": "AMB"}  # string instead of dict
        observations_by_encounter = {"enc-1": [observation_vital_signs]}

        result = calculate_observation_density([encounter], observations_by_encounter)

        assert len(result) == 1
        assert result[0]["encounter_type"] == "unknown"

    def test_encounter_missing_id_skips_observations(self, observation_vital_signs):
        """Encounter without id should not match any observations."""
        encounter = {"status": "finished", "class": {"code": "AMB"}}
        observations_by_encounter = {"enc-1": [observation_vital_signs]}

        result = calculate_observation_density([encounter], observations_by_encounter)

        assert len(result) == 1
        assert result[0]["total"] == 0

    def test_other_category_counted(self, encounter_ambulatory, observation_other):
        """Non-standard categories should be counted as 'other'."""
        observations_by_encounter = {"enc-amb-1": [observation_other]}

        result = calculate_observation_density([encounter_ambulatory], observations_by_encounter)

        assert result[0]["counts"]["other"] == 1
        assert result[0]["total"] == 1

    def test_all_categories_counted(
        self,
        encounter_ambulatory,
        observation_vital_signs,
        observation_laboratory,
        observation_survey,
        observation_procedure,
        observation_other,
    ):
        """All observation categories should be counted correctly."""
        observations_by_encounter = {
            "enc-amb-1": [
                observation_vital_signs,
                observation_laboratory,
                observation_survey,
                observation_procedure,
                observation_other,
            ]
        }

        result = calculate_observation_density([encounter_ambulatory], observations_by_encounter)

        counts = result[0]["counts"]
        assert counts["vital_signs"] == 1
        assert counts["laboratory"] == 1
        assert counts["survey"] == 1
        assert counts["procedure"] == 1
        assert counts["other"] == 1
        assert result[0]["total"] == 5
