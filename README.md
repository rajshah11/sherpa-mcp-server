# Sherpa MCP Server

A remote Model Context Protocol (MCP) server with personal assistant tools (calendar, tasks, meal logging) and optional Auth0 OAuth.

## What changed (auth simplification)

Auth was simplified to follow the same shape as OpenAI's authenticated MCP scaffold:

- Use `Auth0Provider` directly (no custom provider subclass).
- Keep OAuth config minimal and explicit.
- Add optional **pre-registration** of known OAuth client IDs for stateless deployments.
- Keep `/.well-known/openid-configuration` available at server origin for clients that probe it there.

## Quick start

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure

Copy `.env.example` to `.env` and set values.

### 3) Run

```bash
python server.py
```

Server defaults to `http://localhost:8000`.

## Required environment variables (Auth0 mode)

```bash
AUTH0_CONFIG_URL=https://YOUR_DOMAIN.auth0.com/.well-known/openid-configuration
AUTH0_CLIENT_ID=YOUR_AUTH0_APP_CLIENT_ID
AUTH0_CLIENT_SECRET=YOUR_AUTH0_APP_CLIENT_SECRET
SERVER_BASE_URL=https://YOUR_PUBLIC_DOMAIN
```

Recommended for ChatGPT App dev mode:

```bash
AUTH0_AUDIENCE=https://YOUR_PUBLIC_DOMAIN/mcp
AUTH_REQUIRED_SCOPES=
AUTH_ALLOWED_REDIRECT_URIS=http://localhost:*,https://chat.openai.com/aip/*,https://chatgpt.com/aip/*,https://chat.openai.com/connector/oauth/*,https://chatgpt.com/connector/oauth/*
```

If you hit `client_id ... not found in the server's client registry`, pre-register that client ID:

```bash
AUTH_PRE_REGISTERED_CLIENT_IDS=GCnHrvVUiCmszNV761KgPBaKhAllxMG6
```

(Comma-separated list supported.)

## Endpoints

- `POST /mcp` – MCP streamable HTTP endpoint
- `GET /health` – health status
- `GET /info` – runtime configuration summary
- `GET /.well-known/oauth-authorization-server` – OAuth metadata (when auth enabled)
- `GET /.well-known/oauth-protected-resource/mcp` – protected resource metadata (when auth enabled)
- `GET /.well-known/openid-configuration` – proxied Auth0 OIDC config

## ChatGPT App setup

See **[CHATGPT_APP_SETUP.md](CHATGPT_APP_SETUP.md)** for the step-by-step setup and troubleshooting checklist.

## Integrations

- Google Calendar (optional)
- TickTick (optional)
- Meal Logger (optional)

Integration setup docs:

- [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)
- [TICKTICK_SETUP.md](TICKTICK_SETUP.md)

## Deployment

Railway deployment notes: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
