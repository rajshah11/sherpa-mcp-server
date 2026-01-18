"""
Google Calendar Integration Module

This module handles Google Calendar API authentication and provides
helper functions for calendar operations.

Authentication is done via environment variables:
- GOOGLE_CALENDAR_CREDENTIALS_JSON: OAuth client credentials (from Google Cloud Console)
- GOOGLE_CALENDAR_TOKEN_JSON: OAuth token (generated after first authentication)
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarClient:
    """Client for interacting with Google Calendar API.

    Uses environment variables for credentials:
    - GOOGLE_CALENDAR_CREDENTIALS_JSON: OAuth client config JSON
    - GOOGLE_CALENDAR_TOKEN_JSON: OAuth token JSON
    """

    def __init__(self):
        """Initialize the Google Calendar client."""
        self._credentials_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")
        self._token_json = os.getenv("GOOGLE_CALENDAR_TOKEN_JSON")
        self._service = None
        self._creds = None

    def _get_credentials(self) -> Optional[Credentials]:
        """Get or refresh Google API credentials from environment variable.

        Returns:
            Valid credentials or None if not configured
        """
        if not self._token_json:
            logger.warning("GOOGLE_CALENDAR_TOKEN_JSON not set")
            return None

        try:
            token_data = json.loads(self._token_json)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            logger.info("Loaded credentials from GOOGLE_CALENDAR_TOKEN_JSON")
        except Exception as e:
            logger.error(f"Failed to parse GOOGLE_CALENDAR_TOKEN_JSON: {e}")
            return None

        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Refreshed expired credentials")
                # Log new token so user can update env var
                logger.warning(
                    "Token was refreshed. Update GOOGLE_CALENDAR_TOKEN_JSON "
                    "with the new value below to persist:"
                )
                print(f"\nGOOGLE_CALENDAR_TOKEN_JSON='{creds.to_json()}'\n")
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                return None

        return creds

    def authenticate(self, headless: bool = False) -> bool:
        """Authenticate with Google Calendar API.

        Args:
            headless: If True, don't attempt browser-based auth

        Returns:
            True if authentication successful, False otherwise
        """
        self._creds = self._get_credentials()

        if self._creds and self._creds.valid:
            logger.info("Using valid credentials from environment")
            return True

        if headless:
            logger.error(
                "No valid token found. Set GOOGLE_CALENDAR_TOKEN_JSON env var. "
                "Run locally with GOOGLE_CALENDAR_CREDENTIALS_JSON to generate token."
            )
            return False

        # Interactive authentication requires credentials
        if not self._credentials_json:
            logger.error(
                "GOOGLE_CALENDAR_CREDENTIALS_JSON not set. "
                "Download OAuth credentials from Google Cloud Console."
            )
            return False

        try:
            credentials_info = json.loads(self._credentials_json)
            flow = InstalledAppFlow.from_client_config(credentials_info, SCOPES)
            self._creds = flow.run_local_server(port=0)

            # Print token for env var setup
            token_json = self._creds.to_json()
            logger.info("Authentication successful!")
            print("\n" + "=" * 60)
            print("Set this environment variable for production:")
            print("=" * 60)
            print(f"\nGOOGLE_CALENDAR_TOKEN_JSON='{token_json}'\n")
            print("=" * 60 + "\n")

            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def get_service(self):
        """Get the Google Calendar API service.

        Returns:
            Google Calendar API service object

        Raises:
            RuntimeError: If not authenticated
        """
        if not self._creds or not self._creds.valid:
            if not self.authenticate(headless=True):
                raise RuntimeError(
                    "Google Calendar not authenticated. "
                    "Set GOOGLE_CALENDAR_TOKEN_JSON environment variable."
                )

        if not self._service:
            self._service = build("calendar", "v3", credentials=self._creds)

        return self._service

    def is_authenticated(self) -> bool:
        """Check if the client is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        if self._creds and self._creds.valid:
            return True

        creds = self._get_credentials()
        return creds is not None and creds.valid

    # ========================================================================
    # Calendar Operations
    # ========================================================================

    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars accessible to the user."""
        try:
            service = self.get_service()
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])
            return [
                {
                    "id": cal.get("id"),
                    "summary": cal.get("summary"),
                    "description": cal.get("description"),
                    "primary": cal.get("primary", False),
                    "access_role": cal.get("accessRole"),
                    "background_color": cal.get("backgroundColor"),
                    "time_zone": cal.get("timeZone")
                }
                for cal in calendars
            ]
        except HttpError as e:
            logger.error(f"Failed to list calendars: {e}")
            raise

    def list_events(
        self,
        calendar_id: str = "primary",
        max_results: int = 10,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        query: Optional[str] = None,
        single_events: bool = True,
        order_by: str = "startTime"
    ) -> List[Dict[str, Any]]:
        """List events from a calendar."""
        try:
            service = self.get_service()

            if time_min is None:
                time_min = datetime.utcnow()

            params = {
                "calendarId": calendar_id,
                "maxResults": max_results,
                "timeMin": time_min.isoformat() + "Z",
                "singleEvents": single_events,
                "orderBy": order_by
            }

            if time_max:
                params["timeMax"] = time_max.isoformat() + "Z"

            if query:
                params["q"] = query

            events_result = service.events().list(**params).execute()
            events = events_result.get("items", [])

            return [self._format_event(event) for event in events]
        except HttpError as e:
            logger.error(f"Failed to list events: {e}")
            raise

    def get_event(self, event_id: str, calendar_id: str = "primary") -> Dict[str, Any]:
        """Get a specific event by ID."""
        try:
            service = self.get_service()
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return self._format_event(event)
        except HttpError as e:
            logger.error(f"Failed to get event {event_id}: {e}")
            raise

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary",
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        time_zone: Optional[str] = None,
        reminders: Optional[Dict[str, Any]] = None,
        all_day: bool = False
    ) -> Dict[str, Any]:
        """Create a new calendar event."""
        try:
            service = self.get_service()

            if all_day:
                event_body = {
                    "summary": summary,
                    "start": {"date": start_time.strftime("%Y-%m-%d")},
                    "end": {"date": end_time.strftime("%Y-%m-%d")}
                }
            else:
                event_body = {
                    "summary": summary,
                    "start": {
                        "dateTime": start_time.isoformat(),
                        "timeZone": time_zone or "UTC"
                    },
                    "end": {
                        "dateTime": end_time.isoformat(),
                        "timeZone": time_zone or "UTC"
                    }
                }

            if description:
                event_body["description"] = description
            if location:
                event_body["location"] = location
            if attendees:
                event_body["attendees"] = [{"email": email} for email in attendees]
            if reminders:
                event_body["reminders"] = reminders

            event = service.events().insert(
                calendarId=calendar_id,
                body=event_body
            ).execute()

            logger.info(f"Created event: {event.get('id')}")
            return self._format_event(event)
        except HttpError as e:
            logger.error(f"Failed to create event: {e}")
            raise

    def update_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        time_zone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing calendar event."""
        try:
            service = self.get_service()

            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            if summary is not None:
                event["summary"] = summary
            if description is not None:
                event["description"] = description
            if location is not None:
                event["location"] = location

            if start_time is not None:
                if "date" in event.get("start", {}):
                    event["start"] = {"date": start_time.strftime("%Y-%m-%d")}
                else:
                    event["start"] = {
                        "dateTime": start_time.isoformat(),
                        "timeZone": time_zone or event.get("start", {}).get("timeZone", "UTC")
                    }

            if end_time is not None:
                if "date" in event.get("end", {}):
                    event["end"] = {"date": end_time.strftime("%Y-%m-%d")}
                else:
                    event["end"] = {
                        "dateTime": end_time.isoformat(),
                        "timeZone": time_zone or event.get("end", {}).get("timeZone", "UTC")
                    }

            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()

            logger.info(f"Updated event: {event_id}")
            return self._format_event(updated_event)
        except HttpError as e:
            logger.error(f"Failed to update event {event_id}: {e}")
            raise

    def delete_event(self, event_id: str, calendar_id: str = "primary") -> bool:
        """Delete a calendar event."""
        try:
            service = self.get_service()
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            logger.info(f"Deleted event: {event_id}")
            return True
        except HttpError as e:
            logger.error(f"Failed to delete event {event_id}: {e}")
            raise

    def quick_add_event(self, text: str, calendar_id: str = "primary") -> Dict[str, Any]:
        """Create an event using natural language."""
        try:
            service = self.get_service()
            event = service.events().quickAdd(
                calendarId=calendar_id,
                text=text
            ).execute()
            logger.info(f"Quick added event: {event.get('id')}")
            return self._format_event(event)
        except HttpError as e:
            logger.error(f"Failed to quick add event: {e}")
            raise

    def _format_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format a raw event response into a clean dictionary."""
        start = event.get("start", {})
        end = event.get("end", {})

        return {
            "id": event.get("id"),
            "summary": event.get("summary", "(No title)"),
            "description": event.get("description"),
            "location": event.get("location"),
            "start": start.get("dateTime") or start.get("date"),
            "end": end.get("dateTime") or end.get("date"),
            "start_timezone": start.get("timeZone"),
            "end_timezone": end.get("timeZone"),
            "all_day": "date" in start,
            "status": event.get("status"),
            "html_link": event.get("htmlLink"),
            "created": event.get("created"),
            "updated": event.get("updated"),
            "creator": event.get("creator", {}).get("email"),
            "organizer": event.get("organizer", {}).get("email"),
            "attendees": [
                {
                    "email": att.get("email"),
                    "response_status": att.get("responseStatus"),
                    "organizer": att.get("organizer", False)
                }
                for att in event.get("attendees", [])
            ],
            "recurring_event_id": event.get("recurringEventId"),
            "recurrence": event.get("recurrence")
        }


# Global client instance
_calendar_client: Optional[GoogleCalendarClient] = None


def get_calendar_client() -> GoogleCalendarClient:
    """Get or create the global Google Calendar client."""
    global _calendar_client
    if _calendar_client is None:
        _calendar_client = GoogleCalendarClient()
    return _calendar_client


def is_calendar_configured() -> bool:
    """Check if Google Calendar is configured via environment variables."""
    return bool(os.getenv("GOOGLE_CALENDAR_TOKEN_JSON"))
