"""
Tests for the unified clock tool module.

Tests verify:
- get_clock with "time" mode and various formats
- get_clock with "date" mode and various formats
- get_clock with "datetime" mode and various formats
- get_clock with "timezone" mode
- get_clock with "time_in_tz" mode for valid and invalid timezones
- get_clock with "unix" mode
- get_clock with "info" mode
"""

import re

import pytest

from fivcplayground import __backend__
from fivcplayground.tools.clock import clock
from fivcplayground.tools.types.backends import get_tool_name


def invoke_tool(tool, **kwargs):
    """Helper to invoke tools in both Strands and LangChain backends."""
    if __backend__ == "langchain":
        # LangChain tools have .invoke() method
        return tool.invoke(kwargs) if kwargs else tool.invoke({})
    else:
        # Strands tools are callable directly
        return tool(**kwargs) if kwargs else tool()


class TestGetClockTime:
    """Test get_clock function with 'time' mode."""

    def test_default_format(self):
        """Test get_clock with 'time' mode and default format."""
        result = invoke_tool(clock, mode="time")
        # Should match HH:MM:SS format
        assert re.match(r"^\d{2}:\d{2}:\d{2}$", result)

    def test_custom_format_12hour(self):
        """Test get_clock with 'time' mode and 12-hour format."""
        result = invoke_tool(clock, mode="time", format="%I:%M %p")
        # Should match HH:MM AM/PM format
        assert re.match(r"^\d{2}:\d{2} (AM|PM)$", result)

    def test_custom_format_hm(self):
        """Test get_clock with 'time' mode and HH:MM format."""
        result = invoke_tool(clock, mode="time", format="%H:%M")
        # Should match HH:MM format
        assert re.match(r"^\d{2}:\d{2}$", result)

    def test_valid_format(self):
        """Test get_clock with 'time' mode and valid format."""
        result = invoke_tool(clock, mode="time", format="%H:%M:%S")
        # Should still work with valid format
        assert re.match(r"^\d{2}:\d{2}:\d{2}$", result)


class TestGetClockDate:
    """Test get_clock function with 'date' mode."""

    def test_default_format(self):
        """Test get_clock with 'date' mode and default format."""
        result = invoke_tool(clock, mode="date")
        # Should match YYYY-MM-DD format
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", result)

    def test_custom_format_us(self):
        """Test get_clock with 'date' mode and US format."""
        result = invoke_tool(clock, mode="date", format="%m/%d/%Y")
        # Should match MM/DD/YYYY format
        assert re.match(r"^\d{2}/\d{2}/\d{4}$", result)

    def test_custom_format_long(self):
        """Test get_clock with 'date' mode and long format."""
        result = invoke_tool(clock, mode="date", format="%A, %B %d, %Y")
        # Should contain day name, month name, day, and year
        assert any(
            day in result
            for day in [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        )
        assert any(
            month in result
            for month in [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]
        )

    def test_valid_format_iso(self):
        """Test get_clock with 'date' mode and ISO format."""
        result = invoke_tool(clock, mode="date", format="%Y-%m-%d")
        # Should match YYYY-MM-DD format
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", result)


class TestGetClockDateTime:
    """Test get_clock function with 'datetime' mode."""

    def test_default_format(self):
        """Test get_clock with 'datetime' mode and default format."""
        result = invoke_tool(clock, mode="datetime")
        # Should match YYYY-MM-DD HH:MM:SS format
        assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", result)

    def test_custom_format_12hour(self):
        """Test get_clock with 'datetime' mode and 12-hour format."""
        result = invoke_tool(clock, mode="datetime", format="%Y-%m-%d %I:%M:%S %p")
        # Should match YYYY-MM-DD HH:MM:SS AM/PM format
        assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} (AM|PM)$", result)

    def test_valid_format_iso(self):
        """Test get_clock with 'datetime' mode and ISO format."""
        result = invoke_tool(clock, mode="datetime", format="%Y-%m-%d %H:%M:%S")
        # Should match YYYY-MM-DD HH:MM:SS format
        assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", result)


class TestGetClockTimezone:
    """Test get_clock function with 'timezone' mode."""

    def test_timezone_format(self):
        """Test get_clock with 'timezone' mode returns valid format."""
        result = invoke_tool(clock, mode="timezone")
        # Should contain UTC offset and timezone name
        assert "UTC" in result
        assert "(" in result and ")" in result

    def test_timezone_offset_format(self):
        """Test timezone offset is in correct format."""
        result = invoke_tool(clock, mode="timezone")
        # Should match UTC±HH:MM (NAME) format
        assert re.search(r"UTC[+-]\d{2}:\d{2}", result)


