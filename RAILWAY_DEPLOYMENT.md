# Railway Deployment Guide for Sherpa MCP Server

This guide walks you through deploying the Sherpa MCP Server to Railway.app, a modern platform for deploying containerized applications.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Railway Setup](#railway-setup)
3. [Deploy from GitHub](#deploy-from-github)
4. [Configure Environment Variables](#configure-environment-variables)
5. [Configure Custom Domain](#configure-custom-domain)
6. [Configure Auth0 for Production](#configure-auth0-for-production)
7. [Test Deployment](#test-deployment)
8. [Monitoring and Logs](#monitoring-and-logs)
9. [Troubleshooting](#troubleshooting)
10. [Cost and Scaling](#cost-and-scaling)

## Prerequisites

- GitHub account with the sherpa-mcp-server repository
- Railway account (free tier available)
- Auth0 account (if using authentication)
- Domain name (optional, for custom domain)

## Railway Setup

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click **Start a New Project**
3. Sign up with GitHub (recommended for easy deployment)
4. Authorize Railway to access your GitHub repositories

### Step 2: Create New Project

1. After login, click **New Project**
2. Select **Deploy from GitHub repo**
3. Choose your repository: `sherpa-mcp-server`
4. Railway will automatically detect the Dockerfile

## Deploy from GitHub

### Automatic Deployment

Railway automatically deploys when you push to your repository.

1. **Initial Deploy**:
   - Railway reads `railway.toml` for configuration
   - Builds Docker image from `Dockerfile`
   - Starts the container with environment variables
   - Assigns a public URL (e.g., `sherpa-mcp-production.up.railway.app`)

2. **Auto-Deploy on Push**:
   - Every git push to `main` triggers a new deployment
   - Railway builds and deploys automatically
   - Zero-downtime deployments

### Manual Deploy

If you need to trigger a manual deployment:

1. Go to your Railway project dashboard
2. Click on your service
3. Click **Deploy** → **Redeploy**

## Configure Environment Variables

Railway provides environment variables through the dashboard.

### Step 1: Access Variables

1. In Railway dashboard, select your project
2. Click on your service (e.g., `sherpa-mcp-server`)
3. Go to **Variables** tab

### Step 2: Add Required Variables

Click **New Variable** and add the following:

#### Basic Configuration

```
SERVER_HOST=0.0.0.0
```

**Note**: `PORT` is automatically set by Railway (do not override)

#### Auth0 Configuration (Required for Production)

```
AUTH0_CONFIG_URL=https://YOUR_DOMAIN.auth0.com/.well-known/openid-configuration
AUTH0_CLIENT_ID=your-production-client-id
AUTH0_CLIENT_SECRET=your-production-client-secret
AUTH0_AUDIENCE=https://api.sherpa-mcp.com
REQUIRE_CONSENT=true
```

#### Server Base URL

After Railway assigns your domain, add:

```
SERVER_BASE_URL=https://sherpa-mcp-production.up.railway.app
```

**Important**: Update this to your custom domain if you configure one.

#### Google Calendar Configuration (Optional)

If using Google Calendar integration:

```
GOOGLE_CALENDAR_TOKEN_JSON='{"token":"...","refresh_token":"...","client_id":"...","client_secret":"..."}'
```

**Setup**:
1. Run authentication locally first (see [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md))
2. Copy the generated `GOOGLE_CALENDAR_TOKEN_JSON` value
3. Add it as a Railway environment variable

No files needed - everything is stored in environment variables.

### Step 3: Use Railway's Secret Manager (Optional)

For sensitive values like `AUTH0_CLIENT_SECRET`:

1. Railway automatically treats all variables as secrets
2. Values are encrypted at rest
3. Never exposed in logs or deployment info

### Step 4: Variable References

You can reference other variables:

```
SERVER_BASE_URL=${{RAILWAY_STATIC_URL}}
```

Railway provides built-in variables:
- `RAILWAY_STATIC_URL` - Your app's public URL
- `RAILWAY_ENVIRONMENT` - Current environment (production/staging)
- `PORT` - Port Railway assigns (auto-set)

## Configure Custom Domain

### Step 1: Generate Domain in Railway

1. In your service settings, go to **Settings** tab
2. Scroll to **Networking** section
3. Click **Generate Domain**
4. Railway provides a free subdomain: `*.up.railway.app`

### Step 2: Add Custom Domain (Optional)

If you have your own domain:

1. In **Networking** section, click **Custom Domain**
2. Enter your domain (e.g., `mcp.yourdomain.com`)
3. Railway provides DNS records to configure:
   ```
   Type: CNAME
   Name: mcp (or your subdomain)
   Value: provided-by-railway.railway.app
   ```

4. Add the CNAME record to your DNS provider
5. Wait for DNS propagation (5-30 minutes)
6. Railway automatically provisions SSL certificate

### Step 3: Update Environment Variables

After setting up your domain:

1. Update `SERVER_BASE_URL`:
   ```
   SERVER_BASE_URL=https://mcp.yourdomain.com
   ```

2. Redeploy to apply changes

## Configure Auth0 for Production

After deploying to Railway, update your Auth0 configuration.

### Step 1: Get Your Railway URL

Your Railway URL will be something like:
```
https://sherpa-mcp-production.up.railway.app
```

Or if using custom domain:
```
https://mcp.yourdomain.com
```

### Step 2: Update Auth0 Application Settings

1. Go to [Auth0 Dashboard](https://manage.auth0.com)
2. Navigate to **Applications** → **Applications**
3. Select your **Sherpa MCP Server** application
4. Update **Application URIs**:

#### Allowed Callback URLs
Add your production callback URL:
```
https://sherpa-mcp-production.up.railway.app/auth/callback
```

Or with custom domain:
```
https://mcp.yourdomain.com/auth/callback
```

Keep localhost for development:
```
http://localhost:8000/auth/callback, https://sherpa-mcp-production.up.railway.app/auth/callback
```

#### Allowed Web Origins
```
https://sherpa-mcp-production.up.railway.app
```

#### Allowed Logout URLs
```
https://sherpa-mcp-production.up.railway.app
```

5. Click **Save Changes**

### Step 3: Verify OAuth Discovery

Test the OAuth metadata endpoint:

```bash
curl https://sherpa-mcp-production.up.railway.app/.well-known/oauth-authorization-server | jq
```

Should return OAuth configuration with your production URL.

## Test Deployment

### Step 1: Test Health Endpoint

```bash
curl https://sherpa-mcp-production.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-04T...",
  "service": "sherpa-mcp-server",
  "version": "1.0.0",
  "auth_enabled": true,
  "google_calendar_enabled": true
}
```

### Step 2: Test Info Endpoint

```bash
curl https://sherpa-mcp-production.up.railway.app/info
```

### Step 3: Test OAuth Flow

1. Use Claude.ai (web interface)
2. Configure MCP server in Claude settings
3. Trigger OAuth flow by using a tool
4. Verify Auth0 login works
5. Confirm tool execution succeeds

### Step 4: Test with Claude Desktop

Update your Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sherpa": {
      "url": "https://sherpa-mcp-production.up.railway.app/mcp",
      "transport": "streamable-http"
    }
  }
}
```

Restart Claude Desktop and test the connection.

## Monitoring and Logs

### Railway Dashboard

1. **Deployments**: View deployment history and status
2. **Metrics**: CPU, memory, network usage
3. **Logs**: Real-time application logs

### View Logs

1. In Railway dashboard, click on your service
2. Go to **Deployments** tab
3. Click on the latest deployment
4. View logs in real-time

You'll see your application logs:
```
============================================================
Starting Sherpa MCP Server v1.0.0
============================================================
Authentication: Enabled (Auth0)
Google Calendar: Enabled
Server URL: https://sherpa-mcp-production.up.railway.app
============================================================
Starting server on 0.0.0.0:8080
```

### Health Monitoring

Railway automatically monitors your `/health` endpoint (configured in `railway.toml`):

- **Health Check Interval**: Every 30 seconds (Docker HEALTHCHECK)
- **Railway Monitor**: Uses `/health` for service status
- **Auto-Restart**: Unhealthy containers restart automatically

### Alerts (Pro Plan)

Railway Pro plan provides:
- Email notifications for deployment failures
- Slack/Discord webhooks
- Custom alerting rules

## Troubleshooting

### Common Issues

#### 1. Build Fails

**Symptom**: Railway build fails during Docker image creation

**Check**:
- View build logs in Railway dashboard
- Verify `Dockerfile` syntax
- Check `requirements.txt` dependencies

**Solution**:
```bash
# Test locally first
docker build -t sherpa-mcp-server .
docker run -p 8000:8000 sherpa-mcp-server
```

#### 2. Health Check Fails

**Symptom**: Railway shows service as unhealthy

**Check**:
- View logs for startup errors
- Verify `/health` endpoint responds
- Check environment variables are set

**Solution**:
```bash
# Check health endpoint
curl https://your-app.up.railway.app/health

# View Railway logs
# Check for Python errors or missing env vars
```

#### 3. Port Binding Issues

**Symptom**: Server fails to start with port errors

**Check**:
- Server uses `PORT` environment variable (Railway provides this)
- `server.py` reads from `PORT` (already implemented)

**Solution**:
- Verify `server.py` line 221: `port = int(os.getenv("PORT", ...))`
- Railway automatically sets `PORT`, no configuration needed

#### 4. OAuth Errors

**Symptom**: Auth0 login fails or shows "Invalid Callback URL"

**Check**:
- `SERVER_BASE_URL` matches your actual Railway URL
- Auth0 callback URL includes production URL
- HTTPS is used (not HTTP)

**Solution**:
1. Update `SERVER_BASE_URL` in Railway variables
2. Add callback URL to Auth0 application settings
3. Redeploy the service

#### 5. Environment Variables Not Loading

**Symptom**: Server can't read environment variables

**Check**:
- Variables are set in Railway dashboard
- No typos in variable names
- Service was redeployed after adding variables

**Solution**:
1. Add/verify variables in Railway dashboard
2. Click **Deploy** → **Redeploy** to apply changes
3. Check logs for variable values (don't log secrets!)

### Debug Mode

Enable debug logging:

1. Add variable in Railway:
   ```
   LOG_LEVEL=DEBUG
   ```

2. Redeploy

3. View detailed logs in Railway dashboard

### Railway CLI (Advanced)

Install Railway CLI for local testing:

```bash
# Install
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# View logs
railway logs

# Run locally with Railway environment
railway run python server.py

# Open in browser
railway open
```

## Cost and Scaling

### Railway Pricing (as of 2026)

**Free Tier (Hobby)**:
- $5 credit per month
- 512 MB RAM
- 1 GB disk
- 100 GB egress
- Perfect for personal MCP server

**Pro Plan** ($20/month):
- $20 credit included
- Pay for what you use beyond credits
- Up to 8 GB RAM per service
- Shared CPU (can upgrade to dedicated)
- Custom domains
- Team collaboration
- Priority support

### Estimated Costs for MCP Server

For a personal MCP server with moderate usage:

**Expected Resource Usage**:
- Memory: ~256-512 MB
- CPU: Minimal (mostly idle)
- Network: ~1-5 GB/month (depending on usage)

**Estimated Cost**: Free tier is usually sufficient for personal use.

### Scaling Configuration

Railway auto-scales based on traffic, but you can configure limits:

1. In Railway dashboard, go to **Settings**
2. Under **Resources**, set:
   - **Memory**: 512 MB - 1 GB (recommended)
   - **CPU**: Shared (cost-effective for MCP server)

### Horizontal Scaling (Advanced)

For high availability, deploy multiple instances:

1. Use Redis for shared session storage (update `server.py`)
2. Configure Auth0Provider with Redis backend
3. Deploy multiple Railway services behind a load balancer

Example with Redis:
```python
from key_value.aio.stores.redis import RedisStore

redis_store = RedisStore(url=os.getenv("REDIS_URL"))

auth = Auth0Provider(
    # ... other config ...
    client_storage=redis_store,
)
```

Add Redis in Railway:
1. **New** → **Database** → **Add Redis**
2. Railway provides `REDIS_URL` automatically
3. Update requirements.txt: `redis>=4.0.0`

## Production Checklist

Before going to production:

- [ ] Auth0 configured with production URLs
- [ ] `SERVER_BASE_URL` set to production URL
- [ ] All environment variables configured in Railway
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active (automatic with Railway)
- [ ] Health endpoint returns 200 OK
- [ ] OAuth flow tested end-to-end
- [ ] Logs reviewed for errors
- [ ] Health monitoring configured
- [ ] Backup OAuth credentials stored securely
- [ ] Team members have access to Railway project (if applicable)
- [ ] Auth0 security settings reviewed (MFA, anomaly detection)
- [ ] Railway resource limits configured
- [ ] Google Calendar credentials deployed (if using calendar integration)
- [ ] Calendar tools tested in production

## Next Steps

After successful deployment:

1. **Configure Claude.ai**: Add your Railway URL to Claude web interface
2. **Test Tools**: Verify all MCP tools work correctly
3. **Monitor Usage**: Watch Railway metrics and logs
4. **Scale as Needed**: Adjust resources based on usage
5. **Configure Google Calendar**: See [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)
6. **Add More Features**: Implement TickTick, Obsidian integrations

## Getting Help

### Resources

- **Railway Documentation**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Railway Status**: https://status.railway.app
- **Auth0 + Railway**: See AUTH0_SETUP.md

### Railway Support

- **Community**: Discord server (very active)
- **Pro Support**: Available with Pro plan
- **GitHub**: https://github.com/railwayapp/railway

### Common Railway Commands

```bash
# View service status
railway status

# Stream logs
railway logs --follow

# Execute command in Railway environment
railway run <command>

# Open Railway dashboard
railway open

# Deploy manually
railway up

# View all variables
railway variables

# Add variable
railway variables set KEY=value
```

---

**Previous**: [AUTH0_SETUP.md](AUTH0_SETUP.md)
**Next**: [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)
