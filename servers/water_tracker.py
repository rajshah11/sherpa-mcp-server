"""
Water Tracker MCP Server - Log and query daily water consumption.
"""

import logging
from typing import Optional

from fastmcp import Context, FastMCP

from water_tracker import get_water_tracker_client, is_water_tracker_configured

logger = logging.getLogger(__name__)

water_tracker_server = FastMCP(name="Water Tracker")

NOT_CONFIGURED_ERROR = {
    "error": "Water tracker not configured",
    "message": "RAILWAY_VOLUME_MOUNT_PATH environment variable is required. Attach a volume to your Railway service."
}


@water_tracker_server.tool(
    name="water_log",
    description="Log a water intake entry with the amount in millilitres"
)
async def log_water(
    amount_ml: float,
    logged_at: Optional[str] = None,
    notes: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Log a water intake entry.

    Args:
        amount_ml: Amount consumed in millilitres (e.g. 250 for a glass, 500 for a bottle)
        logged_at: ISO datetime when water was consumed (defaults to now)
        notes: Optional label, e.g. "morning", "post-run", "with supplements"
    """
    if not is_water_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Logging water intake: {amount_ml}ml")

        return get_water_tracker_client().log_water(
            amount_ml=amount_ml,
            logged_at=logged_at,
            notes=notes,
        )
    except Exception as e:
        logger.error(f"Failed to log water: {e}")
        return {"error": str(e)}


@water_tracker_server.tool(
    name="water_get",
    description="Get a specific water intake entry by ID"
)
async def get_water_entry(
    entry_id: str,
    ctx: Context = None
) -> dict:
    """
    Get a water intake entry by ID.

    Args:
        entry_id: ID of the water entry to retrieve
    """
    if not is_water_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Fetching water entry: {entry_id}")

        return get_water_tracker_client().get_entry(entry_id)
    except Exception as e:
        logger.error(f"Failed to get water entry: {e}")
        return {"error": str(e)}


@water_tracker_server.tool(
    name="water_update",
    description="Update an existing water intake entry"
)
async def update_water_entry(
    entry_id: str,
    amount_ml: Optional[float] = None,
    logged_at: Optional[str] = None,
    notes: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Update a water intake entry.

    Args:
        entry_id: ID of the water entry to update
        amount_ml: New amount in millilitres
        logged_at: Updated ISO datetime when water was consumed
        notes: Updated notes/label
    """
    if not is_water_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Updating water entry: {entry_id}")

        return get_water_tracker_client().update_entry(
            entry_id=entry_id,
            amount_ml=amount_ml,
            logged_at=logged_at,
            notes=notes,
        )
    except Exception as e:
        logger.error(f"Failed to update water entry: {e}")
        return {"error": str(e)}


@water_tracker_server.tool(
    name="water_delete",
    description="Delete a water intake entry by ID"
)
async def delete_water_entry(
    entry_id: str,
    ctx: Context = None
) -> dict:
    """Delete a water intake entry."""
    if not is_water_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Deleting water entry: {entry_id}")

        return get_water_tracker_client().delete_entry(entry_id)
    except Exception as e:
        logger.error(f"Failed to delete water entry: {e}")
        return {"error": str(e)}


@water_tracker_server.tool(
    name="water_list",
    description="List water intake entries with optional date range filter"
)
async def list_water_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    ctx: Context = None
) -> dict:
    """
    List water intake entries.

    Args:
        start_date: Filter on or after this date (YYYY-MM-DD)
        end_date: Filter on or before this date (YYYY-MM-DD)
        limit: Maximum results to return (default 50)
    """
    if not is_water_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info("Fetching water intake history...")

        return get_water_tracker_client().list_entries(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Failed to list water entries: {e}")
        return {"error": str(e)}


@water_tracker_server.tool(
    name="water_daily_summary",
    description="Get water intake summary for a day including total ml, entry count, and progress toward daily goal"
)
async def get_water_daily_summary(
    date: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Get daily water intake summary.

    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
    """
    if not is_water_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Getting water summary for {date or 'today'}")

        return get_water_tracker_client().get_daily_summary(date=date)
    except Exception as e:
        logger.error(f"Failed to get water daily summary: {e}")
        return {"error": str(e)}
