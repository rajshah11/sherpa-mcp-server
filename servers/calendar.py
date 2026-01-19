"""
Google Calendar MCP Server - Calendar management tools.
"""

import datetime
import logging
from typing import Optional
from fastmcp import FastMCP, Context

from google_calendar import get_calendar_client, is_calendar_configured

logger = logging.getLogger(__name__)

calendar_server = FastMCP(name="Google Calendar")


def _check_configured() -> Optional[dict]:
    """Return error dict if not configured, None if OK."""
    if not is_calendar_configured():
        return {
            "error": "Google Calendar not configured",
            "message": "Please set up Google Calendar credentials. See GOOGLE_CALENDAR_SETUP.md"
        }
    return None


@calendar_server.tool(
    name="calendar_list_calendars",
    description="List all Google Calendars accessible to the user"
)
async def list_calendars(ctx: Context) -> dict:
    """List all calendars the user has access to."""
    if err := _check_configured():
        return err

    try:
        await ctx.info("Fetching calendar list...")
        client = get_calendar_client()
        calendars = client.list_calendars()
        return {"calendars": calendars, "count": len(calendars)}
    except Exception as e:
        logger.error(f"Failed to list calendars: {e}")
        return {"error": str(e)}


@calendar_server.tool(
    name="calendar_list_events",
    description="List upcoming events from Google Calendar"
)
async def list_events(
    calendar_id: str = "primary",
    max_results: int = 10,
    days_ahead: int = 7,
    query: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """List upcoming events from a calendar."""
    if err := _check_configured():
        return err

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


@calendar_server.tool(
    name="calendar_get_event",
    description="Get details of a specific calendar event"
)
async def get_event(
    event_id: str,
    calendar_id: str = "primary",
    ctx: Context = None
) -> dict:
    """Get a specific event by ID."""
    if err := _check_configured():
        return err

    try:
        if ctx:
            await ctx.info(f"Fetching event: {event_id}")

        client = get_calendar_client()
        event = client.get_event(event_id=event_id, calendar_id=calendar_id)
        return {"event": event}
    except Exception as e:
        logger.error(f"Failed to get event: {e}")
        return {"error": str(e)}


@calendar_server.tool(
    name="calendar_create_event",
    description="Create a new event in Google Calendar"
)
async def create_event(
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
    """Create a new calendar event."""
    if err := _check_configured():
        return err

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

        return {"status": "created", "event": event}
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        return {"error": str(e)}


@calendar_server.tool(
    name="calendar_quick_add",
    description="Create a calendar event using natural language"
)
async def quick_add(
    text: str,
    calendar_id: str = "primary",
    ctx: Context = None
) -> dict:
    """Create an event using natural language description."""
    if err := _check_configured():
        return err

    try:
        if ctx:
            await ctx.info(f"Quick adding event: {text}")

        client = get_calendar_client()
        event = client.quick_add_event(text=text, calendar_id=calendar_id)

        return {"status": "created", "event": event}
    except Exception as e:
        logger.error(f"Failed to quick add event: {e}")
        return {"error": str(e)}


@calendar_server.tool(
    name="calendar_update_event",
    description="Update an existing calendar event"
)
async def update_event(
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
    """Update an existing calendar event."""
    if err := _check_configured():
        return err

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

        return {"status": "updated", "event": event}
    except Exception as e:
        logger.error(f"Failed to update event: {e}")
        return {"error": str(e)}


@calendar_server.tool(
    name="calendar_delete_event",
    description="Delete a calendar event"
)
async def delete_event(
    event_id: str,
    calendar_id: str = "primary",
    ctx: Context = None
) -> dict:
    """Delete a calendar event."""
    if err := _check_configured():
        return err

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
