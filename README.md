# Sherpa MCP Server

A remote Model Context Protocol (MCP) server with Auth0 OAuth authentication, designed to act as your personal assistant. The server manages calendar events, tasks, notes, health data, and more.

## Features

- 🔐 **Secure Authentication**: Auth0 OAuth 2.1 + OIDC with PKCE support
- 🛠️ **MCP Tools**: Test connection, echo messages, get server time, and more
- 🏥 **Health Monitoring**: Built-in health check and info endpoints
- 🌐 **Remote Access**: HTTP-based transport for remote connectivity
- 📦 **Modular Design**: Easy to extend with new tools and integrations

## Current Status

✅ **Phase 1 Complete**: Basic MCP server with Auth0 OAuth authentication
- Remote MCP server with streamable-http transport
- Test connection tool for connectivity verification
- Health check and info custom endpoints
- Auth0 OAuth authentication (optional)
- Production-ready with secure defaults

🚧 **Planned Integrations**:
- Google Calendar events management
- TickTick task management
- Obsidian notes (filesystem synced with SyncThing)
- Health data management

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Auth0 account (optional, for authentication)
- pip or uv for package management

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd sherpa-mcp-server
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the server**:
   ```bash
   python server.py
   ```

The server will start on `http://localhost:8000` by default.

## Configuration

### Without Authentication (Development)

For local development without authentication:

```bash
# .env file - leave Auth0 variables commented out
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_BASE_URL=http://localhost:8000
```

Run the server:
```bash
python server.py
```

### With Auth0 Authentication (Production)

For production with Auth0:

1. **Set up Auth0** (see [AUTH0_SETUP.md](AUTH0_SETUP.md) for detailed instructions)
2. **Configure environment variables** in `.env`:
   ```bash
   AUTH0_CONFIG_URL=https://YOUR_DOMAIN.auth0.com/.well-known/openid-configuration
   AUTH0_CLIENT_ID=your-client-id
   AUTH0_CLIENT_SECRET=your-client-secret
   AUTH0_AUDIENCE=https://api.your-app.com
   SERVER_BASE_URL=https://your-server.com
   ```

3. **Run the server**:
   ```bash
   python server.py
   ```

## Available Endpoints

### MCP Protocol Endpoint
- **POST** `/mcp` - Main MCP protocol endpoint (streamable-http transport)

### Custom HTTP Endpoints
- **GET** `/` - Root endpoint with server information
- **GET** `/health` - Health check for monitoring
- **GET** `/info` - Detailed server information

### OAuth Endpoints (when Auth0 is enabled)
- **GET** `/.well-known/oauth-authorization-server` - OAuth metadata
- **GET** `/.well-known/oauth-protected-resource` - Protected resource metadata
- **GET** `/auth/callback` - OAuth callback endpoint

## Available Tools

The MCP server exposes the following tools to clients:

### 1. `test_connection`
Test the connection to the MCP server and get server status.

**Returns**: Connection status with timestamp and authentication info

### 2. `echo`
Echo back a message with optional formatting.

**Parameters**:
- `message` (string, required): The message to echo
- `uppercase` (boolean, optional): Convert to uppercase
- `prefix` (string, optional): Prefix to add to the message

**Returns**: Formatted message

### 3. `get_server_time`
Get the current server time in ISO format.

**Returns**: Dictionary with local and UTC timestamps

## Connecting to Claude Desktop

To use this server with Claude Desktop:

1. **Without Auth0 (Local Development)**:
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

2. **With Auth0 (Production)**:
   ```json
   {
     "mcpServers": {
       "sherpa": {
         "url": "https://your-server.com/mcp",
         "transport": "streamable-http",
         "oauth": {
           "client_id": "your-mcp-client-id"
         }
       }
     }
   }
   ```

See [AUTH0_SETUP.md](AUTH0_SETUP.md) for complete Auth0 configuration.

## Testing the Server

