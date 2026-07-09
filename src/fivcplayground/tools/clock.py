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
from typing import Literal

from zoneinfo import ZoneInfo, available_timezones


def _format_utc_offset(dt: datetime) -> str:
    tz_offset = dt.strftime("%z")
    if len(tz_offset) >= 5:
        return f"{tz_offset[:-2]}:{tz_offset[-2:]}"
    return tz_offset


def _timezone_label(dt: datetime) -> str:
    tz_name = dt.tzname() or "UTC"
    return f"UTC{_format_utc_offset(dt)} ({tz_name})"


def _format_with_timezone(dt: datetime, fmt: str) -> str:
    formatted = dt.strftime(fmt)
    if "%z" in fmt or "%Z" in fmt:
        return formatted
    return f"{formatted} {_timezone_label(dt)}"


def _format_iso_datetime(dt: datetime) -> str:
    return f"{dt.strftime('%Y-%m-%dT%H:%M:%S')}{_format_utc_offset(dt)}"


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
            - "time": Get current UTC time (fmt: "%H:%M:%S %Z")
            - "date": Get current UTC date (fmt: "%Y-%m-%d %Z")
            - "datetime": Get current UTC date and time (ISO-like with offset)
            - "timezone": Get UTC timezone information
            - "time_in_tz": Get time in specific timezone (requires tz)
            - "unix": Get Unix timestamp
            - "info": Get comprehensive UTC time information

        fmt: Custom fmt string using strftime syntax
            Timezone information is appended when fmt omits both "%z" and "%Z".
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
        '2024-10-28T14:30:45+00:00'
        >>> clock(mode="time")
        '14:30:45 UTC'
        >>> clock(mode="date", fmt="%A, %B %d, %Y")
        'Monday, October 28, 2024 UTC+00:00 (UTC)'
        >>> clock(mode="time_in_tz", tz="America/New_York")
        '2024-10-28T10:30:45-04:00'
        >>> clock(mode="unix")
        '1729094445'
        >>> clock(mode="info")
        'Date: 2024-10-28, Time: 14:30:45, Timezone: UTC+00:00 (UTC), Unix: 1729094445'
    """
    try:
        now = datetime.now(timezone.utc)
        if mode == "time":
            fmt = fmt or "%H:%M:%S %Z"
            return _format_with_timezone(now, fmt)

        elif mode == "date":
            fmt = fmt or "%Y-%m-%d %Z"
            return _format_with_timezone(now, fmt)

        elif mode == "datetime":
            if not fmt:
                return _format_iso_datetime(now)
            return _format_with_timezone(now, fmt)

        elif mode == "timezone":
            return _timezone_label(now)

        elif mode == "time_in_tz":
            if not tz:
                return "Error: tz is required for 'time_in_tz' mode"
            if tz not in available_timezones():
                available = ", ".join(sorted(list(available_timezones())[:10]))
                return f"Error: Unknown timezone '{tz}'. Available timezones include: {available}..."
            tz = ZoneInfo(tz)
            now_in_tz = now.astimezone(tz)
            if not fmt:
                return _format_iso_datetime(now_in_tz)
            return _format_with_timezone(now_in_tz, fmt)

        elif mode == "unix":
            timestamp = int(now.timestamp())
            return str(timestamp)

        elif mode == "info":
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            unix_timestamp = int(now.timestamp())
            return (
                f"Date: {date_str}, Time: {time_str}, "
                f"Timezone: {_timezone_label(now)}, Unix: {unix_timestamp}"
            )

        else:
            return f"Error: Unknown mode '{mode}'. Valid modes: time, date, datetime, timezone, time_in_tz, unix, info"

    except ValueError as e:
        return f"Error: Invalid fmt string. {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
