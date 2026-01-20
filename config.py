"""
Shared configuration for Sherpa MCP Server.

Environment variables:
- TIMEZONE: Timezone for date/time operations (e.g., "America/Los_Angeles"). Defaults to UTC.
"""

import logging
import os
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
