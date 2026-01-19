"""
Meal Logger Module

Provides persistent meal logging with JSON file storage.
Requires RAILWAY_VOLUME_MOUNT_PATH environment variable to be set.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class MealLoggerClient:
    """Client for logging meals with persistent JSON storage."""

    def __init__(self):
        mount_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        if not mount_path:
            raise ValueError("RAILWAY_VOLUME_MOUNT_PATH environment variable is required")
        self._data_dir = Path(mount_path) / "meals"
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Meal data directory: {self._data_dir}")
        except Exception as e:
            logger.error(f"Failed to create data directory: {e}")

    def _get_meals_file(self) -> Path:
        """Get path to the meals JSON file."""
        return self._data_dir / "meals.json"

    def _load_meals(self) -> List[Dict[str, Any]]:
        """Load meals from JSON file."""
        meals_file = self._get_meals_file()
        if not meals_file.exists():
            return []
        try:
            with open(meals_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load meals: {e}")
            return []

    def _save_meals(self, meals: List[Dict[str, Any]]) -> bool:
        """Save meals to JSON file."""
        try:
            with open(self._get_meals_file(), "w") as f:
                json.dump(meals, f, indent=2, default=str)
            return True
        except IOError as e:
            logger.error(f"Failed to save meals: {e}")
            return False

    def _format_meal(self, meal: Dict[str, Any]) -> Dict[str, Any]:
        """Format meal for API response."""
        return {
            "id": meal.get("id"),
            "description": meal.get("description"),
            "meal_type": meal.get("meal_type"),
            "logged_at": meal.get("logged_at"),
            "macros": meal.get("macros", {}),
            "created_at": meal.get("created_at"),
            "updated_at": meal.get("updated_at"),
        }

    def log_meal(
        self,
        description: str,
        meal_type: str,
        logged_at: Optional[str] = None,
        calories: Optional[float] = None,
        protein: Optional[float] = None,
        carbs: Optional[float] = None,
        fat: Optional[float] = None,
        fiber: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Log a new meal."""
        meal_type_lower = meal_type.lower()
        valid_types = [t.value for t in MealType]
        if meal_type_lower not in valid_types:
            return {"error": f"Invalid meal type. Must be one of: {valid_types}"}

        now = datetime.utcnow().isoformat() + "Z"
        meal = {
            "id": str(uuid.uuid4()),
            "description": description,
            "meal_type": meal_type_lower,
            "logged_at": logged_at or now,
            "macros": _build_macros(calories, protein, carbs, fat, fiber),
            "created_at": now,
            "updated_at": now,
        }

        meals = self._load_meals()
        meals.append(meal)

        if not self._save_meals(meals):
            return {"error": "Failed to save meal"}

        return {"status": "success", "meal": self._format_meal(meal)}

    def list_meals(
        self,
        meal_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List meals with optional filters."""
        meals = self._load_meals()

        if meal_type:
            meals = [m for m in meals if m.get("meal_type") == meal_type.lower()]

        if start_date:
            meals = [m for m in meals if m.get("logged_at", "") >= start_date]

        if end_date:
            meals = [m for m in meals if m.get("logged_at", "") <= end_date]

        meals = sorted(meals, key=lambda m: m.get("logged_at", ""), reverse=True)
        meals = meals[:limit]

        return {
            "status": "success",
            "count": len(meals),
            "meals": [self._format_meal(m) for m in meals],
        }

    def get_meal(self, meal_id: str) -> Dict[str, Any]:
        """Get a specific meal by ID."""
        meals = self._load_meals()
        meal = next((m for m in meals if m.get("id") == meal_id), None)

        if not meal:
            return {"error": f"Meal not found: {meal_id}"}

        return {"status": "success", "meal": self._format_meal(meal)}

    def update_meal(
        self,
        meal_id: str,
        description: Optional[str] = None,
        meal_type: Optional[str] = None,
        logged_at: Optional[str] = None,
        calories: Optional[float] = None,
        protein: Optional[float] = None,
        carbs: Optional[float] = None,
        fat: Optional[float] = None,
        fiber: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update an existing meal."""
        meals = self._load_meals()
        meal_index = next(
            (i for i, m in enumerate(meals) if m.get("id") == meal_id), None
        )

        if meal_index is None:
            return {"error": f"Meal not found: {meal_id}"}

        meal = meals[meal_index]

        if description is not None:
            meal["description"] = description

        if meal_type is not None:
            meal_type_lower = meal_type.lower()
            valid_types = [t.value for t in MealType]
            if meal_type_lower not in valid_types:
                return {"error": f"Invalid meal type. Must be one of: {valid_types}"}
            meal["meal_type"] = meal_type_lower

        if logged_at is not None:
            meal["logged_at"] = logged_at

        macro_updates = _build_macros(calories, protein, carbs, fat, fiber)
        if macro_updates:
            meal["macros"] = {**meal.get("macros", {}), **macro_updates}

        meal["updated_at"] = datetime.utcnow().isoformat() + "Z"
        meals[meal_index] = meal

        if not self._save_meals(meals):
            return {"error": "Failed to save meal"}

        return {"status": "success", "meal": self._format_meal(meal)}

    def delete_meal(self, meal_id: str) -> Dict[str, Any]:
        """Delete a meal."""
        meals = self._load_meals()
        original_count = len(meals)
        meals = [m for m in meals if m.get("id") != meal_id]

        if len(meals) == original_count:
            return {"error": f"Meal not found: {meal_id}"}

        if not self._save_meals(meals):
            return {"error": "Failed to delete meal"}

        return {"status": "success", "message": f"Meal {meal_id} deleted"}

    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get nutrition summary for a specific day."""
        target_date = date or datetime.utcnow().strftime("%Y-%m-%d")
        meals = self._load_meals()

        day_meals = [
            m for m in meals if m.get("logged_at", "").startswith(target_date)
        ]

        totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
        by_type = {}

        for meal in day_meals:
            macros = meal.get("macros", {})
            for key in totals:
                totals[key] += macros.get(key, 0) or 0

            meal_type = meal.get("meal_type", "unknown")
            if meal_type not in by_type:
                by_type[meal_type] = []
            by_type[meal_type].append(self._format_meal(meal))

        return {
            "status": "success",
            "date": target_date,
            "meal_count": len(day_meals),
            "totals": totals,
            "meals_by_type": by_type,
        }


def _build_macros(
    calories: Optional[float] = None,
    protein: Optional[float] = None,
    carbs: Optional[float] = None,
    fat: Optional[float] = None,
    fiber: Optional[float] = None,
) -> Dict[str, float]:
    """Build macros dict from optional values."""
    macros = {}
    if calories is not None:
        macros["calories"] = calories
    if protein is not None:
        macros["protein"] = protein
    if carbs is not None:
        macros["carbs"] = carbs
    if fat is not None:
        macros["fat"] = fat
    if fiber is not None:
        macros["fiber"] = fiber
    return macros


_client: Optional[MealLoggerClient] = None


def get_meal_logger_client() -> MealLoggerClient:
    """Get or create the MealLoggerClient singleton."""
    global _client
    if _client is None:
        _client = MealLoggerClient()
    return _client


def is_meal_logger_configured() -> bool:
    """Check if meal logger storage is configured."""
    return bool(os.getenv("RAILWAY_VOLUME_MOUNT_PATH"))
