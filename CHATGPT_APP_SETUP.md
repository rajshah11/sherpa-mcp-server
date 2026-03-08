# ChatGPT App (Developer Mode) Setup

Use this guide to connect this server as a remote MCP server in ChatGPT App developer mode.

## 1) Server/Auth0 configuration

Set these Railway env vars:

```bash
AUTH0_CONFIG_URL=https://YOUR_DOMAIN.auth0.com/.well-known/openid-configuration
AUTH0_CLIENT_ID=YOUR_AUTH0_APP_CLIENT_ID
AUTH0_CLIENT_SECRET=YOUR_AUTH0_APP_CLIENT_SECRET
SERVER_BASE_URL=https://YOUR_PUBLIC_RAILWAY_DOMAIN
AUTH0_AUDIENCE=https://YOUR_PUBLIC_RAILWAY_DOMAIN/mcp
AUTH_REQUIRED_SCOPES=
AUTH_ALLOWED_REDIRECT_URIS=http://localhost:*,https://chat.openai.com/aip/*,https://chatgpt.com/aip/*,https://chat.openai.com/connector/oauth/*,https://chatgpt.com/connector/oauth/*
```

If ChatGPT shows this error:

> The client ID ... was not found in the server's client registry.

then set:

```bash
AUTH_PRE_REGISTERED_CLIENT_IDS=<that_client_id>
```

(Comma-separated list supported.)

## 2) Auth0 app/API checks

- Auth0 API Identifier must exactly match `AUTH0_AUDIENCE`.
- App must allow redirects that cover ChatGPT/OpenAI callback URLs.
- App must be allowed to request tokens for the configured audience.

## 3) Verify discovery endpoints

```bash
curl -i https://YOUR_PUBLIC_RAILWAY_DOMAIN/.well-known/oauth-protected-resource/mcp
curl -i https://YOUR_PUBLIC_RAILWAY_DOMAIN/.well-known/oauth-authorization-server
curl -i https://YOUR_PUBLIC_RAILWAY_DOMAIN/.well-known/openid-configuration
```

All should return `200`.

## 4) Connect in ChatGPT App

Use server URL:

```text
https://YOUR_PUBLIC_RAILWAY_DOMAIN/mcp
```

## 5) Troubleshooting

- `404` on `/.well-known/openid-configuration` → verify server deployed latest version.
- `401 invalid_token` on `/mcp` → verify audience exact match and avoid restrictive scopes.
- `client registry` error → add client ID to `AUTH_PRE_REGISTERED_CLIENT_IDS`.
- Use `GET /info` to confirm active auth settings.
