# Google Calendar Setup Guide

This guide walks you through setting up Google Calendar integration for the Sherpa MCP Server.

## Overview

Google Calendar integration uses two environment variables:
- `GOOGLE_CALENDAR_CREDENTIALS_JSON` - OAuth client config (for initial auth)
- `GOOGLE_CALENDAR_TOKEN_JSON` - OAuth token (for production use)

No files need to be persisted - everything is stored in environment variables.

---

## Quick Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Sherpa MCP Server")
3. Select the project

### 2. Enable Calendar API

1. Go to **APIs & Services** > **Library**
2. Search for "Google Calendar API"
3. Click **Enable**

### 3. Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Select **External** user type
3. Fill in required fields:
   - App name: Sherpa MCP Server
   - User support email: Your email
   - Developer contact: Your email
4. Add scope: `https://www.googleapis.com/auth/calendar`
5. Add your email as a test user

### 4. Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Select **Desktop app**
4. Click **Create**
5. Click **Download JSON**

### 5. Set Credentials Environment Variable

Copy the contents of the downloaded JSON file:

```bash
export GOOGLE_CALENDAR_CREDENTIALS_JSON='{"installed":{"client_id":"YOUR_CLIENT_ID.apps.googleusercontent.com","project_id":"your-project","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"YOUR_CLIENT_SECRET","redirect_uris":["http://localhost"]}}'
```

### 6. Generate Token (One-time Local Setup)

Run the server locally to trigger authentication:

```bash
python server.py
```

A browser window will open for Google OAuth. After authorization, the server will print:

```
============================================================
Set this environment variable for production:
============================================================

GOOGLE_CALENDAR_TOKEN_JSON='{"token":"...","refresh_token":"...","token_uri":"...","client_id":"...","client_secret":"...","scopes":["https://www.googleapis.com/auth/calendar"]}'

============================================================
```

### 7. Set Token Environment Variable

Copy the printed `GOOGLE_CALENDAR_TOKEN_JSON` value and set it in your production environment.

For Railway:
1. Go to your project's **Variables** tab
2. Add `GOOGLE_CALENDAR_TOKEN_JSON` with the value from step 6

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CALENDAR_CREDENTIALS_JSON` | For initial auth | OAuth client credentials JSON |
| `GOOGLE_CALENDAR_TOKEN_JSON` | For production | OAuth token JSON (generated after auth) |

---

## Available Tools

Once configured, these MCP tools are available:

| Tool | Description |
|------|-------------|
| `calendar_list_calendars` | List all accessible calendars |
| `calendar_list_events` | List upcoming events |
| `calendar_get_event` | Get event details |
| `calendar_create_event` | Create a new event |
| `calendar_quick_add` | Create event with natural language |
| `calendar_update_event` | Update an existing event |
| `calendar_delete_event` | Delete an event |

---

## Token Refresh

Tokens automatically refresh when expired. If a token is refreshed, the server logs the new token JSON. Update `GOOGLE_CALENDAR_TOKEN_JSON` with the new value to persist it.

---

## Troubleshooting

### "GOOGLE_CALENDAR_TOKEN_JSON not set"

Set the environment variable with a valid token. Run local authentication first if needed.

### "This app isn't verified"

For personal use, click **Advanced** > **Go to [App Name] (unsafe)** during OAuth.

### Token refresh fails

Delete and regenerate the token by running local authentication again.

---

## Resources

- [Google Calendar API](https://developers.google.com/calendar/api)
- [Google Cloud Console](https://console.cloud.google.com/)
