"""
Clock tool implementation for Strands framework.

This module provides a clock/time tool using the Strands framework, implementing
the ITool interface for integration with the FivcPlayground component architecture.

The clock tool supports multiple modes:
    - "time": Get current time in specified format
    - "date": Get current date in specified format
    - "datetime": Get current date and time
    - "timezone": Get current timezone information
    - "time_in_tz": Get time in specific timezone
    - "unix": Get Unix timestamp
    - "info": Get comprehensive time information
"""

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones
from typing import Literal, Any

from strands.tools import tool as make_tool
from strands.types.tools import ToolResult
from uuid import uuid4

from fivcplayground.interfaces import ITool

logger = logging.getLogger(__name__)


@make_tool
def _clock_impl(
    mode: Literal[
        "time", "date", "datetime", "timezone", "time_in_tz", "unix", "info"
    ] = "datetime",
    format: str = "",
    timezone_name: str = "",
) -> ToolResult:
    """
    Get current time and date information in various formats.

    Args:
        mode: Operation mode (default: "datetime")
            - "time": Get current time (format: "%H:%M:%S")
            - "date": Get current date (format: "%Y-%m-%d")
            - "datetime": Get current date and time (format: "%Y-%m-%d %H:%M:%S")
            - "timezone": Get current timezone information
            - "time_in_tz": Get time in specific timezone (requires timezone_name)
            - "unix": Get Unix timestamp
            - "info": Get comprehensive time information

        format: Custom format string using strftime syntax
        timezone_name: Timezone name for "time_in_tz" mode

    Returns:
        ToolResult with formatted time/date string or error message
    """
    try:
        if mode == "time":
            fmt = format or "%H:%M:%S"
            result = datetime.now().strftime(fmt)
        elif mode == "date":
            fmt = format or "%Y-%m-%d"
            result = datetime.now().strftime(fmt)
        elif mode == "datetime":
            fmt = format or "%Y-%m-%d %H:%M:%S"
            result = datetime.now().strftime(fmt)
        elif mode == "timezone":
            now = datetime.now(timezone.utc).astimezone()
            tz_name = now.tzname()
            tz_offset = now.strftime("%z")
            if len(tz_offset) >= 5:
                tz_offset = f"{tz_offset[:-2]}:{tz_offset[-2:]}"
            result = f"UTC{tz_offset} ({tz_name})"
        elif mode == "time_in_tz":
            if not timezone_name:
                return ToolResult(
                    content=[
                        {
                            "type": "text",
                            "text": "Error: timezone_name is required for 'time_in_tz' mode",
                        }
                    ],
                    status="error",
                    toolUseId=str(uuid4()),
                )
            if timezone_name not in available_timezones():
                available = ", ".join(sorted(list(available_timezones())[:10]))
                return ToolResult(
                    content=[
                        {
                            "type": "text",
                            "text": f"Error: Unknown timezone '{timezone_name}'. Available timezones include: {available}...",
                        }
                    ],
                    status="error",
                    toolUseId=str(uuid4()),
                )
            tz = ZoneInfo(timezone_name)
            fmt = format or "%Y-%m-%d %H:%M:%S"
            result = datetime.now(tz).strftime(fmt)
        elif mode == "unix":
            timestamp = int(datetime.now().timestamp())
            result = str(timestamp)
        elif mode == "info":
            now = datetime.now(timezone.utc).astimezone()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            tz_name = now.tzname()
            tz_offset = now.strftime("%z")
            if len(tz_offset) >= 5:
                tz_offset = f"{tz_offset[:-2]}:{tz_offset[-2:]}"
            unix_timestamp = int(datetime.now().timestamp())
            result = (
                f"Date: {date_str}, Time: {time_str}, "
                f"Timezone: UTC{tz_offset} ({tz_name}), Unix: {unix_timestamp}"
            )
        else:
            return ToolResult(
                content=[{"type": "text", "text": f"Error: Unknown mode '{mode}'"}],
                status="error",
                toolUseId=str(uuid4()),
            )

        return ToolResult(
            content=[{"type": "text", "text": result}],
            status="success",
            toolUseId=str(uuid4()),
        )
    except ValueError as e:
        return ToolResult(
            content=[
                {"type": "text", "text": f"Error: Invalid format string. {str(e)}"}
            ],
            status="error",
            toolUseId=str(uuid4()),
        )
    except Exception as e:
        return ToolResult(
            content=[{"type": "text", "text": f"Error: {str(e)}"}],
            status="error",
            toolUseId=str(uuid4()),
        )


class ClockToolImpl(ITool):
    """
    Implementation of ITool interface for clock tool using Strands framework.

    This class wraps the Strands clock tool and provides the ITool interface
    for integration with FivcPlayground's component architecture.
    """

    def __init__(self):
        """Initialize the clock tool."""
        self._name = "clock"
        self._description = "Get current time and date information in various formats (time, date, datetime, timezone, time_in_tz, unix, info)"
        self._underlying = _clock_impl

    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return self._name

    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return self._description

    def get_underlying(self) -> Any:
        """Get the underlying Strands tool object."""
        return self._underlying
