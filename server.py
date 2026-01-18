#!/usr/bin/env python3
"""
Sherpa MCP Server - A remote MCP server with Auth0 OAuth authentication.

This server acts as a personal assistant, managing calendar events, tasks, notes,
health data, and more. It uses Auth0 for secure authentication.
"""
import os
import datetime
import logging
from typing import Optional, List
from fastmcp import FastMCP, Context
from fastmcp.server.auth.providers.auth0 import Auth0Provider
from starlette.requests import Request
from starlette.responses import JSONResponse
from dotenv import load_dotenv

# Google Calendar integration
from google_calendar import get_calendar_client, is_calendar_configured

# TickTick integration
from ticktick import get_ticktick_client, is_ticktick_configured

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Auth0 OAuth Configuration
# ============================================================================

# Check if Auth0 is configured
auth0_enabled = all([
    os.getenv("AUTH0_CONFIG_URL"),
    os.getenv("AUTH0_CLIENT_ID"),
    os.getenv("AUTH0_CLIENT_SECRET"),
    os.getenv("AUTH0_AUDIENCE")
])

if auth0_enabled:
    logger.info("Configuring Auth0 OAuth authentication...")
    auth = Auth0Provider(
        config_url=os.getenv("AUTH0_CONFIG_URL"),
        client_id=os.getenv("AUTH0_CLIENT_ID"),
        client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
        audience=os.getenv("AUTH0_AUDIENCE"),
        base_url=os.getenv("SERVER_BASE_URL", "http://localhost:8000"),

        # Optional: customize settings
        required_scopes=["openid", "profile"],
        allowed_client_redirect_uris=[
            "http://localhost:*",  # Allow MCP clients on any localhost port
        ],
        require_authorization_consent=os.getenv("REQUIRE_CONSENT", "true").lower() == "true",
    )
    logger.info("Auth0 OAuth configured successfully")
else:
    logger.warning("Auth0 not configured - running without authentication")
    logger.warning("Set AUTH0_* environment variables to enable authentication")
    auth = None

# ============================================================================
# Initialize FastMCP Server
# ============================================================================

server = FastMCP(
    name="Sherpa MCP Server",
    instructions="A remote MCP server providing personal assistant capabilities with secure Auth0 authentication",
    version="1.0.0",
    auth=auth  # None if not configured, Auth0Provider if configured
)

# ============================================================================
# MCP Tools
# ============================================================================

@server.tool(
    name="test_connection",
    description="Test the connection to the MCP server and get server status"
)
async def test_connection(ctx: Context) -> str:
    """Test the connection to the server.

    Returns:
        A confirmation message with server timestamp
    """
    await ctx.info("Testing connection to Sherpa MCP Server...")
    timestamp = datetime.datetime.now().isoformat()
    auth_status = "authenticated" if auth0_enabled else "no authentication"
    return f"✓ Connection successful!\nServer time: {timestamp}\nAuth status: {auth_status}"

@server.tool(
    name="echo",
    description="Echo back a message with optional formatting"
)
async def echo_tool(
    message: str,
    uppercase: bool = False,
    prefix: str = "",
    ctx: Context = None
) -> str:
    """Echo back a message with optional formatting.

    Args:
        message: The message to echo
        uppercase: Convert to uppercase (default: False)
        prefix: Optional prefix to add
        ctx: FastMCP context

    Returns:
        The formatted message
    """
    if ctx:
        await ctx.info(f"Echoing message: {message[:50]}...")

    result = message
    if uppercase:
        result = result.upper()
    if prefix:
        result = f"{prefix}: {result}"

    return result

@server.tool(
    name="get_server_time",
    description="Get the current server time in ISO format"
)
def get_server_time() -> dict:
    """Get the current server time.

    Returns:
        Dictionary with timestamp and timezone info
    """
    now = datetime.datetime.now()
    return {
        "timestamp": now.isoformat(),
        "utc_timestamp": datetime.datetime.utcnow().isoformat(),
        "timezone": "local"
    }


# ============================================================================
# Google Calendar Tools
# ============================================================================

@server.tool(
    name="calendar_list_calendars",
    description="List all Google Calendars accessible to the user"
)
async def calendar_list_calendars(ctx: Context) -> dict:
    """List all calendars the user has access to.

    Returns:
        Dictionary with list of calendars
    """
    if not is_calendar_configured():
        return {
            "error": "Google Calendar not configured",
            "message": "Please set up Google Calendar credentials. See .env.example for instructions."
        }

    try:
        await ctx.info("Fetching calendar list...")
        client = get_calendar_client()
        calendars = client.list_calendars()
        return {
            "calendars": calendars,
            "count": len(calendars)
        }
    except Exception as e:
        logger.error(f"Failed to list calendars: {e}")
        return {"error": str(e)}


