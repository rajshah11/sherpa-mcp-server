# Connect Sherpa MCP Server to ChatGPT App (Developer Mode)

This guide covers the specific settings needed to connect this remote MCP server to ChatGPT App in developer mode without OAuth failures.

## Why auth was failing

Typical failure pattern:

- `GET /.well-known/openid-configuration` returned `404`
- `POST /mcp` returned `401 invalid_token`

ChatGPT App probes OIDC/OAuth discovery endpoints from your server origin and then calls `/mcp` with a bearer token. If discovery or token constraints are mismatched, you get `invalid_token`.

## 1) Set required Railway environment variables

In Railway, set:

```bash
AUTH0_CONFIG_URL=https://YOUR_DOMAIN.auth0.com/.well-known/openid-configuration
AUTH0_CLIENT_ID=YOUR_AUTH0_APP_CLIENT_ID
AUTH0_CLIENT_SECRET=YOUR_AUTH0_APP_CLIENT_SECRET
AUTH0_AUDIENCE=https://YOUR_PUBLIC_RAILWAY_DOMAIN/mcp
SERVER_BASE_URL=https://YOUR_PUBLIC_RAILWAY_DOMAIN
REQUIRE_CONSENT=true
```

Recommended for ChatGPT App compatibility:

```bash
# Leave empty unless you explicitly need scope enforcement
AUTH_REQUIRED_SCOPES=

# Include OpenAI callback URL patterns
AUTH_ALLOWED_REDIRECT_URIS=http://localhost:*,https://chat.openai.com/aip/*,https://chatgpt.com/aip/*,https://chat.openai.com/connector/oauth/*,https://chatgpt.com/connector/oauth/*
AUTH_AUTO_REGISTER_UNKNOWN_CLIENTS=true
```

## 2) Configure Auth0 correctly

In Auth0:

1. Create/use an **Application** (Regular Web App is typical).
2. Create/use an **API** and set its Identifier to exactly your MCP resource URL (typically `https://YOUR_PUBLIC_RAILWAY_DOMAIN/mcp`).
3. In the Application's allowed URLs, include:
   - `https://chat.openai.com/aip/*`
   - `https://chatgpt.com/aip/*`
   - your own callback if used (`https://YOUR_PUBLIC_RAILWAY_DOMAIN/auth/callback`)
4. Ensure the app can request tokens for your API audience.

## 3) Verify discovery endpoints from your deployed URL

Replace `https://YOUR_PUBLIC_RAILWAY_DOMAIN` below:

```bash
curl -i https://YOUR_PUBLIC_RAILWAY_DOMAIN/.well-known/oauth-protected-resource/mcp
curl -i https://YOUR_PUBLIC_RAILWAY_DOMAIN/.well-known/oauth-authorization-server
curl -i https://YOUR_PUBLIC_RAILWAY_DOMAIN/.well-known/openid-configuration
```

All should return `200` with JSON.

## 4) Verify token acceptance path

After linking in ChatGPT App dev mode, test:

```bash
curl -i https://YOUR_PUBLIC_RAILWAY_DOMAIN/health
```

Then try a tool call from ChatGPT. If you see an authorization page saying `The client ID ... was not found in the server's client registry`, make sure `AUTH_AUTO_REGISTER_UNKNOWN_CLIENTS=true` (or pre-register that client manually).

If `/mcp` still returns `401 invalid_token`, check:

- `AUTH0_AUDIENCE` matches `https://YOUR_PUBLIC_RAILWAY_DOMAIN/mcp` and Auth0 API Identifier exactly.
- Token `iss` matches your Auth0 tenant.
- You did not set restrictive `AUTH_REQUIRED_SCOPES` that ChatGPT token does not include.

## 5) Configure in ChatGPT App (Developer Mode)

Use your MCP endpoint:

- **Server URL**: `https://YOUR_PUBLIC_RAILWAY_DOMAIN/mcp`

ChatGPT should discover OAuth metadata automatically from your server.

## Quick troubleshooting checklist

- `/.well-known/openid-configuration` must be `200` (not `404`).
- `SERVER_BASE_URL` must match your externally reachable HTTPS URL.
- Auth0 Application must allow OpenAI redirect patterns.
- `AUTH_REQUIRED_SCOPES` should be empty unless you truly need scope checks.
- `AUTH0_AUDIENCE` must exactly equal your MCP resource URL and Auth0 API Identifier.
