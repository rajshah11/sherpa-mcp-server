"""
Workout Tracker MCP Server - Log and track the 50-day workout plan.
"""

import logging
from typing import Optional

from fastmcp import Context, FastMCP

from workout_tracker import get_workout_tracker_client, is_workout_tracker_configured

logger = logging.getLogger(__name__)

workout_tracker_server = FastMCP(name="Workout Tracker")

NOT_CONFIGURED_ERROR = {
    "error": "Workout tracker not configured",
    "message": "RAILWAY_VOLUME_MOUNT_PATH environment variable is required. Attach a volume to your Railway service."
}


@workout_tracker_server.tool(
    name="workout_log",
    description="Log a workout session for the 50-day plan — mark it completed or skipped, rate how you felt, and add notes"
)
async def log_workout(
    completed: bool,
    date: Optional[str] = None,
    day_number: Optional[int] = None,
    actual_workout: Optional[str] = None,
    how_felt: Optional[int] = None,
    notes: Optional[str] = None,
    logged_at: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Log a workout session.

    Args:
        completed: Whether the workout was completed
        date: Date of the workout in YYYY-MM-DD format (defaults to today)
        day_number: Plan day number (1-50); inferred from date if not provided
        actual_workout: Description of what was actually done (if different from plan)
        how_felt: Energy/effort rating 1-5 (1=exhausted, 5=great)
        notes: Free-text notes, e.g. baby sleep quality, modifications made
        logged_at: ISO datetime when the workout occurred (defaults to now)
    """
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Logging workout (completed={completed})")

        return get_workout_tracker_client().log_workout(
            completed=completed,
            date=date,
            day_number=day_number,
            actual_workout=actual_workout,
            how_felt=how_felt,
            notes=notes,
            logged_at=logged_at,
        )
    except Exception as e:
        logger.error(f"Failed to log workout: {e}")
        return {"error": str(e)}


@workout_tracker_server.tool(
    name="workout_get_plan",
    description="Get the planned workout for a specific day number or date"
)
async def get_plan(
    day_number: Optional[int] = None,
    date: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Get the planned workout.

    Args:
        day_number: Plan day number (1-50)
        date: Date in YYYY-MM-DD format (defaults to today if neither provided)
    """
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Getting plan for day={day_number}, date={date}")

        return get_workout_tracker_client().get_plan(day_number=day_number, date=date)
    except Exception as e:
        logger.error(f"Failed to get plan: {e}")
        return {"error": str(e)}


@workout_tracker_server.tool(
    name="workout_get_log",
    description="Get the logged workout entry (and the plan) for a specific day or date"
)
async def get_workout_log(
    day_number: Optional[int] = None,
    date: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Get logged workout(s) for a day, alongside the plan.

    Args:
        day_number: Plan day number (1-50)
        date: Date in YYYY-MM-DD format (defaults to today)
    """
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Getting workout log for day={day_number}, date={date}")

        return get_workout_tracker_client().get_workout_log(day_number=day_number, date=date)
    except Exception as e:
        logger.error(f"Failed to get workout log: {e}")
        return {"error": str(e)}


@workout_tracker_server.tool(
    name="workout_list",
    description="List logged workout sessions with optional date range and completion filters"
)
async def list_workouts(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    completed_only: bool = False,
    limit: int = 50,
    ctx: Context = None
) -> dict:
    """
    List logged workouts.

    Args:
        start_date: Filter on or after this date (YYYY-MM-DD)
        end_date: Filter on or before this date (YYYY-MM-DD)
        completed_only: Return only completed sessions
        limit: Maximum results to return (default 50)
    """
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info("Fetching workout history...")

        return get_workout_tracker_client().list_workouts(
            start_date=start_date,
            end_date=end_date,
            completed_only=completed_only,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Failed to list workouts: {e}")
        return {"error": str(e)}


@workout_tracker_server.tool(
    name="workout_update",
    description="Update an existing workout log entry (completion status, feel score, notes, etc.)"
)
async def update_workout(
    workout_id: str,
    completed: Optional[bool] = None,
    actual_workout: Optional[str] = None,
    how_felt: Optional[int] = None,
    notes: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Update a logged workout.

    Args:
        workout_id: ID of the workout log entry to update
        completed: New completion status
        actual_workout: Updated description of what was done
        how_felt: Updated rating 1-5
        notes: Updated notes
    """
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Updating workout: {workout_id}")

        return get_workout_tracker_client().update_workout(
            workout_id=workout_id,
            completed=completed,
            actual_workout=actual_workout,
            how_felt=how_felt,
            notes=notes,
        )
    except Exception as e:
        logger.error(f"Failed to update workout: {e}")
        return {"error": str(e)}


@workout_tracker_server.tool(
    name="workout_delete",
    description="Delete a workout log entry by ID"
)
async def delete_workout(
    workout_id: str,
    ctx: Context = None
) -> dict:
    """Delete a workout log entry."""
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Deleting workout: {workout_id}")

        return get_workout_tracker_client().delete_workout(workout_id)
    except Exception as e:
        logger.error(f"Failed to delete workout: {e}")
        return {"error": str(e)}


@workout_tracker_server.tool(
    name="workout_progress",
    description="Get an overall progress summary across the 50-day plan — completion rate, feel scores, days remaining"
)
async def get_progress(ctx: Context = None) -> dict:
    """Get overall 50-day plan progress summary."""
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info("Calculating workout progress...")

        return get_workout_tracker_client().get_progress()
    except Exception as e:
        logger.error(f"Failed to get progress: {e}")
        return {"error": str(e)}


@workout_tracker_server.tool(
    name="workout_list_plan",
    description="List all 50 days of the workout plan, optionally filtered by phase or type (Gym/Home/Rest)"
)
async def list_plan(
    phase: Optional[str] = None,
    workout_type: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    List the full 50-day plan.

    Args:
        phase: Filter by phase name, e.g. "Phase 1", "Phase 2", "Phase 3"
        workout_type: Filter by type — "Gym", "Home", or "Rest"
    """
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info("Listing workout plan...")

        return get_workout_tracker_client().list_plan(phase=phase, workout_type=workout_type)
    except Exception as e:
        logger.error(f"Failed to list plan: {e}")
        return {"error": str(e)}
