#!/usr/bin/env python3
"""
Standalone Google Calendar authentication script.

Generates the GOOGLE_CALENDAR_TOKEN_JSON environment variable value
without needing to run the full server.

Usage:
    export GOOGLE_CALENDAR_CREDENTIALS_JSON='<your credentials json>'
    python scripts/google_calendar_auth.py
"""

import os
import sys
import json

def main():
    # Check for credentials
    credentials_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")

    if not credentials_json:
        print("Error: GOOGLE_CALENDAR_CREDENTIALS_JSON environment variable not set.")
        print()
        print("Steps:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create a project and enable Google Calendar API")
        print("3. Create OAuth 2.0 credentials (Desktop app)")
        print("4. Download the JSON file")
        print("5. Set the environment variable:")
        print()
        print("   export GOOGLE_CALENDAR_CREDENTIALS_JSON='<contents of downloaded JSON>'")
        print()
        print("Then run this script again.")
        sys.exit(1)

    # Import Google libraries (only needed if credentials are set)
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Error: Google auth libraries not installed.")
        print("Run: pip install google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    # Parse credentials
    try:
        credentials_info = json.loads(credentials_json)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in GOOGLE_CALENDAR_CREDENTIALS_JSON: {e}")
        sys.exit(1)

    # Run OAuth flow
    print("Opening browser for Google OAuth...")
    print()

    scopes = ["https://www.googleapis.com/auth/calendar"]

    try:
        flow = InstalledAppFlow.from_client_config(credentials_info, scopes)
        creds = flow.run_local_server(port=0)
    except Exception as e:
        print(f"Error during authentication: {e}")
        sys.exit(1)

    # Output the token
    token_json = creds.to_json()

    print()
    print("=" * 60)
    print("Authentication successful!")
    print("=" * 60)
    print()
    print("Set this environment variable for production:")
    print()
    print(f"GOOGLE_CALENDAR_TOKEN_JSON='{token_json}'")
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
