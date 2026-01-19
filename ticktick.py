"""
TickTick Integration Module

Handles TickTick API authentication and task/project management.
Requires TICKTICK_ACCESS_TOKEN environment variable.
Use scripts/ticktick_auth.py to generate the token.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

TICKTICK_API_BASE = "https://api.ticktick.com/open/v1"


class TickTickClient:
    """Client for interacting with TickTick API."""

    def __init__(self):
        """Initialize the TickTick client."""
        self._access_token = os.getenv("TICKTICK_ACCESS_TOKEN")
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if not self._access_token:
            raise RuntimeError(
                "TickTick not configured. "
                "Set TICKTICK_ACCESS_TOKEN environment variable. "
                "Use scripts/ticktick_auth.py to generate token."
            )

        if self._client is None:
            self._client = httpx.Client(
                base_url=TICKTICK_API_BASE,
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )

        return self._client

    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return bool(self._access_token)

    # ========================================================================
    # Project Operations
    # ========================================================================

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects (task lists) accessible to the user."""
        client = self._get_client()
        response = client.get("/project")
        response.raise_for_status()
        return [self._format_project(proj) for proj in response.json()]

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get a specific project by ID."""
        client = self._get_client()
        response = client.get(f"/project/{project_id}")
        response.raise_for_status()
        return self._format_project(response.json())

    def get_project_with_tasks(self, project_id: str) -> Dict[str, Any]:
        """Get a project with all its tasks."""
        client = self._get_client()
        response = client.get(f"/project/{project_id}/data")
        response.raise_for_status()
        data = response.json()

        return {
            "project": self._format_project(data.get("project", {})),
            "tasks": [self._format_task(task) for task in data.get("tasks", [])],
            "columns": data.get("columns", [])
        }

    def create_project(
        self,
        name: str,
        color: Optional[str] = None,
        view_mode: str = "list",
        kind: str = "TASK"
    ) -> Dict[str, Any]:
        """Create a new project."""
        client = self._get_client()
        body = {"name": name, "viewMode": view_mode, "kind": kind}
        if color:
            body["color"] = color

        response = client.post("/project", json=body)
        response.raise_for_status()
        proj = response.json()
        logger.info(f"Created project: {proj.get('id')}")
        return self._format_project(proj)

    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        color: Optional[str] = None,
        view_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing project."""
        client = self._get_client()
        body = self._build_optional_fields(name=name, color=color, viewMode=view_mode)

        response = client.post(f"/project/{project_id}", json=body)
        response.raise_for_status()
        logger.info(f"Updated project: {project_id}")
        return self._format_project(response.json())

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        client = self._get_client()
        response = client.delete(f"/project/{project_id}")
        response.raise_for_status()
        logger.info(f"Deleted project: {project_id}")
        return True

    # ========================================================================
    # Task Operations
    # ========================================================================

    def get_task(self, project_id: str, task_id: str) -> Dict[str, Any]:
        """Get a specific task by ID."""
        client = self._get_client()
        response = client.get(f"/project/{project_id}/task/{task_id}")
        response.raise_for_status()
        task = response.json()
        return self._format_task(task)

    def create_task(
        self,
        title: str,
        project_id: str,
        content: Optional[str] = None,
        desc: Optional[str] = None,
        start_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        time_zone: str = "America/Los_Angeles",
        is_all_day: bool = False,
        priority: int = 0,
        reminders: Optional[List[str]] = None,
        items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a new task."""
        client = self._get_client()

        body = {
            "title": title,
            "projectId": project_id,
            "timeZone": time_zone,
            "isAllDay": is_all_day,
            "priority": priority
        }

        if content:
            body["content"] = content
        if desc:
            body["desc"] = desc
        if start_date:
            body["startDate"] = self._format_datetime(start_date)
        if due_date:
            body["dueDate"] = self._format_datetime(due_date)
        if reminders:
            body["reminders"] = reminders
        if items:
            body["items"] = items

        response = client.post("/task", json=body)
        response.raise_for_status()
        task = response.json()
        logger.info(f"Created task: {task.get('id')}")

        return self._format_task(task)

    def update_task(
        self,
        task_id: str,
        project_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        desc: Optional[str] = None,
        start_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        time_zone: Optional[str] = None,
        is_all_day: Optional[bool] = None,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an existing task."""
        client = self._get_client()
        body = {"id": task_id, "projectId": project_id}

        optional = self._build_optional_fields(
            title=title,
            content=content,
            desc=desc,
            timeZone=time_zone,
            isAllDay=is_all_day,
            priority=priority
        )
        body.update(optional)

        if start_date is not None:
            body["startDate"] = self._format_datetime(start_date)
        if due_date is not None:
            body["dueDate"] = self._format_datetime(due_date)

        response = client.post(f"/task/{task_id}", json=body)
        response.raise_for_status()
        logger.info(f"Updated task: {task_id}")
        return self._format_task(response.json())

    def complete_task(self, project_id: str, task_id: str) -> bool:
        """Mark a task as complete."""
        client = self._get_client()
        response = client.post(f"/project/{project_id}/task/{task_id}/complete")
        response.raise_for_status()
        logger.info(f"Completed task: {task_id}")
        return True

    def delete_task(self, project_id: str, task_id: str) -> bool:
        """Delete a task."""
        client = self._get_client()
        response = client.delete(f"/project/{project_id}/task/{task_id}")
        response.raise_for_status()
        logger.info(f"Deleted task: {task_id}")
        return True

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _build_optional_fields(self, **kwargs) -> Dict[str, Any]:
        """Build a dictionary with only non-None values."""
        return {k: v for k, v in kwargs.items() if v is not None}

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for TickTick API."""
        if dt.tzinfo:
            return dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        return dt.strftime("%Y-%m-%dT%H:%M:%S+0000")

    def _format_project(self, proj: Dict[str, Any]) -> Dict[str, Any]:
        """Format a raw project response into a clean dictionary."""
        return {
            "id": proj.get("id"),
            "name": proj.get("name"),
            "color": proj.get("color"),
            "closed": proj.get("closed", False),
            "group_id": proj.get("groupId"),
            "view_mode": proj.get("viewMode"),
            "sort_order": proj.get("sortOrder"),
            "kind": proj.get("kind"),
            "permission": proj.get("permission")
        }

    def _format_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Format a raw task response into a clean dictionary."""
        return {
            "id": task.get("id"),
            "project_id": task.get("projectId"),
            "title": task.get("title"),
            "content": task.get("content"),
            "desc": task.get("desc"),
            "is_all_day": task.get("isAllDay", False),
            "start_date": task.get("startDate"),
            "due_date": task.get("dueDate"),
            "time_zone": task.get("timeZone"),
            "reminders": task.get("reminders", []),
            "repeat_flag": task.get("repeatFlag"),
            "priority": task.get("priority", 0),
            "status": task.get("status", 0),
            "completed_time": task.get("completedTime"),
            "sort_order": task.get("sortOrder"),
            "kind": task.get("kind"),
            "items": [
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "status": item.get("status", 0),
                    "sort_order": item.get("sortOrder"),
                    "start_date": item.get("startDate"),
                    "is_all_day": item.get("isAllDay", False),
                    "time_zone": item.get("timeZone"),
                    "completed_time": item.get("completedTime")
                }
                for item in task.get("items", [])
            ]
        }


# Global client instance
_ticktick_client: Optional[TickTickClient] = None


def get_ticktick_client() -> TickTickClient:
    """Get or create the global TickTick client."""
    global _ticktick_client
    if _ticktick_client is None:
        _ticktick_client = TickTickClient()
    return _ticktick_client


def is_ticktick_configured() -> bool:
    """Check if TickTick is configured via environment variables."""
    return bool(os.getenv("TICKTICK_ACCESS_TOKEN"))
