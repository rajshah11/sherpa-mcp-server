"""
Water Tracker Module

Provides persistent water consumption logging with daily JSON files.
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

from config import format_datetime_local, get_timezone, parse_datetime_input

logger = logging.getLogger(__name__)

WATER_DAILY_GOAL_ML_DEFAULT = 1920.0


# ============================================================================
# Storage Client
# ============================================================================

class WaterTrackerClient:
    """Client for logging water consumption with daily JSON file storage."""

    def __init__(self):
        mount_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
        if not mount_path:
            raise ValueError("RAILWAY_VOLUME_MOUNT_PATH environment variable is required")
        self._data_dir = Path(mount_path) / "water"
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
            logger.error(f"Failed to load water entries for {date}: {e}")
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
            logger.error(f"Failed to save water entries for {date}: {e}")
            return False

    def _all_dates(self) -> List[str]:
        dates = [f.stem for f in self._data_dir.glob("*.json") if len(f.stem) == 10]
        return sorted(dates, reverse=True)

    def _find(self, entry_id: str) -> Optional[Tuple[str, Dict[str, Any], int]]:
        for date in self._all_dates():
            for i, rec in enumerate(self._load(date)):
                if rec.get("id") == entry_id:
                    return (date, rec, i)
        return None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _today(self) -> str:
        return datetime.now(get_timezone()).strftime("%Y-%m-%d")

    def _get_local_date(self, iso_timestamp: str) -> str:
        return parse_datetime_input(iso_timestamp).astimezone(get_timezone()).strftime("%Y-%m-%d")

    def _format(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": rec.get("id"),
            "amount_ml": rec.get("amount_ml"),
            "logged_at": format_datetime_local(rec["logged_at"]) if rec.get("logged_at") else None,
            "notes": rec.get("notes"),
            "created_at": format_datetime_local(rec["created_at"]) if rec.get("created_at") else None,
            "updated_at": format_datetime_local(rec["updated_at"]) if rec.get("updated_at") else None,
        }

    def _get_daily_goal_ml(self) -> float:
        raw = os.getenv("WATER_DAILY_GOAL_ML", str(WATER_DAILY_GOAL_ML_DEFAULT))
        try:
            val = float(raw)
            if val <= 0:
                raise ValueError("must be positive")
            return val
        except (ValueError, TypeError):
            logger.warning(f"Invalid WATER_DAILY_GOAL_ML='{raw}', using default {WATER_DAILY_GOAL_ML_DEFAULT}ml")
            return WATER_DAILY_GOAL_ML_DEFAULT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_water(
        self,
        amount_ml: float,
        logged_at: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        if amount_ml <= 0:
            return {"error": "amount_ml must be a positive number"}

        now = self._now()
        if logged_at:
            logged_at = parse_datetime_input(logged_at).isoformat().replace("+00:00", "Z")
        entry_logged_at = logged_at or now
        target_date = self._get_local_date(entry_logged_at)

        record = {
            "id": str(uuid.uuid4()),
            "amount_ml": float(amount_ml),
            "logged_at": entry_logged_at,
            "notes": notes,
            "created_at": now,
            "updated_at": now,
        }

        records = self._load(target_date)
        records.append(record)
        if not self._save(target_date, records):
            return {"error": "Failed to save water entry"}

        return {"status": "success", "entry": self._format(record)}

    def get_entry(self, entry_id: str) -> Dict[str, Any]:
        result = self._find(entry_id)
        if not result:
            return {"error": f"Water entry not found: {entry_id}"}
        return {"status": "success", "entry": self._format(result[1])}

    def update_entry(
        self,
        entry_id: str,
        amount_ml: Optional[float] = None,
        logged_at: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        result = self._find(entry_id)
        if not result:
            return {"error": f"Water entry not found: {entry_id}"}

        if amount_ml is not None and amount_ml <= 0:
            return {"error": "amount_ml must be a positive number"}

        date, record, index = result

        if amount_ml is not None:
            record["amount_ml"] = float(amount_ml)
        if logged_at is not None:
            record["logged_at"] = parse_datetime_input(logged_at).isoformat().replace("+00:00", "Z")
        if notes is not None:
            record["notes"] = notes

        record["updated_at"] = self._now()
        records = self._load(date)
        records[index] = record
        if not self._save(date, records):
            return {"error": "Failed to update water entry"}

        return {"status": "success", "entry": self._format(record)}

    def delete_entry(self, entry_id: str) -> Dict[str, Any]:
        result = self._find(entry_id)
        if not result:
            return {"error": f"Water entry not found: {entry_id}"}

        date, _, index = result
        records = self._load(date)
        records.pop(index)
        if not self._save(date, records):
            return {"error": "Failed to delete water entry"}

        return {"status": "success", "message": f"Water entry {entry_id} deleted"}

    def list_entries(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        all_records: List[Dict[str, Any]] = []
        for date in self._all_dates():
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
            all_records.extend(self._load(date))

        all_records = sorted(all_records, key=lambda r: r.get("logged_at", ""), reverse=True)
        return {
            "status": "success",
            "count": len(all_records[:limit]),
            "entries": [self._format(r) for r in all_records[:limit]],
        }

    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        target_date = date or self._today()
        records = self._load(target_date)

        total_ml = sum(r.get("amount_ml", 0) for r in records)
        goal_ml = self._get_daily_goal_ml()
        goal_pct = round(total_ml / goal_ml * 100, 1)

        sorted_records = sorted(records, key=lambda r: r.get("logged_at", ""))

        return {
            "status": "success",
            "date": target_date,
            "total_ml": total_ml,
            "entry_count": len(records),
            "goal_ml": goal_ml,
            "goal_pct": goal_pct,
            "goal_met": total_ml >= goal_ml,
            "entries": [self._format(r) for r in sorted_records],
        }


# ============================================================================
# Singleton
# ============================================================================

_client: Optional[WaterTrackerClient] = None


def get_water_tracker_client() -> WaterTrackerClient:
    global _client
    if _client is None:
        _client = WaterTrackerClient()
    return _client


def is_water_tracker_configured() -> bool:
    return bool(os.getenv("RAILWAY_VOLUME_MOUNT_PATH"))
