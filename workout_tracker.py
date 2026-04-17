"""
Workout Tracker Module

Provides persistent workout session logging with daily JSON files.
Requires RAILWAY_VOLUME_MOUNT_PATH environment variable to be set.
Files are stored as YYYY-MM-DD.json for fast daily lookups.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import get_timezone

logger = logging.getLogger(__name__)

# ============================================================================
# Validation
# ============================================================================

VALID_SESSION_TYPES = {"strength", "cardio", "hiit", "bodyweight", "mobility", "rest"}
VALID_EXERCISE_TYPES = {"strength", "cardio", "hiit", "bodyweight"}


def _validate_exercises(parsed: List[Dict]) -> Optional[str]:
    """Validate exercises list. Returns error string or None if valid."""
    if not isinstance(parsed, list):
        return "exercises must be a JSON array"

    for i, ex in enumerate(parsed):
        n = i + 1
        if not isinstance(ex, dict):
            return f"Exercise {n} must be an object"
        if not ex.get("exercise_type"):
            return f"Exercise {n} missing 'exercise_type'"
        if ex["exercise_type"] not in VALID_EXERCISE_TYPES:
            return f"Exercise {n}: invalid exercise_type '{ex['exercise_type']}'. Must be one of: {sorted(VALID_EXERCISE_TYPES)}"
        if not ex.get("name"):
            return f"Exercise {n} missing 'name'"

        etype = ex["exercise_type"]

        if etype in ("strength", "bodyweight"):
            sets = ex.get("sets")
            if not sets or not isinstance(sets, list):
                return f"Exercise '{ex['name']}' must have at least one set"
            for j, s in enumerate(sets):
                if not isinstance(s, dict):
                    return f"Set {j+1} of '{ex['name']}' must be an object"
                if not s.get("reps") and not s.get("duration_seconds"):
                    return f"Set {j+1} of '{ex['name']}' must have 'reps' or 'duration_seconds'"
                if "set_number" not in s:
                    s["set_number"] = j + 1

        elif etype == "cardio":
            if not ex.get("duration_seconds") and not ex.get("distance_meters"):
                return f"Exercise '{ex['name']}' (cardio) must have 'duration_seconds' or 'distance_meters'"

        elif etype == "hiit":
            if not ex.get("rounds"):
                return f"Exercise '{ex['name']}' (hiit) must have 'rounds'"
            if not ex.get("work_seconds"):
                return f"Exercise '{ex['name']}' (hiit) must have 'work_seconds'"

    return None


# ============================================================================
# Storage Client
# ============================================================================

class WorkoutTrackerClient:
    """Client for logging workout sessions with daily JSON file storage."""

    def __init__(self):
        mount_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        if not mount_path:
            raise ValueError("RAILWAY_VOLUME_MOUNT_PATH environment variable is required")
        self._data_dir = Path(mount_path) / "workouts"
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _day_file(self, date: str) -> Path:
        return self._data_dir / f"{date}.json"

    def _load(self, date: str) -> List[Dict[str, Any]]:
        f = self._day_file(date)
        if not f.exists():
            return []
        try:
            with open(f) as fp:
                return json.load(fp)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load workouts for {date}: {e}")
            return []

    def _save(self, date: str, records: List[Dict[str, Any]]) -> bool:
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            f = self._day_file(date)
            if not records:
                if f.exists():
                    f.unlink()
                return True
            with open(f, "w") as fp:
                json.dump(records, fp, indent=2, default=str)
            return True
        except (IOError, OSError) as e:
            logger.error(f"Failed to save workouts for {date}: {e}")
            return False

    def _all_dates(self) -> List[str]:
        dates = [f.stem for f in self._data_dir.glob("*.json") if len(f.stem) == 10]
        return sorted(dates, reverse=True)

    def _find(self, workout_id: str) -> Optional[Tuple[str, Dict[str, Any], int]]:
        for date in self._all_dates():
            for i, rec in enumerate(self._load(date)):
                if rec.get("id") == workout_id:
                    return (date, rec, i)
        return None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _today(self) -> str:
        return datetime.now(get_timezone()).strftime("%Y-%m-%d")

    def _format(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": rec.get("id"),
            "date": rec.get("date"),
            "tags": rec.get("tags", []),
            "session_type": rec.get("session_type"),
            "exercises": rec.get("exercises", []),
            "how_felt": rec.get("how_felt"),
            "notes": rec.get("notes"),
            "logged_at": rec.get("logged_at"),
            "created_at": rec.get("created_at"),
            "updated_at": rec.get("updated_at"),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_workout(
        self,
        session_type: str,
        date: Optional[str] = None,
        exercises: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None,
        how_felt: Optional[int] = None,
        notes: Optional[str] = None,
        logged_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        session_type_lower = session_type.lower()
        if session_type_lower not in VALID_SESSION_TYPES:
            return {"error": f"Invalid session_type. Must be one of: {sorted(VALID_SESSION_TYPES)}"}

        if how_felt is not None and not (1 <= how_felt <= 5):
            return {"error": "how_felt must be between 1 and 5"}

        exercises = exercises or []
        if exercises:
            err = _validate_exercises(exercises)
            if err:
                return {"error": f"exercises validation error: {err}"}

        target_date = date or self._today()
        now = self._now()

        record = {
            "id": str(uuid.uuid4()),
            "date": target_date,
            "tags": tags or [],
            "session_type": session_type_lower,
            "exercises": exercises,
            "how_felt": how_felt,
            "notes": notes,
            "logged_at": logged_at or now,
            "created_at": now,
            "updated_at": now,
        }

        records = self._load(target_date)
        records.append(record)
        if not self._save(target_date, records):
            return {"error": "Failed to save workout"}

        return {"status": "success", "workout": self._format(record)}

    def get_workout_log(self, date: Optional[str] = None) -> Dict[str, Any]:
        target_date = date or self._today()
        records = self._load(target_date)
        return {
            "status": "success",
            "date": target_date,
            "logged_count": len(records),
            "workouts": [self._format(r) for r in records],
        }

    def list_workouts(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        session_type: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        all_records: List[Dict[str, Any]] = []
        for date in self._all_dates():
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
            all_records.extend(self._load(date))

        if session_type:
            all_records = [r for r in all_records if r.get("session_type") == session_type.lower()]
        if tag:
            all_records = [r for r in all_records if tag in (r.get("tags") or [])]

        all_records = sorted(all_records, key=lambda r: r.get("logged_at", ""), reverse=True)
        return {
            "status": "success",
            "count": len(all_records[:limit]),
            "workouts": [self._format(r) for r in all_records[:limit]],
        }

    def update_workout(
        self,
        workout_id: str,
        session_type: Optional[str] = None,
        exercises: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None,
        how_felt: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        result = self._find(workout_id)
        if not result:
            return {"error": f"Workout not found: {workout_id}"}

        if how_felt is not None and not (1 <= how_felt <= 5):
            return {"error": "how_felt must be between 1 and 5"}

        date, record, index = result

        if session_type is not None:
            st = session_type.lower()
            if st not in VALID_SESSION_TYPES:
                return {"error": f"Invalid session_type. Must be one of: {sorted(VALID_SESSION_TYPES)}"}
            record["session_type"] = st
        if exercises is not None:
            err = _validate_exercises(exercises)
            if err:
                return {"error": f"exercises validation error: {err}"}
            record["exercises"] = exercises
        if tags is not None:
            record["tags"] = tags
        if how_felt is not None:
            record["how_felt"] = how_felt
        if notes is not None:
            record["notes"] = notes

        record["updated_at"] = self._now()
        records = self._load(date)
        records[index] = record
        if not self._save(date, records):
            return {"error": "Failed to update workout"}

        return {"status": "success", "workout": self._format(record)}

    def delete_workout(self, workout_id: str) -> Dict[str, Any]:
        result = self._find(workout_id)
        if not result:
            return {"error": f"Workout not found: {workout_id}"}

        date, _, index = result
        records = self._load(date)
        records.pop(index)
        if not self._save(date, records):
            return {"error": "Failed to delete workout"}

        return {"status": "success", "message": f"Workout {workout_id} deleted"}

    def get_progress(self) -> Dict[str, Any]:
        all_dates = self._all_dates()
        days_trained = 0
        rest_days_logged = 0
        feel_scores: List[int] = []

        for date in all_dates:
            for r in self._load(date):
                if r.get("session_type") == "rest":
                    rest_days_logged += 1
                else:
                    days_trained += 1
                if r.get("how_felt"):
                    feel_scores.append(r["how_felt"])

        return {
            "status": "success",
            "total_sessions": days_trained + rest_days_logged,
            "days_trained": days_trained,
            "rest_days_logged": rest_days_logged,
            "avg_feel_score": round(sum(feel_scores) / len(feel_scores), 1) if feel_scores else None,
            "first_session_date": all_dates[-1] if all_dates else None,
            "last_session_date": all_dates[0] if all_dates else None,
        }


# ============================================================================
# Singleton
# ============================================================================

_client: Optional[WorkoutTrackerClient] = None


def get_workout_tracker_client() -> WorkoutTrackerClient:
    global _client
    if _client is None:
        _client = WorkoutTrackerClient()
    return _client


def is_workout_tracker_configured() -> bool:
    return bool(os.getenv("RAILWAY_VOLUME_MOUNT_PATH"))
