"""
TickTick MCP Server - Task management tools.
"""

import datetime
import logging
from typing import Optional
from fastmcp import FastMCP, Context

from ticktick import get_ticktick_client, is_ticktick_configured

logger = logging.getLogger(__name__)

ticktick_server = FastMCP(name="TickTick")


def _check_configured() -> Optional[dict]:
    """Return error dict if not configured, None if OK."""
    if not is_ticktick_configured():
        return {
            "error": "TickTick not configured",
            "message": "Please set up TickTick credentials. See TICKTICK_SETUP.md"
        }
    return None


# ============================================================================
# Project Tools
# ============================================================================

@ticktick_server.tool(
    name="ticktick_list_projects",
    description="List all TickTick projects (task lists)"
)
async def list_projects(ctx: Context) -> dict:
    """List all projects the user has access to."""
    if err := _check_configured():
        return err

    try:
        await ctx.info("Fetching TickTick projects...")
        client = get_ticktick_client()
        projects = client.list_projects()
        return {"projects": projects, "count": len(projects)}
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return {"error": str(e)}


@ticktick_server.tool(
    name="ticktick_get_project",
    description="Get a specific TickTick project with all its tasks"
)
async def get_project(
    project_id: str,
    include_tasks: bool = True,
    ctx: Context = None
) -> dict:
    """Get a project by ID, optionally with all its tasks."""
    if err := _check_configured():
        return err

    try:
        if ctx:
            await ctx.info(f"Fetching project: {project_id}")

        client = get_ticktick_client()
        if include_tasks:
            result = client.get_project_with_tasks(project_id)
        else:
            result = {"project": client.get_project(project_id)}
        return result
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        return {"error": str(e)}


@ticktick_server.tool(
    name="ticktick_create_project",
    description="Create a new TickTick project (task list)"
)
async def create_project(
    name: str,
    color: Optional[str] = None,
    view_mode: str = "list",
    ctx: Context = None
) -> dict:
    """Create a new project."""
    if err := _check_configured():
        return err

    try:
        if ctx:
            await ctx.info(f"Creating project: {name}")

        client = get_ticktick_client()
        project = client.create_project(
            name=name,
            color=color,
            view_mode=view_mode
        )
        return {"status": "created", "project": project}
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        return {"error": str(e)}


@ticktick_server.tool(
    name="ticktick_delete_project",
    description="Delete a TickTick project"
)
async def delete_project(
    project_id: str,
    ctx: Context = None
) -> dict:
    """Delete a project."""
    if err := _check_configured():
        return err

    try:
        if ctx:
            await ctx.info(f"Deleting project: {project_id}")

        client = get_ticktick_client()
        client.delete_project(project_id)
        return {"status": "deleted", "project_id": project_id}
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        return {"error": str(e)}


# ============================================================================
# Task Tools
# ============================================================================

@ticktick_server.tool(
    name="ticktick_get_task",
    description="Get a specific TickTick task"
)
async def get_task(
    project_id: str,
    task_id: str,
    ctx: Context = None
) -> dict:
    """Get a specific task by ID."""
    if err := _check_configured():
        return err

    try:
        if ctx:
            await ctx.info(f"Fetching task: {task_id}")

        client = get_ticktick_client()
        task = client.get_task(project_id=project_id, task_id=task_id)
        return {"task": task}
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        return {"error": str(e)}


@ticktick_server.tool(
    name="ticktick_create_task",
    description="Create a new task in TickTick"
)
async def create_task(
    title: str,
    project_id: str,
    content: Optional[str] = None,
    desc: Optional[str] = None,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
    time_zone: str = "America/Los_Angeles",
    is_all_day: bool = False,
    priority: int = 0,
    ctx: Context = None
) -> dict:
    """Create a new task."""
    if err := _check_configured():
        return err

    try:
        if ctx:
            await ctx.info(f"Creating task: {title}")

        client = get_ticktick_client()

        # Parse dates if provided
        start_dt = None
        due_dt = None
        if start_date:
            start_dt = datetime.datetime.fromisoformat(start_date.replace("Z", ""))
        if due_date:
            due_dt = datetime.datetime.fromisoformat(due_date.replace("Z", ""))

        task = client.create_task(
            title=title,
            project_id=project_id,
            content=content,
            desc=desc,
            start_date=start_dt,
            due_date=due_dt,
            time_zone=time_zone,
            is_all_day=is_all_day,
            priority=priority
        )
        return {"status": "created", "task": task}
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        return {"error": str(e)}


@ticktick_server.tool(
    name="ticktick_update_task",
    description="Update an existing TickTick task"
)
async def update_task(
    task_id: str,
    project_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    desc: Optional[str] = None,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
    time_zone: Optional[str] = None,
    is_all_day: Optional[bool] = None,
    priority: Optional[int] = None,
    ctx: Context = None
) -> dict:
    """Update an existing task."""
    if err := _check_configured():
        return err

    try:
        if ctx:
            await ctx.info(f"Updating task: {task_id}")

        client = get_ticktick_client()

        # Parse dates if provided
        start_dt = None
        due_dt = None
        if start_date:
            start_dt = datetime.datetime.fromisoformat(start_date.replace("Z", ""))
        if due_date:
            due_dt = datetime.datetime.fromisoformat(due_date.replace("Z", ""))

        task = client.update_task(
            task_id=task_id,
            project_id=project_id,
            title=title,
            content=content,
            desc=desc,
            start_date=start_dt,
            due_date=due_dt,
            time_zone=time_zone,
            is_all_day=is_all_day,
            priority=priority
        )
        return {"status": "updated", "task": task}
    except Exception as e:
        logger.error(f"Failed to update task: {e}")
        return {"error": str(e)}


@ticktick_server.tool(
    name="ticktick_complete_task",
    description="Mark a TickTick task as complete"
)
async def complete_task(
    project_id: str,
    task_id: str,
    ctx: Context = None
) -> dict:
    """Mark a task as complete."""
    if err := _check_configured():
        return err

    try:
        if ctx:
            await ctx.info(f"Completing task: {task_id}")

        client = get_ticktick_client()
        client.complete_task(project_id=project_id, task_id=task_id)
        return {
            "status": "completed",
            "task_id": task_id,
            "project_id": project_id
        }
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        return {"error": str(e)}


@ticktick_server.tool(
    name="ticktick_delete_task",
    description="Delete a TickTick task"
)
async def delete_task(
    project_id: str,
    task_id: str,
    ctx: Context = None
) -> dict:
    """Delete a task."""
    if err := _check_configured():
        return err

    try:
        if ctx:
            await ctx.info(f"Deleting task: {task_id}")

        client = get_ticktick_client()
        client.delete_task(project_id=project_id, task_id=task_id)
        return {
            "status": "deleted",
            "task_id": task_id,
            "project_id": project_id
        }
    except Exception as e:
        logger.error(f"Failed to delete task: {e}")
        return {"error": str(e)}
