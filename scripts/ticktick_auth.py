#!/usr/bin/env python3
"""
Standalone TickTick authentication script.

Generates the TICKTICK_ACCESS_TOKEN environment variable value using OAuth2 flow.

Usage:
    export TICKTICK_CLIENT_ID='your-client-id'
    export TICKTICK_CLIENT_SECRET='your-client-secret'
    python scripts/ticktick_auth.py
"""

import base64
import os
import secrets
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx

TICKTICK_AUTH_URL = "https://ticktick.com/oauth/authorize"
TICKTICK_TOKEN_URL = "https://ticktick.com/oauth/token"
REDIRECT_PORT = 8765
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
SCOPES = "tasks:read tasks:write"

SETUP_INSTRUCTIONS = """
Error: TICKTICK_CLIENT_ID and TICKTICK_CLIENT_SECRET must be set.

Steps:
1. Go to https://developer.ticktick.com/manage
2. Create an application
3. Set redirect URI to: http://localhost:8765/callback
4. Copy your Client ID and Client Secret
5. Set environment variables:

   export TICKTICK_CLIENT_ID='your-client-id'
   export TICKTICK_CLIENT_SECRET='your-client-secret'

Then run this script again.
"""

SUCCESS_HTML = b"""
<!DOCTYPE html>
<html>
<head><title>TickTick Auth</title></head>
<body style="font-family: system-ui; padding: 40px; text-align: center;">
    <h1>Authentication Successful!</h1>
    <p>You can close this window and return to the terminal.</p>
</body>
</html>
"""


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle the OAuth callback from TickTick."""

    def log_message(self, format, *args):
        """Suppress server logs."""
        pass

    def do_GET(self):
        """Handle GET request with authorization code."""
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        query_params = urllib.parse.parse_qs(parsed.query)

        if "code" in query_params:
            self.server.auth_code = query_params["code"][0]
            self.server.auth_state = query_params.get("state", [None])[0]
            self._send_html(200, SUCCESS_HTML)
        else:
            error = query_params.get("error", ["Unknown error"])[0]
            self.server.auth_error = error
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>TickTick Auth Error</title></head>
            <body style="font-family: system-ui; padding: 40px; text-align: center;">
                <h1>Authentication Failed</h1>
                <p>Error: {error}</p>
            </body>
            </html>
            """.encode()
            self._send_html(400, error_html)

    def _send_html(self, status: int, content: bytes):
        """Send an HTML response."""
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(content)


def get_authorization_code(client_id: str) -> tuple[str, str]:
    """Start OAuth flow and get authorization code."""
    state = secrets.token_urlsafe(16)

    params = {
        "client_id": client_id,
        "scope": SCOPES,
        "state": state,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code"
    }
    auth_url = f"{TICKTICK_AUTH_URL}?{urllib.parse.urlencode(params)}"

    print("Opening browser for TickTick OAuth...")
    print(f"\nIf browser doesn't open, visit:\n{auth_url}\n")

    server = HTTPServer(("localhost", REDIRECT_PORT), OAuthCallbackHandler)
    server.auth_code = None
    server.auth_state = None
    server.auth_error = None

    webbrowser.open(auth_url)

    print("Waiting for authorization...")
    while server.auth_code is None and server.auth_error is None:
        server.handle_request()

    if server.auth_error:
        raise Exception(f"Authorization failed: {server.auth_error}")

    if server.auth_state != state:
        raise Exception("State mismatch - possible CSRF attack")

    return server.auth_code, state


def exchange_code_for_token(client_id: str, client_secret: str, code: str) -> dict:
    """Exchange authorization code for access token."""
    auth_bytes = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_bytes}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "code": code,
        "grant_type": "authorization_code",
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI
    }

    with httpx.Client() as client:
        response = client.post(TICKTICK_TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json()


def main():
    client_id = os.getenv("TICKTICK_CLIENT_ID")
    client_secret = os.getenv("TICKTICK_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(SETUP_INSTRUCTIONS)
        sys.exit(1)

    try:
        code, _ = get_authorization_code(client_id)
        print("\nReceived authorization code")

        print("Exchanging code for access token...")
        token_data = exchange_code_for_token(client_id, client_secret, code)

        access_token = token_data.get("access_token")
        if not access_token:
            print(f"Error: No access token in response: {token_data}")
            sys.exit(1)

        separator = "=" * 60
        print(f"\n{separator}")
        print("Authentication successful!")
        print(separator)
        print("\nSet this environment variable for production:\n")
        print(f"TICKTICK_ACCESS_TOKEN='{access_token}'")
        print(f"\n{separator}")

    except Exception as e:
        print(f"\nError during authentication: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
