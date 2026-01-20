"""
Meal Logger Module

Provides persistent meal logging with daily JSON files.
Requires RAILWAY_VOLUME_MOUNT_PATH environment variable to be set.
Files are stored as YYYY-MM-DD.json for fast daily lookups.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class MealLoggerClient:
    """Client for logging meals with daily JSON file storage."""

    def __init__(self):
        mount_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        if not mount_path:
            raise ValueError("RAILWAY_VOLUME_MOUNT_PATH environment variable is required")
        self._data_dir = Path(mount_path) / "meals"
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _get_date_file(self, date: str) -> Path:
        """Get path to the JSON file for a specific date (YYYY-MM-DD)."""
        return self._data_dir / f"{date}.json"

    def _extract_date(self, logged_at: str) -> str:
        """Extract YYYY-MM-DD from an ISO datetime string."""
        return logged_at[:10]

    def _load_day_meals(self, date: str) -> List[Dict[str, Any]]:
        """Load meals for a specific date."""
        date_file = self._get_date_file(date)
        if not date_file.exists():
            return []
        try:
            with open(date_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load meals for {date}: {e}")
            return []

    def _save_day_meals(self, date: str, meals: List[Dict[str, Any]]) -> bool:
        """Save meals for a specific date."""
        try:
            self._ensure_data_dir()
            date_file = self._get_date_file(date)
            if not meals:
                if date_file.exists():
                    date_file.unlink()
                return True
            with open(date_file, "w") as f:
                json.dump(meals, f, indent=2, default=str)
            return True
        except (IOError, OSError) as e:
            logger.error(f"Failed to save meals for {date}: {e}")
            return False

    def _list_date_files(self) -> List[str]:
        """List all dates that have meal files, sorted descending."""
        dates = []
        for f in self._data_dir.glob("*.json"):
            if f.stem and len(f.stem) == 10:  # YYYY-MM-DD format
                dates.append(f.stem)
        return sorted(dates, reverse=True)

    def _find_meal(self, meal_id: str) -> Optional[Tuple[str, Dict[str, Any], int]]:
        """Find a meal by ID across all files. Returns (date, meal, index) or None."""
        for date in self._list_date_files():
            meals = self._load_day_meals(date)
            for i, meal in enumerate(meals):
                if meal.get("id") == meal_id:
                    return (date, meal, i)
        return None

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

    def _now_iso(self) -> str:
        """Get current UTC time in ISO format."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _today(self) -> str:
        """Get today's date as YYYY-MM-DD."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

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

        now = self._now_iso()
        logged_at = logged_at or now
        date = self._extract_date(logged_at)

        meal = {
            "id": str(uuid.uuid4()),
            "description": description,
            "meal_type": meal_type_lower,
            "logged_at": logged_at,
            "macros": _build_macros(calories, protein, carbs, fat, fiber),
            "created_at": now,
            "updated_at": now,
        }

        meals = self._load_day_meals(date)
        meals.append(meal)

        if not self._save_day_meals(date, meals):
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
        all_meals = []
        for date in self._list_date_files():
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
            all_meals.extend(self._load_day_meals(date))

        if meal_type:
            all_meals = [m for m in all_meals if m.get("meal_type") == meal_type.lower()]

        all_meals = sorted(all_meals, key=lambda m: m.get("logged_at", ""), reverse=True)
        all_meals = all_meals[:limit]

        return {
            "status": "success",
            "count": len(all_meals),
            "meals": [self._format_meal(m) for m in all_meals],
        }

    def get_meal(self, meal_id: str) -> Dict[str, Any]:
        """Get a specific meal by ID."""
        result = self._find_meal(meal_id)
        if not result:
            return {"error": f"Meal not found: {meal_id}"}
        return {"status": "success", "meal": self._format_meal(result[1])}

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
        result = self._find_meal(meal_id)
        if not result:
            return {"error": f"Meal not found: {meal_id}"}

        old_date, meal, index = result

        if description is not None:
            meal["description"] = description

        if meal_type is not None:
            meal_type_lower = meal_type.lower()
            valid_types = [t.value for t in MealType]
            if meal_type_lower not in valid_types:
                return {"error": f"Invalid meal type. Must be one of: {valid_types}"}
            meal["meal_type"] = meal_type_lower

        new_date = old_date
        if logged_at is not None:
            meal["logged_at"] = logged_at
            new_date = self._extract_date(logged_at)

        macro_updates = _build_macros(calories, protein, carbs, fat, fiber)
        if macro_updates:
            meal["macros"] = {**meal.get("macros", {}), **macro_updates}

        meal["updated_at"] = self._now_iso()

        if new_date != old_date:
            # Move meal to new date file
            old_meals = self._load_day_meals(old_date)
            old_meals.pop(index)
            if not self._save_day_meals(old_date, old_meals):
                return {"error": "Failed to update meal"}
            new_meals = self._load_day_meals(new_date)
            new_meals.append(meal)
            if not self._save_day_meals(new_date, new_meals):
                return {"error": "Failed to update meal"}
        else:
            meals = self._load_day_meals(old_date)
            meals[index] = meal
            if not self._save_day_meals(old_date, meals):
                return {"error": "Failed to update meal"}

        return {"status": "success", "meal": self._format_meal(meal)}

    def delete_meal(self, meal_id: str) -> Dict[str, Any]:
        """Delete a meal."""
        result = self._find_meal(meal_id)
        if not result:
            return {"error": f"Meal not found: {meal_id}"}

        date, _, index = result
        meals = self._load_day_meals(date)
        meals.pop(index)

        if not self._save_day_meals(date, meals):
            return {"error": "Failed to delete meal"}

        return {"status": "success", "message": f"Meal {meal_id} deleted"}

    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get nutrition summary for a specific day."""
        target_date = date or self._today()
        meals = self._load_day_meals(target_date)

        totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
        by_type: Dict[str, List] = {}

        for meal in meals:
            macros = meal.get("macros", {})
            for key in totals:
                totals[key] += macros.get(key, 0) or 0

            mt = meal.get("meal_type", "unknown")
            if mt not in by_type:
                by_type[mt] = []
            by_type[mt].append(self._format_meal(meal))

        return {
            "status": "success",
            "date": target_date,
            "meal_count": len(meals),
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
