"""
Meal Logger MCP Server - Meal tracking and nutrition tools.
"""

import logging
from typing import Optional

from fastmcp import Context, FastMCP

from meal_logger import get_meal_logger_client, is_meal_logger_configured

logger = logging.getLogger(__name__)

meal_logger_server = FastMCP(name="Meal Logger")

NOT_CONFIGURED_ERROR = {
    "error": "Meal logger not configured",
    "message": "RAILWAY_VOLUME_MOUNT_PATH environment variable is required. Attach a volume to your Railway service."
}


@meal_logger_server.tool(
    name="meal_log",
    description="Log a new meal with description, type, time, and optional macros"
)
async def log_meal(
    description: str,
    meal_type: str,
    logged_at: Optional[str] = None,
    calories: Optional[float] = None,
    protein: Optional[float] = None,
    carbs: Optional[float] = None,
    fat: Optional[float] = None,
    fiber: Optional[float] = None,
    ctx: Context = None
) -> dict:
    """
    Log a new meal.

    Args:
        description: What you ate (e.g., "Grilled chicken salad with avocado")
        meal_type: Type of meal - breakfast, lunch, dinner, or snack
        logged_at: ISO datetime when meal was eaten (defaults to now)
        calories: Total calories
        protein: Protein in grams
        carbs: Carbohydrates in grams
        fat: Fat in grams
        fiber: Fiber in grams
    """
    if not is_meal_logger_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Logging {meal_type}: {description}")

        return get_meal_logger_client().log_meal(
            description=description,
            meal_type=meal_type,
            logged_at=logged_at,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            fiber=fiber
        )
    except Exception as e:
        logger.error(f"Failed to log meal: {e}")
        return {"error": str(e)}


@meal_logger_server.tool(
    name="meal_list",
    description="List logged meals with optional filters"
)
async def list_meals(
    meal_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    ctx: Context = None
) -> dict:
    """
    List meals with optional filters.

    Args:
        meal_type: Filter by type - breakfast, lunch, dinner, or snack
        start_date: Filter meals on or after this ISO date
        end_date: Filter meals on or before this ISO date
        limit: Maximum number of meals to return (default 50)
    """
    if not is_meal_logger_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info("Fetching meals...")

        return get_meal_logger_client().list_meals(
            meal_type=meal_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Failed to list meals: {e}")
        return {"error": str(e)}


@meal_logger_server.tool(
    name="meal_get",
    description="Get a specific meal by ID"
)
async def get_meal(
    meal_id: str,
    ctx: Context = None
) -> dict:
    """Get a meal by its ID."""
    if not is_meal_logger_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Fetching meal: {meal_id}")

        return get_meal_logger_client().get_meal(meal_id)
    except Exception as e:
        logger.error(f"Failed to get meal: {e}")
        return {"error": str(e)}


@meal_logger_server.tool(
    name="meal_update",
    description="Update an existing meal"
)
async def update_meal(
    meal_id: str,
    description: Optional[str] = None,
    meal_type: Optional[str] = None,
    logged_at: Optional[str] = None,
    calories: Optional[float] = None,
    protein: Optional[float] = None,
    carbs: Optional[float] = None,
    fat: Optional[float] = None,
    fiber: Optional[float] = None,
    ctx: Context = None
) -> dict:
    """
    Update an existing meal.

    Args:
        meal_id: ID of the meal to update
        description: New description
        meal_type: New meal type - breakfast, lunch, dinner, or snack
        logged_at: New ISO datetime
        calories: Updated calories
        protein: Updated protein in grams
        carbs: Updated carbohydrates in grams
        fat: Updated fat in grams
        fiber: Updated fiber in grams
    """
    if not is_meal_logger_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Updating meal: {meal_id}")

        return get_meal_logger_client().update_meal(
            meal_id=meal_id,
            description=description,
            meal_type=meal_type,
            logged_at=logged_at,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            fiber=fiber
        )
    except Exception as e:
        logger.error(f"Failed to update meal: {e}")
        return {"error": str(e)}


@meal_logger_server.tool(
    name="meal_delete",
    description="Delete a meal"
)
async def delete_meal(
    meal_id: str,
    ctx: Context = None
) -> dict:
    """Delete a meal by ID."""
    if not is_meal_logger_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Deleting meal: {meal_id}")

        return get_meal_logger_client().delete_meal(meal_id)
    except Exception as e:
        logger.error(f"Failed to delete meal: {e}")
        return {"error": str(e)}


@meal_logger_server.tool(
    name="meal_daily_summary",
    description="Get nutrition summary for a specific day"
)
async def get_daily_summary(
    date: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Get nutrition summary for a day.

    Args:
        date: ISO date (YYYY-MM-DD) to summarize. Defaults to today.
    """
    if not is_meal_logger_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Getting daily summary for: {date or 'today'}")

        return get_meal_logger_client().get_daily_summary(date)
    except Exception as e:
        logger.error(f"Failed to get daily summary: {e}")
        return {"error": str(e)}