### Test Health Endpoint
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-04T...",
  "service": "sherpa-mcp-server",
  "version": "1.0.0",
  "auth_enabled": false
}
```

### Test Info Endpoint
```bash
curl http://localhost:8000/info
```

### Test MCP Tool (requires MCP client)
Use Claude Desktop or the FastMCP CLI to test MCP tools:
```bash
# Using FastMCP CLI (if available)
fastmcp client http://localhost:8000/mcp --tool test_connection
```

## Development

### Project Structure
```
sherpa-mcp-server/
├── server.py              # Main server implementation
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment configuration
├── .env                  # Your local configuration (not in git)
├── README.md            # This file
├── AUTH0_SETUP.md       # Auth0 setup guide
└── src/                 # Future: modular components
```

### Adding New Tools

Add new tools using the `@server.tool` decorator:

```python
@server.tool(
    name="my_tool",
    description="Description of what this tool does"
)
async def my_tool(param1: str, param2: int = 0) -> dict:
    """Tool implementation."""
    return {"result": f"{param1}-{param2}"}
```

### Adding Custom Endpoints

Add custom HTTP endpoints using `@server.custom_route`:

```python
@server.custom_route("/my-endpoint", methods=["GET"])
async def my_endpoint(request: Request) -> JSONResponse:
    return JSONResponse({"data": "value"})
```

## Security

### Authentication
- **Development**: Server runs without authentication by default
- **Production**: Enable Auth0 OAuth for secure remote access
- **PKCE**: Full OAuth 2.1 PKCE support for enhanced security
- **Token Encryption**: Upstream OAuth tokens encrypted at rest

### Best Practices
1. Always use HTTPS in production (set `SERVER_BASE_URL` to https://)
2. Keep `REQUIRE_CONSENT=true` in production
3. Use strong `JWT_SIGNING_KEY` (minimum 12 characters)
4. Restrict `ALLOWED_CLIENT_REDIRECT_URIS` appropriately
5. Store secrets in environment variables, never in code
6. Rotate credentials regularly in Auth0

See [AUTH0_SETUP.md](AUTH0_SETUP.md) for complete security guidelines.

## Deployment

### Local Development
```bash
python server.py
```

### Production (Railway, Heroku, etc.)
1. Set environment variables in your deployment platform
2. Ensure `SERVER_BASE_URL` uses HTTPS
3. Configure Auth0 with production URLs
4. Use a process manager or container orchestration

Example Railway deployment:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Add environment variables in Railway dashboard.

## Troubleshooting

### Server won't start
- Check Python version: `python --version` (requires 3.8+)
- Verify dependencies: `pip install -r requirements.txt`
- Check port availability: `lsof -i :8000` (macOS/Linux)

### Auth0 errors
- Verify environment variables are set correctly
- Check Auth0 dashboard for application configuration
- Ensure callback URLs are whitelisted in Auth0
- See [AUTH0_SETUP.md](AUTH0_SETUP.md) for detailed troubleshooting

### Connection errors
- Verify server is running: `curl http://localhost:8000/health`
- Check firewall settings
- Verify MCP client configuration

## Contributing

This is a personal project, but suggestions and improvements are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Resources

- [FastMCP Documentation](https://gofastmcp.com)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Auth0 Documentation](https://auth0.com/docs)
- [Claude Desktop Documentation](https://claude.ai/docs)

## Support

For issues and questions:
- Check [AUTH0_SETUP.md](AUTH0_SETUP.md) for Auth0-related questions
- Review FastMCP documentation at https://gofastmcp.com
- Open an issue in this repository

## Roadmap

- ✅ Phase 1: Basic MCP server with Auth0 OAuth
- 🚧 Phase 2: Google Calendar integration
- 🚧 Phase 3: TickTick task management
- 🚧 Phase 4: Obsidian notes integration
- 🚧 Phase 5: Health data management
- 🚧 Phase 6: Advanced AI-powered features

---

Made with ❤️ using [FastMCP](https://gofastmcp.com)
