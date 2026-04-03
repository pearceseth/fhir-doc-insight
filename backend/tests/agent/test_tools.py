"""Tests for agent/tools.py helper functions.

Mocks for heavy dependencies (langchain, llm, etc.) are set up in conftest.py.
"""

import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from freezegun import freeze_time

# Import the actual tools module after mocks are set up by conftest.py
# We use importlib to load it fresh with our mocks in place
_tools_path = Path(__file__).parent.parent.parent / "agent" / "tools.py"
_spec = importlib.util.spec_from_file_location("agent.tools_test", _tools_path)
_agent_tools = importlib.util.module_from_spec(_spec)
sys.modules["agent.tools_test"] = _agent_tools
_spec.loader.exec_module(_agent_tools)

_parse_date_range = _agent_tools._parse_date_range
_extract_encounter_date = _agent_tools._extract_encounter_date
_get_encounter_class = _agent_tools._get_encounter_class
MAX_DATE_RANGE_DAYS = _agent_tools.MAX_DATE_RANGE_DAYS


class TestParseDateRange:
    """Tests for _parse_date_range function."""

    @freeze_time("2024-01-15")
    def test_no_dates_defaults_to_last_week(self):
        """No dates should default to last 7 days."""
        from_date, to_date, error = _parse_date_range(None, None)

        assert error is None
        assert from_date == date(2024, 1, 8)
        assert to_date == date(2024, 1, 15)

    @freeze_time("2024-01-15")
    def test_today_keyword_for_from(self):
        """'today' keyword should return today's date."""
        from_date, to_date, error = _parse_date_range("today", None)

        assert error is None
        assert from_date == date(2024, 1, 15)
        assert to_date == date(2024, 1, 15)

    @freeze_time("2024-01-15")
    def test_today_keyword_for_to(self):
        """'today' keyword for date_to should return today's date."""
        from_date, to_date, error = _parse_date_range("2024-01-10", "today")

        assert error is None
        assert from_date == date(2024, 1, 10)
        assert to_date == date(2024, 1, 15)

    @freeze_time("2024-01-15")
    def test_last_week_keyword(self):
        """'last_week' keyword should return 7 days ago."""
        from_date, to_date, error = _parse_date_range("last_week", None)

        assert error is None
        assert from_date == date(2024, 1, 8)
        assert to_date == date(2024, 1, 15)

    @freeze_time("2024-01-15")
    def test_last_month_keyword(self):
        """'last_month' keyword should return 30 days ago."""
        from_date, to_date, error = _parse_date_range("last_month", None)

        assert error is None
        assert from_date == date(2023, 12, 16)
        assert to_date == date(2024, 1, 15)

    def test_iso_date_format(self):
        """ISO date format (YYYY-MM-DD) should be parsed."""
        from_date, to_date, error = _parse_date_range("2024-01-01", "2024-01-07")

        assert error is None
        assert from_date == date(2024, 1, 1)
        assert to_date == date(2024, 1, 7)

    def test_us_date_format(self):
        """US date format (MM/DD/YYYY) should be parsed."""
        from_date, to_date, error = _parse_date_range("01/01/2024", "01/07/2024")

        assert error is None
        assert from_date == date(2024, 1, 1)
        assert to_date == date(2024, 1, 7)

    @freeze_time("2024-01-15")
    def test_only_from_date_defaults_to_today(self):
        """Only specifying from_date should default to_date to today."""
        from_date, to_date, error = _parse_date_range("2024-01-10", None)

        assert error is None
        assert from_date == date(2024, 1, 10)
        assert to_date == date(2024, 1, 15)

    @freeze_time("2024-01-15")
    def test_only_to_date_defaults_from_7_days_before(self):
        """Only specifying to_date should default from_date to 7 days before."""
        from_date, to_date, error = _parse_date_range(None, "2024-01-15")

        assert error is None
        assert from_date == date(2024, 1, 8)
        assert to_date == date(2024, 1, 15)

    def test_range_exceeds_max_returns_error(self):
        """Date range exceeding MAX_DATE_RANGE_DAYS should return error."""
        # Create a range of 101 days (exceeds 100)
        from_date, to_date, error = _parse_date_range("2024-01-01", "2024-04-15")

        assert error is not None
        assert f"exceeds the maximum of {MAX_DATE_RANGE_DAYS}" in error
        assert from_date is None
        assert to_date is None

    def test_invalid_from_date_format_returns_error(self):
        """Invalid from_date format should return error."""
        from_date, to_date, error = _parse_date_range("invalid-date", "2024-01-07")

        assert error is not None
        assert "Invalid date_from format" in error
        assert from_date is None
        assert to_date is None

    def test_invalid_to_date_format_returns_error(self):
        """Invalid to_date format should return error."""
        from_date, to_date, error = _parse_date_range("2024-01-01", "not-a-date")

        assert error is not None
        assert "Invalid date_to format" in error
        assert from_date is None
        assert to_date is None

    def test_exact_max_range_is_allowed(self):
        """Exactly MAX_DATE_RANGE_DAYS should be allowed."""
        start = date(2024, 1, 1)
        end = start + timedelta(days=MAX_DATE_RANGE_DAYS)
        from_date, to_date, error = _parse_date_range(
            start.isoformat(), end.isoformat()
        )

        assert error is None
        assert from_date == start
        assert to_date == end

    @freeze_time("2024-01-15")
    def test_various_date_formats_accepted(self):
        """Various common date formats should be accepted."""
        test_formats = [
            ("2024-01-10", date(2024, 1, 10)),
            ("01/10/2024", date(2024, 1, 10)),
            ("Jan 10, 2024", date(2024, 1, 10)),
            ("2024/01/10", date(2024, 1, 10)),
        ]

        for date_str, expected in test_formats:
            from_date, to_date, error = _parse_date_range(date_str, None)
            assert error is None, f"Failed for format: {date_str}"
            assert from_date == expected, f"Failed for format: {date_str}"


