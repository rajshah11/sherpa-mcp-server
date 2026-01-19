#!/usr/bin/env python3
"""
Standalone Google Calendar authentication script.

Generates the GOOGLE_CALENDAR_TOKEN_JSON environment variable value.

Usage:
    export GOOGLE_CALENDAR_CREDENTIALS_JSON='<your credentials json>'
    python scripts/google_calendar_auth.py
"""

import json
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/calendar"]

SETUP_INSTRUCTIONS = """
Error: GOOGLE_CALENDAR_CREDENTIALS_JSON environment variable not set.

Steps:
1. Go to https://console.cloud.google.com
2. Create a project and enable Google Calendar API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download the JSON file
5. Set the environment variable:

   export GOOGLE_CALENDAR_CREDENTIALS_JSON='<contents of downloaded JSON>'

Then run this script again.
"""


def main():
    credentials_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")

    if not credentials_json:
        print(SETUP_INSTRUCTIONS)
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Error: Google auth libraries not installed.")
        print("Run: pip install google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    try:
        credentials_info = json.loads(credentials_json)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in GOOGLE_CALENDAR_CREDENTIALS_JSON: {e}")
        sys.exit(1)

    print("Opening browser for Google OAuth...\n")

    try:
        flow = InstalledAppFlow.from_client_config(credentials_info, SCOPES)
        creds = flow.run_local_server(port=0)
    except Exception as e:
        print(f"Error during authentication: {e}")
        sys.exit(1)

    token_json = creds.to_json()
    separator = "=" * 60

    print(f"\n{separator}")
    print("Authentication successful!")
    print(separator)
    print("\nSet this environment variable for production:\n")
    print(f"GOOGLE_CALENDAR_TOKEN_JSON='{token_json}'")
    print(f"\n{separator}")


if __name__ == "__main__":
    main()
