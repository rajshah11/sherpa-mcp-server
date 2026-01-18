# TickTick Setup Guide

This guide walks you through setting up TickTick integration for the Sherpa MCP Server.

## Overview

TickTick integration uses OAuth2 for authentication. You need:
- `TICKTICK_CLIENT_ID` - Your TickTick app client ID (for auth script)
- `TICKTICK_CLIENT_SECRET` - Your TickTick app client secret (for auth script)
- `TICKTICK_ACCESS_TOKEN` - OAuth access token (for production use)

---

## Quick Setup

### 1. Create TickTick Developer Application

1. Go to [TickTick Developer Center](https://developer.ticktick.com/manage)
2. Sign in with your TickTick account
3. Click **Create App** or **Add Application**
4. Fill in the application details:
   - App Name: Sherpa MCP Server
   - Description: Personal assistant MCP server

### 2. Configure Redirect URI

1. In your app settings, add the redirect URI:
   ```
   http://localhost:8765/callback
   ```
2. Save the settings

### 3. Get Client Credentials

1. Copy your **Client ID**
2. Copy your **Client Secret**

### 4. Generate Access Token

Set your credentials as environment variables and run the auth script:

```bash
export TICKTICK_CLIENT_ID='your-client-id'
export TICKTICK_CLIENT_SECRET='your-client-secret'
python scripts/ticktick_auth.py
```

A browser window will open for TickTick OAuth. After authorization, the script will print:

```
============================================================
Authentication successful!
============================================================

Set this environment variable for production:

TICKTICK_ACCESS_TOKEN='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'

============================================================
```

### 5. Set Access Token Environment Variable

Copy the printed `TICKTICK_ACCESS_TOKEN` value and set it in your production environment.

For Railway:
1. Go to your project's **Variables** tab
2. Add `TICKTICK_ACCESS_TOKEN` with the value from step 4

For local development, add to your `.env` file:
```bash
TICKTICK_ACCESS_TOKEN='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TICKTICK_CLIENT_ID` | For auth script | OAuth client ID |
| `TICKTICK_CLIENT_SECRET` | For auth script | OAuth client secret |
| `TICKTICK_ACCESS_TOKEN` | For production | OAuth access token (generated after auth) |

---

## Available Tools

Once configured, these MCP tools are available:

### Project Tools

| Tool | Description |
|------|-------------|
| `ticktick_list_projects` | List all projects (task lists) |
| `ticktick_get_project` | Get project details with tasks |
| `ticktick_create_project` | Create a new project |
| `ticktick_delete_project` | Delete a project |

### Task Tools

| Tool | Description |
|------|-------------|
| `ticktick_get_task` | Get task details |
| `ticktick_create_task` | Create a new task |
| `ticktick_update_task` | Update an existing task |
| `ticktick_complete_task` | Mark a task as complete |
| `ticktick_delete_task` | Delete a task |

---

## Task Priority Levels

When creating or updating tasks, use these priority values:

| Value | Priority |
|-------|----------|
| 0 | None |
| 1 | Low |
| 3 | Medium |
| 5 | High |

---

## Example Usage

### List all projects
```
Use the ticktick_list_projects tool
```

### Create a task
```
Use ticktick_create_task with:
- title: "Review quarterly report"
- project_id: "inbox" (or specific project ID)
- due_date: "2024-01-20T17:00:00"
- priority: 3
```

### Complete a task
```
Use ticktick_complete_task with:
- project_id: "your-project-id"
- task_id: "your-task-id"
```

---

## Token Expiration

TickTick access tokens are long-lived and typically don't expire. If you receive 401 Unauthorized errors, regenerate the token by running the auth script again.

---

## Troubleshooting

### "TICKTICK_ACCESS_TOKEN not set"

Set the environment variable with a valid token. Run the authentication script to generate one.

### "401 Unauthorized" errors

Your access token may be invalid. Regenerate it:
```bash
export TICKTICK_CLIENT_ID='your-client-id'
export TICKTICK_CLIENT_SECRET='your-client-secret'
python scripts/ticktick_auth.py
```

### Browser doesn't open during auth

Manually visit the URL printed in the terminal and complete the OAuth flow.

### "Redirect URI mismatch" error

Ensure the redirect URI in your TickTick app settings exactly matches:
```
http://localhost:8765/callback
```

---

## Resources

- [TickTick Developer Center](https://developer.ticktick.com/manage)
- [TickTick Open API Documentation](https://developer.ticktick.com/docs)