class TestExtractEncounterDate:
    """Tests for _extract_encounter_date function."""

    def test_extracts_date_from_period_start(self):
        """Should extract date from period.start."""
        encounter = {"period": {"start": "2024-01-15T09:00:00Z"}}

        result = _extract_encounter_date(encounter)

        assert result == date(2024, 1, 15)

    def test_handles_date_only_format(self):
        """Should handle date-only format in period.start."""
        encounter = {"period": {"start": "2024-01-15"}}

        result = _extract_encounter_date(encounter)

        assert result == date(2024, 1, 15)

    def test_returns_none_for_missing_period(self):
        """Should return None when period is missing."""
        encounter = {"status": "finished"}

        result = _extract_encounter_date(encounter)

        assert result is None

    def test_returns_none_for_missing_start(self):
        """Should return None when period.start is missing."""
        encounter = {"period": {"end": "2024-01-15T10:00:00Z"}}

        result = _extract_encounter_date(encounter)

        assert result is None

    def test_returns_none_for_empty_period(self):
        """Should return None when period is empty dict."""
        encounter = {"period": {}}

        result = _extract_encounter_date(encounter)

        assert result is None

    def test_returns_none_for_invalid_date_format(self):
        """Should return None for invalid date format."""
        encounter = {"period": {"start": "invalid-date"}}

        result = _extract_encounter_date(encounter)

        assert result is None

    def test_returns_none_for_empty_start_string(self):
        """Should return None for empty start string."""
        encounter = {"period": {"start": ""}}

        result = _extract_encounter_date(encounter)

        assert result is None


class TestGetEncounterClass:
    """Tests for _get_encounter_class function."""

    def test_returns_class_code(self, encounter_ambulatory):
        """Should return class code from encounter."""
        result = _get_encounter_class(encounter_ambulatory)
        assert result == "AMB"

    def test_returns_unknown_for_missing_class(self):
        """Should return 'unknown' when class is missing."""
        encounter = {"id": "enc-1", "status": "finished"}

        result = _get_encounter_class(encounter)

        assert result == "unknown"

    def test_returns_unknown_for_empty_class_dict(self):
        """Should return 'unknown' when class is empty dict."""
        encounter = {"id": "enc-1", "class": {}}

        result = _get_encounter_class(encounter)

        assert result == "unknown"

    def test_returns_unknown_for_non_dict_class(self):
        """Should return 'unknown' when class is not a dict."""
        encounter = {"id": "enc-1", "class": "AMB"}

        result = _get_encounter_class(encounter)

        assert result == "unknown"

    def test_returns_unknown_for_missing_code_key(self):
        """Should return 'unknown' when code key is missing."""
        encounter = {"id": "enc-1", "class": {"display": "ambulatory"}}

        result = _get_encounter_class(encounter)

        assert result == "unknown"
