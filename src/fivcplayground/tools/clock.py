"""
Clock tool for getting current time and date information.

This module provides a unified clock tool for retrieving current time, date,
and timezone information. The tool is implemented using LangChain's @tool
decorator for seamless integration with agents.

The clock tool supports multiple modes:
    - "time": Get current time in specified fmt
    - "date": Get current date in specified fmt
    - "datetime": Get current date and time
    - "timezone": Get current timezone information
    - "time_in_tz": Get time in specific timezone
    - "unix": Get Unix timestamp
    - "info": Get comprehensive time information
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones
from typing import Literal


def clock(
    mode: Literal[
        "time", "date", "datetime", "timezone", "time_in_tz", "unix", "info"
    ] = "datetime",
    fmt: str = "",
    tz: str = "",
) -> str:
    """
    Get current time and date information in various formats.

    Args:
        mode: Operation mode (default: "datetime")
            - "time": Get current time (fmt: "%H:%M:%S")
            - "date": Get current date (fmt: "%Y-%m-%d")
            - "datetime": Get current date and time (fmt: "%Y-%m-%d %H:%M:%S")
            - "timezone": Get current timezone information
            - "time_in_tz": Get time in specific timezone (requires tz)
            - "unix": Get Unix timestamp
            - "info": Get comprehensive time information

        fmt: Custom fmt string using strftime syntax
            Common formats:
            - Time: "%H:%M:%S" (14:30:45), "%I:%M %p" (02:30 PM)
            - Date: "%Y-%m-%d" (2024-10-28), "%m/%d/%Y" (10/28/2024)
            - Date: "%A, %B %d, %Y" (Monday, October 28, 2024)
            - DateTime: "%Y-%m-%d %H:%M:%S" (2024-10-28 14:30:45)

        tz: Timezone name for "time_in_tz" mode
            Examples: "America/New_York", "Europe/London", "Asia/Tokyo"

    Returns:
        Formatted time/date string or error message

    Examples:
        >>> clock()
        '2024-10-28 14:30:45'
        >>> clock(mode="time")
        '14:30:45'
        >>> clock(mode="date", fmt="%A, %B %d, %Y")
        'Monday, October 28, 2024'
        >>> clock(mode="time_in_tz", tz="America/New_York")
        '2024-10-28 10:30:45'
        >>> clock(mode="unix")
        '1729094445'
        >>> clock(mode="info")
        'Date: 2024-10-28, Time: 14:30:45, Timezone: UTC-07:00 (PDT), Unix: 1729094445'
    """
    try:
        if mode == "time":
            fmt = fmt or "%H:%M:%S"
            return datetime.now().strftime(fmt)

        elif mode == "date":
            fmt = fmt or "%Y-%m-%d"
            return datetime.now().strftime(fmt)

        elif mode == "datetime":
            fmt = fmt or "%Y-%m-%d %H:%M:%S"
            return datetime.now().strftime(fmt)

        elif mode == "timezone":
            now = datetime.now(timezone.utc).astimezone()
            tz_name = now.tzname()
            tz_offset = now.strftime("%z")
            if len(tz_offset) >= 5:
                tz_offset = f"{tz_offset[:-2]}:{tz_offset[-2:]}"
            return f"UTC{tz_offset} ({tz_name})"

        elif mode == "time_in_tz":
            if not tz:
                return "Error: tz is required for 'time_in_tz' mode"
            if tz not in available_timezones():
                available = ", ".join(sorted(list(available_timezones())[:10]))
                return f"Error: Unknown timezone '{tz}'. Available timezones include: {available}..."
            tz = ZoneInfo(tz)
            fmt = fmt or "%Y-%m-%d %H:%M:%S"
            return datetime.now(tz).strftime(fmt)

        elif mode == "unix":
            timestamp = int(datetime.now().timestamp())
            return str(timestamp)

        elif mode == "info":
            now = datetime.now(timezone.utc).astimezone()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            tz_name = now.tzname()
            tz_offset = now.strftime("%z")
            if len(tz_offset) >= 5:
                tz_offset = f"{tz_offset[:-2]}:{tz_offset[-2:]}"
            unix_timestamp = int(datetime.now().timestamp())
            return (
                f"Date: {date_str}, Time: {time_str}, "
                f"Timezone: UTC{tz_offset} ({tz_name}), Unix: {unix_timestamp}"
            )

        else:
            return f"Error: Unknown mode '{mode}'. Valid modes: time, date, datetime, timezone, time_in_tz, unix, info"

    except ValueError as e:
        return f"Error: Invalid fmt string. {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
