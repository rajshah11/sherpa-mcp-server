"""
Workout Tracker MCP Server - Log and track the 50-day workout plan.
"""

import json
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


def _parse_exercises(exercises_str: Optional[str]) -> tuple:
    """Parse exercises JSON string. Returns (list, None) or (None, error_str)."""
    if not exercises_str:
        return [], None
    try:
        parsed = json.loads(exercises_str)
        if not isinstance(parsed, list):
            return None, "exercises must be a JSON array"
        return parsed, None
    except json.JSONDecodeError as e:
        return None, f"exercises parse error: {e}"


def _parse_tags(tags_str: Optional[str]) -> Optional[list]:
    """Split comma-separated tags string into a list."""
    if not tags_str:
        return None
    return [t.strip() for t in tags_str.split(",") if t.strip()]


@workout_tracker_server.tool(
    name="workout_log",
    description=(
        "Log a workout session. Pass exercises as a JSON string array. "
        "For rest/recovery days, use session_type='rest' and omit exercises."
    )
)
async def log_workout(
    session_type: str,
    date: Optional[str] = None,
    exercises: Optional[str] = None,
    tags: Optional[str] = None,
    how_felt: Optional[int] = None,
    notes: Optional[str] = None,
    logged_at: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Log a workout session.

    Args:
        session_type: One of: strength, cardio, hiit, bodyweight, mobility, rest
        date: Date of the workout in YYYY-MM-DD format (defaults to today)
        exercises: JSON string array of exercise objects. Each object must include
            'exercise_type' (strength/cardio/hiit/bodyweight) and 'name'.

            Strength example:
              '[{"exercise_type":"strength","name":"Back Squat","equipment":"barbell",
                 "sets":[{"reps":8,"weight_lbs":125},{"reps":8,"weight_lbs":125}]}]'

            Bodyweight/timed example:
              '[{"exercise_type":"bodyweight","name":"Plank",
                 "sets":[{"duration_seconds":60},{"duration_seconds":45}]}]'

            Cardio example:
              '[{"exercise_type":"cardio","name":"HIIT Circuit","duration_seconds":1500}]'

            HIIT/interval example:
              '[{"exercise_type":"hiit","name":"Tabata","rounds":4,"work_seconds":20,"rest_seconds":10}]'

        tags: Comma-separated grouping tags, e.g. "phase-1,lower,gym"
        how_felt: Energy/effort rating 1-5 (1=exhausted, 5=great)
        notes: Free-text notes (e.g. modifications made, baby sleep quality)
        logged_at: ISO datetime when the workout occurred (defaults to now)
    """
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        parsed_exercises, err = _parse_exercises(exercises)
        if err:
            return {"error": err}

        parsed_tags = _parse_tags(tags)

        if ctx:
            await ctx.info(f"Logging {session_type} session")

        return get_workout_tracker_client().log_workout(
            session_type=session_type,
            date=date,
            exercises=parsed_exercises,
            tags=parsed_tags,
            how_felt=how_felt,
            notes=notes,
            logged_at=logged_at,
        )
    except Exception as e:
        logger.error(f"Failed to log workout: {e}")
        return {"error": str(e)}


@workout_tracker_server.tool(
    name="workout_get_plan",
    description="Get the planned workout for a specific day number (1-50) or date"
)
async def get_plan(
    day_number: Optional[int] = None,
    date: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Get the planned workout.

    Args:
        day_number: Plan day number 1-50
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
    description="Get all logged workout entries for a date, alongside the plan for that day"
)
async def get_workout_log(
    date: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Get logged workouts for a day alongside the plan.

    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
    """
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Getting workout log for date={date or 'today'}")

        return get_workout_tracker_client().get_workout_log(date=date)
    except Exception as e:
        logger.error(f"Failed to get workout log: {e}")
        return {"error": str(e)}


@workout_tracker_server.tool(
    name="workout_list",
    description="List logged workout sessions with optional date range, session type, or tag filters"
)
async def list_workouts(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    session_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
    ctx: Context = None
) -> dict:
    """
    List logged workouts.

    Args:
        start_date: Filter on or after this date (YYYY-MM-DD)
        end_date: Filter on or before this date (YYYY-MM-DD)
        session_type: Filter by type — strength, cardio, hiit, bodyweight, mobility, rest
        tag: Filter by a single tag value (e.g. "phase-1", "gym")
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
            session_type=session_type,
            tag=tag,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Failed to list workouts: {e}")
        return {"error": str(e)}


@workout_tracker_server.tool(
    name="workout_update",
    description=(
        "Update an existing workout log entry. "
        "To modify exercises, pass the full updated exercises JSON string — it replaces the existing list entirely."
    )
)
async def update_workout(
    workout_id: str,
    session_type: Optional[str] = None,
    exercises: Optional[str] = None,
    tags: Optional[str] = None,
    how_felt: Optional[int] = None,
    notes: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Update a logged workout entry.

    Args:
        workout_id: ID of the workout log entry to update
        session_type: New session type
        exercises: Full replacement JSON string array of exercise objects.
                   Replaces all existing exercises. Fetch current entry with
                   workout_get_log first, modify the array, then pass it here.
        tags: New comma-separated tags (replaces existing tags)
        how_felt: Updated rating 1-5
        notes: Updated notes
    """
    if not is_workout_tracker_configured():
        return NOT_CONFIGURED_ERROR

    try:
        parsed_exercises = None
        if exercises is not None:
            parsed_exercises, err = _parse_exercises(exercises)
            if err:
                return {"error": err}

        parsed_tags = _parse_tags(tags)

        if ctx:
            await ctx.info(f"Updating workout: {workout_id}")

        return get_workout_tracker_client().update_workout(
            workout_id=workout_id,
            session_type=session_type,
            exercises=parsed_exercises,
            tags=parsed_tags,
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
    description="Get an overall progress summary — days trained, rest days logged, feel scores, days remaining"
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
        phase: Filter by phase — "Phase 1", "Phase 2", or "Phase 3"
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