@server.tool(
    name="calendar_list_events",
    description="List upcoming events from Google Calendar"
)
async def calendar_list_events(
    calendar_id: str = "primary",
    max_results: int = 10,
    days_ahead: int = 7,
    query: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """List upcoming events from a calendar.

    Args:
        calendar_id: Calendar ID (default: "primary" for main calendar)
        max_results: Maximum number of events to return (default: 10)
        days_ahead: Number of days ahead to look (default: 7)
        query: Optional search query to filter events

    Returns:
        Dictionary with list of events
    """
    if not is_calendar_configured():
        return {
            "error": "Google Calendar not configured",
            "message": "Please set up Google Calendar credentials. See .env.example for instructions."
        }

    try:
        if ctx:
            await ctx.info(f"Fetching events from calendar: {calendar_id}")

        client = get_calendar_client()
        time_min = datetime.datetime.utcnow()
        time_max = time_min + datetime.timedelta(days=days_ahead)

        events = client.list_events(
            calendar_id=calendar_id,
            max_results=max_results,
            time_min=time_min,
            time_max=time_max,
            query=query
        )

        return {
            "events": events,
            "count": len(events),
            "calendar_id": calendar_id,
            "time_range": {
                "from": time_min.isoformat() + "Z",
                "to": time_max.isoformat() + "Z"
            }
        }
    except Exception as e:
        logger.error(f"Failed to list events: {e}")
        return {"error": str(e)}


@server.tool(
    name="calendar_get_event",
    description="Get details of a specific calendar event"
)
async def calendar_get_event(
    event_id: str,
    calendar_id: str = "primary",
    ctx: Context = None
) -> dict:
    """Get a specific event by ID.

    Args:
        event_id: The event ID
        calendar_id: Calendar ID (default: "primary")

    Returns:
        Dictionary with event details
    """
    if not is_calendar_configured():
        return {
            "error": "Google Calendar not configured",
            "message": "Please set up Google Calendar credentials. See .env.example for instructions."
        }

    try:
        if ctx:
            await ctx.info(f"Fetching event: {event_id}")

        client = get_calendar_client()
        event = client.get_event(event_id=event_id, calendar_id=calendar_id)
        return {"event": event}
    except Exception as e:
        logger.error(f"Failed to get event: {e}")
        return {"error": str(e)}


@server.tool(
    name="calendar_create_event",
    description="Create a new event in Google Calendar"
)
async def calendar_create_event(
    summary: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary",
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[str] = None,
    time_zone: str = "UTC",
    all_day: bool = False,
    ctx: Context = None
) -> dict:
    """Create a new calendar event.

    Args:
        summary: Event title
        start_time: Start time in ISO format (e.g., "2024-01-15T10:00:00")
                   For all-day events, use date format: "2024-01-15"
        end_time: End time in ISO format
        calendar_id: Calendar ID (default: "primary")
        description: Event description (optional)
        location: Event location (optional)
        attendees: Comma-separated list of attendee emails (optional)
        time_zone: Time zone (default: "UTC")
        all_day: Whether this is an all-day event (default: False)

    Returns:
        Dictionary with created event details
    """
    if not is_calendar_configured():
        return {
            "error": "Google Calendar not configured",
            "message": "Please set up Google Calendar credentials. See .env.example for instructions."
        }

    try:
        if ctx:
            await ctx.info(f"Creating event: {summary}")

        client = get_calendar_client()

        # Parse times
        if all_day:
            start_dt = datetime.datetime.strptime(start_time[:10], "%Y-%m-%d")
            end_dt = datetime.datetime.strptime(end_time[:10], "%Y-%m-%d")
        else:
            start_dt = datetime.datetime.fromisoformat(start_time.replace("Z", ""))
            end_dt = datetime.datetime.fromisoformat(end_time.replace("Z", ""))

        # Parse attendees
        attendee_list = None
        if attendees:
            attendee_list = [email.strip() for email in attendees.split(",")]

        event = client.create_event(
            summary=summary,
            start_time=start_dt,
            end_time=end_dt,
            calendar_id=calendar_id,
            description=description,
            location=location,
            attendees=attendee_list,
            time_zone=time_zone,
            all_day=all_day
        )

        return {
            "status": "created",
            "event": event
        }
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        return {"error": str(e)}


@server.tool(
    name="calendar_quick_add",
    description="Create a calendar event using natural language"
)
async def calendar_quick_add(
    text: str,
    calendar_id: str = "primary",
    ctx: Context = None
) -> dict:
    """Create an event using natural language description.

    Google's API will parse the text and extract date/time information.

    Args:
        text: Natural language event description
              (e.g., "Meeting with John tomorrow at 3pm for 1 hour")
        calendar_id: Calendar ID (default: "primary")

    Returns:
        Dictionary with created event details
    """
    if not is_calendar_configured():
        return {
            "error": "Google Calendar not configured",
            "message": "Please set up Google Calendar credentials. See .env.example for instructions."
        }

    try:
        if ctx:
            await ctx.info(f"Quick adding event: {text}")

        client = get_calendar_client()
        event = client.quick_add_event(text=text, calendar_id=calendar_id)

        return {
            "status": "created",
            "event": event
        }
    except Exception as e:
        logger.error(f"Failed to quick add event: {e}")
        return {"error": str(e)}


@server.tool(
    name="calendar_update_event",
    description="Update an existing calendar event"
)
async def calendar_update_event(
    event_id: str,
    calendar_id: str = "primary",
    summary: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    time_zone: str = "UTC",
    ctx: Context = None
) -> dict:
    """Update an existing calendar event.

    Only provided fields will be updated.

    Args:
        event_id: The event ID to update
        calendar_id: Calendar ID (default: "primary")
        summary: New event title (optional)
        start_time: New start time in ISO format (optional)
        end_time: New end time in ISO format (optional)
        description: New description (optional)
        location: New location (optional)
        time_zone: Time zone for new times (default: "UTC")

    Returns:
        Dictionary with updated event details
    """
    if not is_calendar_configured():
        return {
            "error": "Google Calendar not configured",
            "message": "Please set up Google Calendar credentials. See .env.example for instructions."
        }

    try:
        if ctx:
            await ctx.info(f"Updating event: {event_id}")

        client = get_calendar_client()

        # Parse times if provided
        start_dt = None
        end_dt = None
        if start_time:
            start_dt = datetime.datetime.fromisoformat(start_time.replace("Z", ""))
        if end_time:
            end_dt = datetime.datetime.fromisoformat(end_time.replace("Z", ""))

        event = client.update_event(
            event_id=event_id,
            calendar_id=calendar_id,
            summary=summary,
            start_time=start_dt,
            end_time=end_dt,
            description=description,
            location=location,
            time_zone=time_zone
        )

        return {
            "status": "updated",
            "event": event
        }
    except Exception as e:
        logger.error(f"Failed to update event: {e}")
        return {"error": str(e)}


@server.tool(
    name="calendar_delete_event",
    description="Delete a calendar event"
)
async def calendar_delete_event(
    event_id: str,
    calendar_id: str = "primary",
    ctx: Context = None
) -> dict:
    """Delete a calendar event.

    Args:
        event_id: The event ID to delete
        calendar_id: Calendar ID (default: "primary")

    Returns:
        Dictionary with deletion status
    """
    if not is_calendar_configured():
        return {
            "error": "Google Calendar not configured",
            "message": "Please set up Google Calendar credentials. See .env.example for instructions."
        }

    try:
        if ctx:
            await ctx.info(f"Deleting event: {event_id}")

        client = get_calendar_client()
        client.delete_event(event_id=event_id, calendar_id=calendar_id)

        return {
            "status": "deleted",
            "event_id": event_id,
            "calendar_id": calendar_id
        }
    except Exception as e:
        logger.error(f"Failed to delete event: {e}")
        return {"error": str(e)}


# ============================================================================
# TickTick Tools
# ============================================================================

@server.tool(
    name="ticktick_list_projects",
    description="List all TickTick projects (task lists)"
)
async def ticktick_list_projects(ctx: Context) -> dict:
    """List all projects the user has access to.

    Returns:
        Dictionary with list of projects
    """
    if not is_ticktick_configured():
        return {
            "error": "TickTick not configured",
            "message": "Please set up TickTick credentials. See .env.example for instructions."
        }

    try:
        await ctx.info("Fetching TickTick projects...")
        client = get_ticktick_client()
        projects = client.list_projects()
        return {
            "projects": projects,
            "count": len(projects)
        }
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return {"error": str(e)}


@server.tool(
    name="ticktick_get_project",
    description="Get a specific TickTick project with all its tasks"
)
async def ticktick_get_project(
    project_id: str,
    include_tasks: bool = True,
    ctx: Context = None
) -> dict:
    """Get a project by ID, optionally with all its tasks.

    Args:
        project_id: The project ID
        include_tasks: Whether to include tasks (default: True)

    Returns:
        Dictionary with project details and tasks
    """
    if not is_ticktick_configured():
        return {
            "error": "TickTick not configured",
            "message": "Please set up TickTick credentials. See .env.example for instructions."
        }

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


@server.tool(
    name="ticktick_create_project",
    description="Create a new TickTick project (task list)"
)
async def ticktick_create_project(
    name: str,
    color: Optional[str] = None,
    view_mode: str = "list",
    ctx: Context = None
) -> dict:
    """Create a new project.

    Args:
        name: Project name
        color: Project color in hex format (e.g., "#F18181")
        view_mode: View mode - "list", "kanban", or "timeline" (default: "list")

    Returns:
        Dictionary with created project details
    """
    if not is_ticktick_configured():
        return {
            "error": "TickTick not configured",
            "message": "Please set up TickTick credentials. See .env.example for instructions."
        }

    try:
        if ctx:
            await ctx.info(f"Creating project: {name}")

        client = get_ticktick_client()
        project = client.create_project(
            name=name,
            color=color,
            view_mode=view_mode
        )
        return {
            "status": "created",
            "project": project
        }
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        return {"error": str(e)}


@server.tool(
    name="ticktick_delete_project",
    description="Delete a TickTick project"
)
async def ticktick_delete_project(
    project_id: str,
    ctx: Context = None
) -> dict:
    """Delete a project.

    Args:
        project_id: The project ID to delete

    Returns:
        Dictionary with deletion status
    """
    if not is_ticktick_configured():
        return {
            "error": "TickTick not configured",
            "message": "Please set up TickTick credentials. See .env.example for instructions."
        }

    try:
        if ctx:
            await ctx.info(f"Deleting project: {project_id}")

        client = get_ticktick_client()
        client.delete_project(project_id)
        return {
            "status": "deleted",
            "project_id": project_id
        }
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        return {"error": str(e)}


@server.tool(
    name="ticktick_get_task",
    description="Get a specific TickTick task"
)
async def ticktick_get_task(
    project_id: str,
    task_id: str,
    ctx: Context = None
) -> dict:
    """Get a specific task by ID.

    Args:
        project_id: The project ID containing the task
        task_id: The task ID

    Returns:
        Dictionary with task details
    """
    if not is_ticktick_configured():
        return {
            "error": "TickTick not configured",
            "message": "Please set up TickTick credentials. See .env.example for instructions."
        }

    try:
        if ctx:
            await ctx.info(f"Fetching task: {task_id}")

        client = get_ticktick_client()
        task = client.get_task(project_id=project_id, task_id=task_id)
        return {"task": task}
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        return {"error": str(e)}


@server.tool(
    name="ticktick_create_task",
    description="Create a new task in TickTick"
)
async def ticktick_create_task(
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
    """Create a new task.

    Args:
        title: Task title
        project_id: Project ID to add the task to
        content: Task content/notes (optional)
        desc: Task description for checklist (optional)
        start_date: Start date in ISO format (e.g., "2024-01-15T10:00:00") (optional)
        due_date: Due date in ISO format (optional)
        time_zone: Time zone (default: "America/Los_Angeles")
        is_all_day: Whether this is an all-day task (default: False)
        priority: Priority level - 0 (None), 1 (Low), 3 (Medium), 5 (High) (default: 0)

    Returns:
        Dictionary with created task details
    """
    if not is_ticktick_configured():
        return {
            "error": "TickTick not configured",
            "message": "Please set up TickTick credentials. See .env.example for instructions."
        }

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
        return {
            "status": "created",
            "task": task
        }
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        return {"error": str(e)}


@server.tool(
    name="ticktick_update_task",
    description="Update an existing TickTick task"
)
async def ticktick_update_task(
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
    """Update an existing task.

    Only provided fields will be updated.

    Args:
        task_id: The task ID to update
        project_id: The project ID containing the task
        title: New task title (optional)
        content: New content/notes (optional)
        desc: New description (optional)
        start_date: New start date in ISO format (optional)
        due_date: New due date in ISO format (optional)
        time_zone: New time zone (optional)
        is_all_day: Whether this is an all-day task (optional)
        priority: New priority level (optional)

    Returns:
        Dictionary with updated task details
    """
    if not is_ticktick_configured():
        return {
            "error": "TickTick not configured",
            "message": "Please set up TickTick credentials. See .env.example for instructions."
        }

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
        return {
            "status": "updated",
            "task": task
        }
    except Exception as e:
        logger.error(f"Failed to update task: {e}")
        return {"error": str(e)}


@server.tool(
    name="ticktick_complete_task",
    description="Mark a TickTick task as complete"
)
async def ticktick_complete_task(
    project_id: str,
    task_id: str,
    ctx: Context = None
) -> dict:
    """Mark a task as complete.

    Args:
        project_id: The project ID containing the task
        task_id: The task ID to complete

    Returns:
        Dictionary with completion status
    """
    if not is_ticktick_configured():
        return {
            "error": "TickTick not configured",
            "message": "Please set up TickTick credentials. See .env.example for instructions."
        }

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


@server.tool(
    name="ticktick_delete_task",
    description="Delete a TickTick task"
)
async def ticktick_delete_task(
    project_id: str,
    task_id: str,
    ctx: Context = None
) -> dict:
    """Delete a task.

    Args:
        project_id: The project ID containing the task
        task_id: The task ID to delete

    Returns:
        Dictionary with deletion status
    """
    if not is_ticktick_configured():
        return {
            "error": "TickTick not configured",
            "message": "Please set up TickTick credentials. See .env.example for instructions."
        }

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


# ============================================================================
# Custom HTTP Endpoints
# ============================================================================

@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring and load balancers.

    Returns:
        JSON response with health status
    """
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "sherpa-mcp-server",
        "version": "1.0.0",
        "auth_enabled": auth0_enabled,
        "google_calendar_enabled": is_calendar_configured(),
        "ticktick_enabled": is_ticktick_configured()
    })

@server.custom_route("/info", methods=["GET"])
async def server_info(request: Request) -> JSONResponse:
    """Server information endpoint.

    Returns:
        JSON response with server details
    """
    return JSONResponse({
        "name": "Sherpa MCP Server",
        "version": "1.0.0",
        "description": "Remote MCP server with personal assistant capabilities",
        "mcp_protocol": "Model Context Protocol",
        "transport": "streamable-http",
        "authentication": {
            "enabled": auth0_enabled,
            "provider": "Auth0" if auth0_enabled else None
        },
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "mcp": "/mcp",
            "oauth_metadata": "/.well-known/oauth-authorization-server" if auth0_enabled else None
        },
        "tools": [
            "test_connection",
            "echo",
            "get_server_time",
            "calendar_list_calendars",
            "calendar_list_events",
            "calendar_get_event",
            "calendar_create_event",
            "calendar_quick_add",
            "calendar_update_event",
            "calendar_delete_event",
            "ticktick_list_projects",
            "ticktick_get_project",
            "ticktick_create_project",
            "ticktick_delete_project",
            "ticktick_get_task",
            "ticktick_create_task",
            "ticktick_update_task",
            "ticktick_complete_task",
            "ticktick_delete_task"
        ],
        "integrations": {
            "google_calendar": is_calendar_configured(),
            "ticktick": is_ticktick_configured()
        },
        "timestamp": datetime.datetime.now().isoformat()
    })

@server.custom_route("/", methods=["GET"])
async def root(request: Request) -> JSONResponse:
    """Root endpoint with basic information.

    Returns:
        JSON response with welcome message
    """
    return JSONResponse({
        "message": "Welcome to Sherpa MCP Server",
        "version": "1.0.0",
        "description": "Your personal assistant MCP server",
        "auth_enabled": auth0_enabled,
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "mcp": "/mcp"
        },
        "documentation": "See README.md for setup instructions"
    })

# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Sherpa MCP Server v1.0.0")
    logger.info("=" * 60)
    logger.info(f"Authentication: {'Enabled (Auth0)' if auth0_enabled else 'Disabled'}")
    logger.info(f"Google Calendar: {'Enabled' if is_calendar_configured() else 'Disabled'}")
    logger.info(f"TickTick: {'Enabled' if is_ticktick_configured() else 'Disabled'}")
    logger.info(f"Server URL: {os.getenv('SERVER_BASE_URL', 'http://localhost:8000')}")
    logger.info("=" * 60)

    # Run the server with streamable-http transport
    # Railway uses PORT, but we also support SERVER_PORT for flexibility
    port = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8000")))
    host = os.getenv("SERVER_HOST", "0.0.0.0")

    logger.info(f"Starting server on {host}:{port}")

    server.run(
        transport="streamable-http",
        host=host,
        port=port,
        show_banner=True
    )