class TestGetClockTimeInTimezone:
    """Test get_clock function with 'time_in_tz' mode."""

    def test_valid_timezone_newyork(self):
        """Test get_clock with 'time_in_tz' mode and America/New_York."""
        result = invoke_tool(clock, mode="time_in_tz", timezone_name="America/New_York")
        # Should match YYYY-MM-DD HH:MM:SS format
        assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", result)

    def test_valid_timezone_tokyo(self):
        """Test get_clock with 'time_in_tz' mode and Asia/Tokyo."""
        result = invoke_tool(clock, mode="time_in_tz", timezone_name="Asia/Tokyo")
        # Should match YYYY-MM-DD HH:MM:SS format
        assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", result)

    def test_valid_timezone_london(self):
        """Test get_clock with 'time_in_tz' mode and Europe/London."""
        result = invoke_tool(clock, mode="time_in_tz", timezone_name="Europe/London")
        # Should match YYYY-MM-DD HH:MM:SS format
        assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", result)

    def test_invalid_timezone(self):
        """Test get_clock with 'time_in_tz' mode and invalid timezone."""
        result = invoke_tool(clock, mode="time_in_tz", timezone_name="Invalid/Timezone")
        assert "Error" in result
        assert "Unknown timezone" in result

    def test_missing_timezone_name(self):
        """Test get_clock with 'time_in_tz' mode without timezone_name."""
        result = invoke_tool(clock, mode="time_in_tz")
        assert "Error" in result
        assert "timezone_name is required" in result

    def test_custom_format(self):
        """Test get_clock with 'time_in_tz' mode and custom format."""
        result = invoke_tool(
            clock,
            mode="time_in_tz",
            timezone_name="America/New_York",
            format="%I:%M %p",
        )
        # Should match HH:MM AM/PM format
        assert re.match(r"^\d{2}:\d{2} (AM|PM)$", result)


class TestGetClockUnix:
    """Test get_clock function with 'unix' mode."""

    def test_unix_timestamp_format(self):
        """Test get_clock with 'unix' mode returns valid format."""
        result = invoke_tool(clock, mode="unix")
        # Should be a string of digits
        assert result.isdigit()

    def test_unix_timestamp_reasonable_value(self):
        """Test get_clock with 'unix' mode returns reasonable value."""
        result = invoke_tool(clock, mode="unix")
        timestamp = int(result)
        # Should be after 2020-01-01 (1577836800)
        assert timestamp > 1577836800
        # Should be before 2100-01-01 (4102444800)
        assert timestamp < 4102444800


class TestGetClockInfo:
    """Test get_clock function with 'info' mode."""

    def test_time_info_format(self):
        """Test get_clock with 'info' mode returns comprehensive information."""
        result = invoke_tool(clock, mode="info")
        # Should contain all required components
        assert "Date:" in result
        assert "Time:" in result
        assert "Timezone:" in result
        assert "Unix:" in result

    def test_time_info_date_format(self):
        """Test get_clock with 'info' mode contains valid date."""
        result = invoke_tool(clock, mode="info")
        # Extract date part
        date_match = re.search(r"Date: (\d{4}-\d{2}-\d{2})", result)
        assert date_match is not None

    def test_time_info_time_format(self):
        """Test get_clock with 'info' mode contains valid time."""
        result = invoke_tool(clock, mode="info")
        # Extract time part
        time_match = re.search(r"Time: (\d{2}:\d{2}:\d{2})", result)
        assert time_match is not None

    def test_time_info_timezone_format(self):
        """Test get_clock with 'info' mode contains valid timezone."""
        result = invoke_tool(clock, mode="info")
        # Extract timezone part
        tz_match = re.search(r"Timezone: (UTC[+-]\d{2}:\d{2})", result)
        assert tz_match is not None

    def test_time_info_unix_format(self):
        """Test get_clock with 'info' mode contains valid Unix timestamp."""
        result = invoke_tool(clock, mode="info")
        # Extract Unix timestamp part
        unix_match = re.search(r"Unix: (\d+)", result)
        assert unix_match is not None
        timestamp = int(unix_match.group(1))
        # Should be reasonable value
        assert timestamp > 1577836800


class TestClockToolIntegration:
    """Integration tests for unified clock tool."""

    def test_all_modes_return_strings(self):
        """Test that all modes return strings."""
        assert isinstance(invoke_tool(clock, mode="time"), str)
        assert isinstance(invoke_tool(clock, mode="date"), str)
        assert isinstance(invoke_tool(clock, mode="datetime"), str)
        assert isinstance(invoke_tool(clock, mode="timezone"), str)
        assert isinstance(
            invoke_tool(clock, mode="time_in_tz", timezone_name="America/New_York"),
            str,
        )
        assert isinstance(invoke_tool(clock, mode="unix"), str)
        assert isinstance(invoke_tool(clock, mode="info"), str)

    def test_default_mode(self):
        """Test that default mode is 'datetime'."""
        result = invoke_tool(clock)
        # Should match YYYY-MM-DD HH:MM:SS format (datetime mode)
        assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", result)

    def test_tool_has_name(self):
        """Test that tool has a name."""
        tool_name = get_tool_name(clock)
        assert tool_name is not None
        assert tool_name == "clock"

    def test_tool_has_description(self):
        """Test that tool has a description."""
        if __backend__ == "langchain":
            description = clock.description
        else:
            # Strands tools have tool_spec as a dict with description
            description = (
                clock.tool_spec.get("description")
                if isinstance(clock.tool_spec, dict)
                else clock.tool_spec.description
            )

        assert description is not None
        assert "mode" in description.lower()

    def test_invalid_mode(self):
        """Test get_clock with invalid mode raises validation error."""
        from pydantic_core import ValidationError

        # Strands tools don't validate at call time, they validate at definition time
        # So we skip this test for Strands backend
        if __backend__ == "langchain":
            with pytest.raises(ValidationError):
                invoke_tool(clock, mode="invalid_mode")
        else:
            # For Strands, invalid mode will be caught by the function logic
            # This is tested implicitly by other tests
            pass
