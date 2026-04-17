"""
Workout Tracker Module

Provides persistent workout logging with daily JSON files.
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
# Embedded 50-Day Workout Plan (Apr 17 – Jun 5, 2026)
# Used only by workout_get_plan and workout_list_plan tools.
# Log entries do NOT reference or embed this plan.
# ============================================================================

WORKOUT_PLAN: Dict[int, Dict[str, str]] = {
    1:  {"date": "2026-04-17", "phase": "Phase 1", "type": "Gym",  "focus": "Lower (Squat)",       "workout_summary": "Back Squat 3x8 @ 125lb, DB Romanian DL 3x10, DB rows 3x10",                                                                         "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    2:  {"date": "2026-04-18", "phase": "Phase 1", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "20-min beginner HIIT: jumping jacks, high knees, mountain climbers, burpees (30s on / 30s off)",                                      "duration": "25 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    3:  {"date": "2026-04-19", "phase": "Phase 1", "type": "Gym",  "focus": "Lower (Deadlift)",     "workout_summary": "Deadlift 3x8 @ 135lb, DB Romanian DL 3x10, DB rows 3x10",                                                                            "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    4:  {"date": "2026-04-20", "phase": "Phase 1", "type": "Home", "focus": "Core & Mobility",      "workout_summary": "Plank circuit (front/side), dead bugs, bird dogs, hip stretches, cat-cow",                                                            "duration": "30 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    5:  {"date": "2026-04-21", "phase": "Phase 1", "type": "Gym",  "focus": "Lower (Front Squat)",  "workout_summary": "Front Squat 3x8 @ 115lb, DB Romanian DL 3x10, DB rows 3x10",                                                                         "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    6:  {"date": "2026-04-22", "phase": "Phase 1", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "Tabata-style: 4 rounds (squat jumps, push-ups, lunges, plank jacks) — 20s on / 10s off x8",                                           "duration": "25 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    7:  {"date": "2026-04-23", "phase": "Phase 1", "type": "Rest", "focus": "Active Recovery",      "workout_summary": "Walk with baby, gentle stretching, foam roll if available. Complete rest also OK.",                                                    "duration": "20-30 min", "plan_notes": "Listen to your body. Sleep > workout if exhausted."},
    8:  {"date": "2026-04-24", "phase": "Phase 1", "type": "Gym",  "focus": "Lower (Squat)",        "workout_summary": "Back Squat 3x8 @ 135lb, DB Romanian DL 3x10, DB rows 3x10",                                                                          "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    9:  {"date": "2026-04-25", "phase": "Phase 1", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "20-min beginner HIIT: jumping jacks, high knees, mountain climbers, burpees (30s on / 30s off)",                                      "duration": "25 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    10: {"date": "2026-04-26", "phase": "Phase 1", "type": "Gym",  "focus": "Lower (Deadlift)",     "workout_summary": "Deadlift 3x8 @ 145lb, DB Romanian DL 3x10, DB rows 3x10",                                                                            "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    11: {"date": "2026-04-27", "phase": "Phase 1", "type": "Home", "focus": "Core & Mobility",      "workout_summary": "Plank circuit (front/side), dead bugs, bird dogs, hip stretches, cat-cow",                                                            "duration": "30 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    12: {"date": "2026-04-28", "phase": "Phase 1", "type": "Gym",  "focus": "Lower (Front Squat)",  "workout_summary": "Front Squat 3x8 @ 125lb, DB Romanian DL 3x10, DB rows 3x10",                                                                         "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    13: {"date": "2026-04-29", "phase": "Phase 1", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "Tabata-style: 4 rounds (squat jumps, push-ups, lunges, plank jacks) — 20s on / 10s off x8",                                           "duration": "25 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    14: {"date": "2026-04-30", "phase": "Phase 1", "type": "Rest", "focus": "Active Recovery",      "workout_summary": "Walk with baby, gentle stretching, foam roll if available. Complete rest also OK.",                                                    "duration": "20-30 min", "plan_notes": "Listen to your body. Sleep > workout if exhausted."},
    15: {"date": "2026-05-01", "phase": "Phase 2", "type": "Gym",  "focus": "Lower (Squat)",        "workout_summary": "Back Squat 4x6 @ 145lb, KB swings 3x15, DB lunges 3x10/leg, DB press 3x10",                                                          "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    16: {"date": "2026-05-02", "phase": "Phase 2", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "30-min intermediate HIIT: burpees, tuck jumps, push-up variations, sprint in place (40s on / 20s off)",                               "duration": "35 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    17: {"date": "2026-05-03", "phase": "Phase 2", "type": "Gym",  "focus": "Lower (Deadlift)",     "workout_summary": "Deadlift 4x6 @ 160lb, KB swings 3x15, DB lunges 3x10/leg, DB press 3x10",                                                            "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    18: {"date": "2026-05-04", "phase": "Phase 2", "type": "Home", "focus": "Bodyweight Strength",  "workout_summary": "Push-up progressions, pistol squat practice, pike push-ups, hollow body holds, L-sits",                                               "duration": "35 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    19: {"date": "2026-05-05", "phase": "Phase 2", "type": "Gym",  "focus": "Lower (Front Squat)",  "workout_summary": "Front Squat 4x6 @ 135lb, KB swings 3x15, DB lunges 3x10/leg, DB press 3x10",                                                         "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    20: {"date": "2026-05-06", "phase": "Phase 2", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "EMOM 30 min: alternate — 10 burpees / 15 air squats / 10 push-ups / 20 mountain climbers",                                            "duration": "35 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    21: {"date": "2026-05-07", "phase": "Phase 2", "type": "Rest", "focus": "Active Recovery",      "workout_summary": "Walk with baby, gentle stretching, foam roll if available. Complete rest also OK.",                                                    "duration": "20-30 min", "plan_notes": "Listen to your body. Sleep > workout if exhausted."},
    22: {"date": "2026-05-08", "phase": "Phase 2", "type": "Gym",  "focus": "Lower (Squat)",        "workout_summary": "Back Squat 4x6 @ 155lb, KB swings 3x15, DB lunges 3x10/leg, DB press 3x10",                                                          "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    23: {"date": "2026-05-09", "phase": "Phase 2", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "30-min intermediate HIIT: burpees, tuck jumps, push-up variations, sprint in place (40s on / 20s off)",                               "duration": "35 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    24: {"date": "2026-05-10", "phase": "Phase 2", "type": "Gym",  "focus": "Lower (Deadlift)",     "workout_summary": "Deadlift 4x6 @ 170lb, KB swings 3x15, DB lunges 3x10/leg, DB press 3x10",                                                            "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    25: {"date": "2026-05-11", "phase": "Phase 2", "type": "Home", "focus": "Bodyweight Strength",  "workout_summary": "Push-up progressions, pistol squat practice, pike push-ups, hollow body holds, L-sits",                                               "duration": "35 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    26: {"date": "2026-05-12", "phase": "Phase 2", "type": "Gym",  "focus": "Lower (Front Squat)",  "workout_summary": "Front Squat 4x6 @ 145lb, KB swings 3x15, DB lunges 3x10/leg, DB press 3x10",                                                         "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    27: {"date": "2026-05-13", "phase": "Phase 2", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "EMOM 30 min: alternate — 10 burpees / 15 air squats / 10 push-ups / 20 mountain climbers",                                            "duration": "35 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    28: {"date": "2026-05-14", "phase": "Phase 2", "type": "Rest", "focus": "Active Recovery",      "workout_summary": "Walk with baby, gentle stretching, foam roll if available. Complete rest also OK.",                                                    "duration": "20-30 min", "plan_notes": "Listen to your body. Sleep > workout if exhausted."},
    29: {"date": "2026-05-15", "phase": "Phase 2", "type": "Gym",  "focus": "Lower (Squat)",        "workout_summary": "Back Squat 4x6 @ 145lb, KB swings 3x15, DB lunges 3x10/leg, DB press 3x10",                                                          "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    30: {"date": "2026-05-16", "phase": "Phase 2", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "30-min intermediate HIIT: burpees, tuck jumps, push-up variations, sprint in place (40s on / 20s off)",                               "duration": "35 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    31: {"date": "2026-05-17", "phase": "Phase 2", "type": "Gym",  "focus": "Lower (Deadlift)",     "workout_summary": "Deadlift 4x6 @ 160lb, KB swings 3x15, DB lunges 3x10/leg, DB press 3x10",                                                            "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 90-120s between sets."},
    32: {"date": "2026-05-18", "phase": "Phase 2", "type": "Home", "focus": "Bodyweight Strength",  "workout_summary": "Push-up progressions, pistol squat practice, pike push-ups, hollow body holds, L-sits",                                               "duration": "35 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    33: {"date": "2026-05-19", "phase": "Phase 3", "type": "Gym",  "focus": "Lower (Front Squat)",  "workout_summary": "Front Squat 5x5 @ 150lb, KB goblet squats 3x12, DB RDL 3x8, DB rows 4x8",                                                            "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 2-3 min between working sets."},
    34: {"date": "2026-05-20", "phase": "Phase 3", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "Chipper: 50 air squats, 40 push-ups, 30 jump lunges, 20 burpees, 10 handstand push-up attempts, then reverse",                         "duration": "40 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    35: {"date": "2026-05-21", "phase": "Phase 3", "type": "Rest", "focus": "Active Recovery",      "workout_summary": "Walk with baby, gentle stretching, foam roll if available. Complete rest also OK.",                                                    "duration": "20-30 min", "plan_notes": "Listen to your body. Sleep > workout if exhausted."},
    36: {"date": "2026-05-22", "phase": "Phase 3", "type": "Gym",  "focus": "Lower (Squat)",        "workout_summary": "Back Squat 5x5 @ 170lb, KB goblet squats 3x12, DB RDL 3x8, DB rows 4x8",                                                             "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 2-3 min between working sets."},
    37: {"date": "2026-05-23", "phase": "Phase 3", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "35-min advanced HIIT: devil press (bodyweight), broad jumps, clap push-ups, box jumps on stairs (45s on / 15s off)",                  "duration": "40 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    38: {"date": "2026-05-24", "phase": "Phase 3", "type": "Gym",  "focus": "Lower (Deadlift)",     "workout_summary": "Deadlift 5x5 @ 185lb, KB goblet squats 3x12, DB RDL 3x8, DB rows 4x8",                                                               "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 2-3 min between working sets."},
    39: {"date": "2026-05-25", "phase": "Phase 3", "type": "Home", "focus": "Plyometric Power",     "workout_summary": "Jump squat complexes, explosive push-ups, split jump lunges, lateral bounds, depth jumps",                                             "duration": "35 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    40: {"date": "2026-05-26", "phase": "Phase 3", "type": "Gym",  "focus": "Lower (Front Squat)",  "workout_summary": "Front Squat 5x5 @ 160lb, KB goblet squats 3x12, DB RDL 3x8, DB rows 4x8",                                                            "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 2-3 min between working sets."},
    41: {"date": "2026-05-27", "phase": "Phase 3", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "Chipper: 50 air squats, 40 push-ups, 30 jump lunges, 20 burpees, 10 handstand push-up attempts, then reverse",                         "duration": "40 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    42: {"date": "2026-05-28", "phase": "Phase 3", "type": "Rest", "focus": "Active Recovery",      "workout_summary": "Walk with baby, gentle stretching, foam roll if available. Complete rest also OK.",                                                    "duration": "20-30 min", "plan_notes": "Listen to your body. Sleep > workout if exhausted."},
    43: {"date": "2026-05-29", "phase": "Phase 3", "type": "Gym",  "focus": "Lower (Squat)",        "workout_summary": "Back Squat 5x5 @ 180lb, KB goblet squats 3x12, DB RDL 3x8, DB rows 4x8",                                                             "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 2-3 min between working sets."},
    44: {"date": "2026-05-30", "phase": "Phase 3", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "35-min advanced HIIT: devil press (bodyweight), broad jumps, clap push-ups, box jumps on stairs (45s on / 15s off)",                  "duration": "40 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    45: {"date": "2026-05-31", "phase": "Phase 3", "type": "Gym",  "focus": "Lower (Deadlift)",     "workout_summary": "Deadlift 5x5 @ 195lb, KB goblet squats 3x12, DB RDL 3x8, DB rows 4x8",                                                               "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 2-3 min between working sets."},
    46: {"date": "2026-06-01", "phase": "Phase 3", "type": "Home", "focus": "Plyometric Power",     "workout_summary": "Jump squat complexes, explosive push-ups, split jump lunges, lateral bounds, depth jumps",                                             "duration": "35 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    47: {"date": "2026-06-02", "phase": "Phase 3", "type": "Gym",  "focus": "Lower (Front Squat)",  "workout_summary": "Front Squat 5x5 @ 165lb, KB goblet squats 3x12, DB RDL 3x8, DB rows 4x8",                                                            "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 2-3 min between working sets."},
    48: {"date": "2026-06-03", "phase": "Phase 3", "type": "Home", "focus": "Cardio / HIIT",        "workout_summary": "Chipper: 50 air squats, 40 push-ups, 30 jump lunges, 20 burpees, 10 handstand push-up attempts, then reverse",                         "duration": "40 min",    "plan_notes": "Follow a YouTube video or timer app. Scale as needed."},
    49: {"date": "2026-06-04", "phase": "Phase 3", "type": "Rest", "focus": "Active Recovery",      "workout_summary": "Walk with baby, gentle stretching, foam roll if available. Complete rest also OK.",                                                    "duration": "20-30 min", "plan_notes": "Listen to your body. Sleep > workout if exhausted."},
    50: {"date": "2026-06-05", "phase": "Phase 3", "type": "Gym",  "focus": "Lower (Squat)",        "workout_summary": "Back Squat 5x5 @ 185lb, KB goblet squats 3x12, DB RDL 3x8, DB rows 4x8",                                                             "duration": "35-45 min", "plan_notes": "Warm up 5 min. Rest 2-3 min between working sets."},
}

_DATE_TO_DAY: Dict[str, int] = {v["date"]: k for k, v in WORKOUT_PLAN.items()}

PLAN_START_DATE = "2026-04-17"
PLAN_END_DATE = "2026-06-05"
TOTAL_PLAN_DAYS = 50


def get_plan_for_day(day_number: int) -> Optional[Dict[str, Any]]:
    entry = WORKOUT_PLAN.get(day_number)
    if not entry:
        return None
    return {"day_number": day_number, **entry}


def get_plan_for_date(date: str) -> Optional[Dict[str, Any]]:
    day = _DATE_TO_DAY.get(date)
    if day is None:
        return None
    return get_plan_for_day(day)


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
                # Assign set_number if absent
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
    """Client for logging workouts with daily JSON file storage."""

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
        """Log a new workout session."""
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

    def get_plan(self, day_number: Optional[int] = None, date: Optional[str] = None) -> Dict[str, Any]:
        """Get the planned workout for a day number or date."""
        if day_number is not None:
            plan = get_plan_for_day(day_number)
            if not plan:
                return {"error": f"No plan found for day {day_number}"}
            return {"status": "success", "plan": plan}

        target_date = date or self._today()
        plan = get_plan_for_date(target_date)
        if not plan:
            return {"error": f"No plan found for date {target_date}"}
        return {"status": "success", "plan": plan}

    def get_workout_log(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get all logged workouts for a specific date."""
        target_date = date or self._today()
        records = self._load(target_date)
        plan = get_plan_for_date(target_date)

        return {
            "status": "success",
            "date": target_date,
            "plan": plan,
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
        """List logged workouts with optional filters."""
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
        all_records = all_records[:limit]

        return {
            "status": "success",
            "count": len(all_records),
            "workouts": [self._format(r) for r in all_records],
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
        """Update an existing workout log entry."""
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
        """Delete a workout log entry."""
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
        """Get overall progress summary across the 50-day plan."""
        logged_dates = set(self._all_dates())
        days_trained = 0
        rest_days_logged = 0
        feel_scores: List[int] = []

        for plan in WORKOUT_PLAN.values():
            plan_date = plan["date"]
            if plan_date in logged_dates:
                records = self._load(plan_date)
                for r in records:
                    st = r.get("session_type", "")
                    if st == "rest":
                        rest_days_logged += 1
                    else:
                        days_trained += 1
                    if r.get("how_felt"):
                        feel_scores.append(r["how_felt"])

        today = self._today()
        days_elapsed = len([d for d in WORKOUT_PLAN.values() if d["date"] <= today])

        return {
            "status": "success",
            "total_plan_days": TOTAL_PLAN_DAYS,
            "days_elapsed": days_elapsed,
            "days_trained": days_trained,
            "rest_days_logged": rest_days_logged,
            "days_remaining": TOTAL_PLAN_DAYS - days_elapsed,
            "completion_rate_pct": round((days_trained + rest_days_logged) / max(days_elapsed, 1) * 100, 1),
            "avg_feel_score": round(sum(feel_scores) / len(feel_scores), 1) if feel_scores else None,
            "plan_start": PLAN_START_DATE,
            "plan_end": PLAN_END_DATE,
        }

    def list_plan(
        self,
        phase: Optional[str] = None,
        workout_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all 50 plan days, optionally filtered."""
        days = [{"day_number": k, **v} for k, v in WORKOUT_PLAN.items()]
        if phase:
            days = [d for d in days if phase.lower() in d["phase"].lower()]
        if workout_type:
            days = [d for d in days if workout_type.lower() in d["type"].lower()]
        return {"status": "success", "count": len(days), "plan": days}


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
