# Auth0 Setup Guide for Sherpa MCP Server

This guide walks you through setting up Auth0 OAuth authentication for your Sherpa MCP Server.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Create Auth0 Account](#create-auth0-account)
3. [Create Auth0 Application](#create-auth0-application)
4. [Create Auth0 API](#create-auth0-api)
5. [Configure Application Settings](#configure-application-settings)
6. [Configure Server Environment](#configure-server-environment)
7. [Test Authentication](#test-authentication)
8. [Troubleshooting](#troubleshooting)
9. [Security Best Practices](#security-best-practices)

## Prerequisites

- Auth0 account (free tier works fine for personal use)
- Sherpa MCP Server installed and configured
- Your server's public URL (e.g., `http://localhost:8000` for development or `https://your-server.com` for production)

## Create Auth0 Account

1. Go to [auth0.com](https://auth0.com)
2. Click **Sign Up** and create a free account
3. Choose a tenant domain (e.g., `your-name.auth0.com`)
   - This will be part of your `AUTH0_CONFIG_URL`
   - Cannot be changed later, so choose carefully
4. Select your region (choose closest to your users)
5. Complete the registration process

## Create Auth0 Application

Auth0 Applications represent your MCP server in the Auth0 dashboard.

### Step 1: Create the Application

1. Log in to [Auth0 Dashboard](https://manage.auth0.com)
2. Navigate to **Applications** → **Applications** in the left sidebar
3. Click **Create Application**
4. Configure the application:
   - **Name**: `Sherpa MCP Server` (or any name you prefer)
   - **Application Type**: Select **Regular Web Application**
5. Click **Create**

### Step 2: Note Your Credentials

After creating the application, you'll see the **Settings** tab:

1. Find and copy the following values:
   - **Domain**: `your-tenant.auth0.com`
   - **Client ID**: A long alphanumeric string
   - **Client Secret**: Click **Show** to reveal, then copy it

2. Save these values - you'll need them for the `.env` file

**Important**: Keep your Client Secret secure! Never commit it to version control or share it publicly.

## Create Auth0 API

Auth0 APIs define the audience for your OAuth tokens. This is required for the server to validate tokens.

### Step 1: Create the API

1. In Auth0 Dashboard, navigate to **Applications** → **APIs**
2. Click **Create API**
3. Configure the API:
   - **Name**: `Sherpa MCP Server API` (or any descriptive name)
   - **Identifier**: `https://api.sherpa-mcp.com` (or any unique URL-like identifier)
     - This becomes your `AUTH0_AUDIENCE`
     - Doesn't need to be a real URL
     - Should be unique across your Auth0 tenant
     - Cannot be changed later
   - **Signing Algorithm**: Select **RS256** (default)
4. Click **Create**

### Step 2: Configure API Settings (Optional)

1. Go to the **Settings** tab of your newly created API
2. Review the settings:
   - **Token Expiration**: Default is 86400 seconds (24 hours) - adjust as needed
   - **Allow Skipping User Consent**: Leave **OFF** for better security
   - **Allow Offline Access**: Enable if you want refresh tokens (recommended)

3. Go to the **Permissions** tab to add scopes (optional):
   - Click **Add a Permission (Scope)**
   - Add scopes like:
     - `read:data` - Read user data
     - `write:data` - Write user data
     - `admin:access` - Admin access
   - These can be used to restrict tool access in future versions

## Configure Application Settings

Now configure your Auth0 Application to work with the MCP server.

### Step 1: Configure URLs

1. Go back to **Applications** → **Applications**
2. Select your **Sherpa MCP Server** application
3. Scroll to **Application URIs** section
4. Configure the following:

#### Allowed Callback URLs
Add your server's callback URL(s):

**For Local Development:**
```
http://localhost:8000/auth/callback
```

**For Production:**
```
https://your-server.com/auth/callback
```

**Multiple Environments** (comma-separated):
```
http://localhost:8000/auth/callback, https://your-server.com/auth/callback
```

#### Allowed Logout URLs (Optional)
If you implement logout functionality:
```
http://localhost:8000
https://your-server.com
```

#### Allowed Web Origins
Add your server's base URL(s):
```
http://localhost:8000
https://your-server.com
```

#### Allowed Origins (CORS)
Same as Allowed Web Origins:
```
http://localhost:8000
https://your-server.com
```

5. Click **Save Changes** at the bottom

### Step 2: Advanced Settings (Optional)

Scroll down to **Advanced Settings** and expand it:

1. **Grant Types**: Ensure the following are enabled:
   - ✅ Authorization Code
   - ✅ Refresh Token
   - ✅ Client Credentials (if you need machine-to-machine)

2. **Refresh Token Rotation**: Enable for better security
   - **Rotation**: **Enabled**
   - **Reuse Interval**: 0 seconds (one-time use)

3. Click **Save Changes**

## Configure Server Environment

Now configure your Sherpa MCP Server with the Auth0 credentials.

### Step 1: Create `.env` File

If you haven't already, copy the example environment file:

```bash
cp .env.example .env
```

### Step 2: Add Auth0 Configuration

Edit `.env` and add your Auth0 credentials:

```bash
# ============================================================================
# Auth0 OAuth Configuration
# ============================================================================

# Auth0 Config URL - Replace YOUR_DOMAIN with your Auth0 tenant domain
AUTH0_CONFIG_URL=https://YOUR_DOMAIN.auth0.com/.well-known/openid-configuration

# Auth0 Application Credentials - From Application Settings
AUTH0_CLIENT_ID=your-client-id-from-auth0-dashboard
AUTH0_CLIENT_SECRET=your-client-secret-from-auth0-dashboard

# Auth0 API Audience - The identifier from your Auth0 API
AUTH0_AUDIENCE=https://api.sherpa-mcp.com

# Server Configuration
SERVER_BASE_URL=http://localhost:8000  # Change to https://your-domain.com for production

# OAuth Settings
REQUIRE_CONSENT=true  # Show consent screen (recommended)
```

### Step 3: Example Configuration

Here's a complete example with placeholder values:

```bash
# Replace these with your actual values:
AUTH0_CONFIG_URL=https://dev-abc123.us.auth0.com/.well-known/openid-configuration
AUTH0_CLIENT_ID=xYzAbc123XyzAbC123xYzAbC12345678
AUTH0_CLIENT_SECRET=xYzAbC123-xYzAbC_123XyZ-aBc_123XyZaBc123XyZ-aBc123XyZaBc123X
AUTH0_AUDIENCE=https://api.sherpa-mcp.com
SERVER_BASE_URL=http://localhost:8000
REQUIRE_CONSENT=true
```

### Step 4: Verify Environment Variables

Check that all required variables are set:

```bash
# macOS/Linux
grep -E "AUTH0_|SERVER_BASE_URL" .env

# Windows (PowerShell)
Select-String -Pattern "AUTH0_|SERVER_BASE_URL" .env
```

## Test Authentication

### Step 1: Start the Server

```bash
# Activate your virtual environment if not already active
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Start the server
python server.py
```

You should see:
```
============================================================
Starting Sherpa MCP Server v1.0.0
============================================================
Authentication: Enabled (Auth0)
Server URL: http://localhost:8000
============================================================
```

### Step 2: Test OAuth Metadata Endpoint

Verify OAuth is configured correctly:

```bash
curl http://localhost:8000/.well-known/oauth-authorization-server | jq
```

Expected response should include:
```json
{
  "issuer": "http://localhost:8000",
  "authorization_endpoint": "http://localhost:8000/auth/authorize",
  "token_endpoint": "http://localhost:8000/auth/token",
  ...
}
```

### Step 3: Test Health Endpoint

```bash
curl http://localhost:8000/health | jq
```

Should return:
```json
{
  "status": "healthy",
  "auth_enabled": true,
  ...
}
```

### Step 4: Test with MCP Client

#### Using Claude Desktop

1. Open Claude Desktop configuration:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add your server configuration:

```json
{
  "mcpServers": {
    "sherpa": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http"
    }
  }
}
```

3. Restart Claude Desktop

4. When you try to use a tool, you'll be redirected to Auth0 for authentication

#### Using Claude.ai (Web)

For remote servers with HTTPS:

```json
{
  "mcpServers": {
    "sherpa": {
      "url": "https://your-server.com/mcp",
      "transport": "streamable-http",
      "oauth": {
        "discovery_url": "https://your-server.com/.well-known/oauth-authorization-server"
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

#### 1. "Invalid Callback URL" Error

**Symptom**: Auth0 shows error "callback URL is not in the allowed list"

**Solution**:
- Verify callback URL is added to **Allowed Callback URLs** in Auth0 Application settings
- Ensure the URL exactly matches (including protocol, port, and path)
- Check for typos (e.g., `http` vs `https`, trailing slashes)

**Example**:
```
Correct: http://localhost:8000/auth/callback
Wrong:   http://localhost:8000/auth/callback/
Wrong:   https://localhost:8000/auth/callback  (http vs https)
```

#### 2. "Client Secret Not Found" Error

**Symptom**: Server fails to start with "AUTH0_CLIENT_SECRET is required"

**Solution**:
- Verify `AUTH0_CLIENT_SECRET` is set in `.env` file
- Check for whitespace or quotes around the secret
- Ensure the secret is copied correctly from Auth0 dashboard

#### 3. "Invalid Audience" Error

**Symptom**: Token validation fails with "invalid audience"

**Solution**:
- Verify `AUTH0_AUDIENCE` matches the **Identifier** in your Auth0 API settings
- Check for typos or extra whitespace
- Ensure the audience is a valid URL-like string

#### 4. "OIDC Discovery Failed" Error

**Symptom**: Server can't fetch Auth0 configuration

**Solution**:
- Verify `AUTH0_CONFIG_URL` is correct
- Check your internet connection
- Ensure Auth0 tenant domain is correct
- Try accessing the URL in a browser:
  ```
  https://YOUR_DOMAIN.auth0.com/.well-known/openid-configuration
  ```

#### 5. "Consent Screen Not Showing"

**Symptom**: Users not seeing consent screen before authentication

**Solution**:
- Set `REQUIRE_CONSENT=true` in `.env`
- Restart the server
- Clear browser cookies for localhost/your domain

#### 6. "Token Expired" Errors

**Symptom**: Frequent token expiration errors

**Solution**:
- Adjust token expiration in Auth0 API settings
- Enable refresh tokens in Auth0 Application grant types
- Implement token refresh in your MCP client

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Add to .env
LOG_LEVEL=DEBUG

# Or set in shell
export LOG_LEVEL=DEBUG
python server.py
```

### Testing Auth0 Configuration

Use this script to test your Auth0 configuration:

```python
# test_auth0.py
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

config_url = os.getenv("AUTH0_CONFIG_URL")
print(f"Testing: {config_url}")

response = httpx.get(config_url)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

Run with:
```bash
python test_auth0.py
```

## Security Best Practices

### 1. Protect Client Secret

- **Never** commit `.env` to version control
- **Never** expose client secret in client-side code
- Store securely in environment variables or secret management service
- Rotate regularly (every 3-6 months)

### 2. Use HTTPS in Production

- Always use `https://` for production `SERVER_BASE_URL`
- Obtain SSL certificate (Let's Encrypt is free)
- Auth0 may require HTTPS for certain features

### 3. Enable Consent Screen

```bash
REQUIRE_CONSENT=true
```

This protects against confused deputy attacks where malicious clients impersonate users.

### 4. Restrict Redirect URIs

Only add specific callback URLs you control:

```
✅ Good: https://your-server.com/auth/callback
❌ Bad:  https://*.com/*  (too permissive)
```

### 5. Configure Token Expiration

In Auth0 API Settings:
- **Access Token**: 1-24 hours (shorter = more secure)
- **Refresh Token**: 7-30 days
- **ID Token**: 1 hour

### 6. Enable Refresh Token Rotation

In Auth0 Application → Advanced Settings → Grant Types:
- Enable **Refresh Token Rotation**
- Set **Reuse Interval** to 0 (one-time use)

### 7. Use Strong Scopes

Define specific scopes in Auth0 API and require them:

```bash
# .env
FASTMCP_SERVER_AUTH_AUTH0_REQUIRED_SCOPES=openid,profile,read:data
```

### 8. Monitor Auth0 Logs

Regularly check Auth0 Dashboard → Monitoring → Logs for:
- Failed login attempts
- Suspicious activity
- Token validation failures

### 9. Implement Rate Limiting

Consider adding rate limiting for your endpoints:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("5/minute")
@server.custom_route("/auth/callback")
async def callback(request: Request):
    # ... callback logic
```

### 10. Regular Security Audits

- Review Auth0 applications and APIs quarterly
- Remove unused applications
- Update Auth0 SDK and dependencies regularly
- Review and rotate credentials

## Advanced Configuration

### Custom JWT Signing Key

For additional security, use a custom JWT signing key:

```bash
# Generate a strong key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
FASTMCP_SERVER_AUTH_AUTH0_JWT_SIGNING_KEY=your-generated-key-here
```

### Custom Storage Backend (Redis)

For horizontal scaling with multiple server instances:

```python
# server.py
from key_value.aio.stores.redis import RedisStore

redis_store = RedisStore(url="redis://localhost:6379")

auth = Auth0Provider(
    # ... other config ...
    client_storage=redis_store,
)
```

### Multiple Environments

Create separate Auth0 Applications for each environment:

```bash
# .env.development
AUTH0_CLIENT_ID=dev-client-id
AUTH0_CLIENT_SECRET=dev-client-secret
SERVER_BASE_URL=http://localhost:8000

# .env.production
AUTH0_CLIENT_ID=prod-client-id
AUTH0_CLIENT_SECRET=prod-client-secret
SERVER_BASE_URL=https://your-server.com
```

### Custom Scopes and Permissions

1. In Auth0 API, define permissions:
   - `read:calendar` - Read calendar events
   - `write:calendar` - Modify calendar events
   - `read:tasks` - Read tasks
   - `write:tasks` - Modify tasks

2. Require specific scopes in your server:

```python
auth = Auth0Provider(
    # ... other config ...
    required_scopes=["openid", "profile", "read:calendar", "write:tasks"],
)
```

3. Check scopes in your tools:

```python
@server.tool()
async def create_calendar_event(ctx: Context):
    # Access token is available in request context
    # Validate scopes if needed
    return "Event created"
```

## Production Deployment Checklist

Before deploying to production:

- [ ] Create separate Auth0 Application for production
- [ ] Use production Auth0 API with appropriate scopes
- [ ] Set `SERVER_BASE_URL` to HTTPS URL
- [ ] Enable refresh token rotation
- [ ] Set `REQUIRE_CONSENT=true`
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging
- [ ] Configure proper CORS settings
- [ ] Use strong JWT signing key
- [ ] Implement Redis or similar for horizontal scaling
- [ ] Set up backup OAuth credentials
- [ ] Document emergency access procedures
- [ ] Test full OAuth flow in production environment
- [ ] Set up Auth0 monitoring alerts

## Getting Help

### Resources

- **Auth0 Documentation**: https://auth0.com/docs
- **FastMCP Documentation**: https://gofastmcp.com/servers/auth/remote-oauth
- **MCP Protocol**: https://modelcontextprotocol.io
- **OAuth 2.1**: https://oauth.net/2.1/

### Auth0 Support

- **Community**: https://community.auth0.com
- **Support**: Available with paid plans
- **Status**: https://status.auth0.com

### Common Auth0 Endpoints

For your Auth0 tenant (`YOUR_DOMAIN.auth0.com`):

- **OpenID Configuration**: `https://YOUR_DOMAIN.auth0.com/.well-known/openid-configuration`
- **JWKS**: `https://YOUR_DOMAIN.auth0.com/.well-known/jwks.json`
- **Authorization**: `https://YOUR_DOMAIN.auth0.com/authorize`
- **Token**: `https://YOUR_DOMAIN.auth0.com/oauth/token`
- **UserInfo**: `https://YOUR_DOMAIN.auth0.com/userinfo`

---

**Next Steps**: Once Auth0 is configured, return to [README.md](README.md) to continue with server setup and testing.
