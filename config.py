"""
Shared configuration for Sherpa MCP Server.

Environment variables:
- TIMEZONE: Timezone for date/time operations (e.g., "America/Los_Angeles"). Defaults to UTC.
"""

import logging
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

_timezone: ZoneInfo | None = None


def get_timezone() -> ZoneInfo:
    """Get configured timezone or default to UTC."""
    global _timezone
    if _timezone is None:
        tz_name = os.getenv("TIMEZONE", "UTC")
        try:
            _timezone = ZoneInfo(tz_name)
        except Exception:
            logger.warning(f"Invalid timezone '{tz_name}', falling back to UTC")
            _timezone = ZoneInfo("UTC")
    return _timezone


def parse_datetime_input(dt_string: str) -> datetime:
    """Parse ISO string; treat naive datetimes as local timezone, return UTC-aware datetime."""
    if dt_string.endswith("Z"):
        dt_string = dt_string[:-1] + "+00:00"
    dt = datetime.fromisoformat(dt_string)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=get_timezone())
    return dt.astimezone(timezone.utc)


def format_datetime_local(utc_string: str) -> str:
    """Convert stored UTC ISO string to local timezone ISO string for caller display."""
    if utc_string.endswith("Z"):
        utc_string = utc_string[:-1] + "+00:00"
    dt = datetime.fromisoformat(utc_string)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(get_timezone()).isoformat()
