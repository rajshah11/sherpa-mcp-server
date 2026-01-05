#!/usr/bin/env python3
"""
Sherpa MCP Server - A remote MCP server with Auth0 OAuth authentication.

This server acts as a personal assistant, managing calendar events, tasks, notes,
health data, and more. It uses Auth0 for secure authentication.
"""
import os
import datetime
import logging
from fastmcp import FastMCP, Context
from fastmcp.server.auth.providers.auth0 import Auth0Provider
from starlette.requests import Request
from starlette.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Auth0 OAuth Configuration
# ============================================================================

# Check if Auth0 is configured
auth0_enabled = all([
    os.getenv("AUTH0_CONFIG_URL"),
    os.getenv("AUTH0_CLIENT_ID"),
    os.getenv("AUTH0_CLIENT_SECRET"),
    os.getenv("AUTH0_AUDIENCE")
])

if auth0_enabled:
    logger.info("Configuring Auth0 OAuth authentication...")
    auth = Auth0Provider(
        config_url=os.getenv("AUTH0_CONFIG_URL"),
        client_id=os.getenv("AUTH0_CLIENT_ID"),
        client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
        audience=os.getenv("AUTH0_AUDIENCE"),
        base_url=os.getenv("SERVER_BASE_URL", "http://localhost:8000"),

        # Optional: customize settings
        required_scopes=["openid", "profile"],
        allowed_client_redirect_uris=[
            "http://localhost:*",  # Allow MCP clients on any localhost port
        ],
        require_authorization_consent=os.getenv("REQUIRE_CONSENT", "true").lower() == "true",
    )
    logger.info("Auth0 OAuth configured successfully")
else:
    logger.warning("Auth0 not configured - running without authentication")
    logger.warning("Set AUTH0_* environment variables to enable authentication")
    auth = None

# ============================================================================
# Initialize FastMCP Server
# ============================================================================

server = FastMCP(
    name="Sherpa MCP Server",
    instructions="A remote MCP server providing personal assistant capabilities with secure Auth0 authentication",
    version="1.0.0",
    auth=auth  # None if not configured, Auth0Provider if configured
)

# ============================================================================
# MCP Tools
# ============================================================================

@server.tool(
    name="test_connection",
    description="Test the connection to the MCP server and get server status"
)
async def test_connection(ctx: Context) -> str:
    """Test the connection to the server.

    Returns:
        A confirmation message with server timestamp
    """
    await ctx.info("Testing connection to Sherpa MCP Server...")
    timestamp = datetime.datetime.now().isoformat()
    auth_status = "authenticated" if auth0_enabled else "no authentication"
    return f"✓ Connection successful!\nServer time: {timestamp}\nAuth status: {auth_status}"

@server.tool(
    name="echo",
    description="Echo back a message with optional formatting"
)
async def echo_tool(
    message: str,
    uppercase: bool = False,
    prefix: str = "",
    ctx: Context = None
) -> str:
    """Echo back a message with optional formatting.

    Args:
        message: The message to echo
        uppercase: Convert to uppercase (default: False)
        prefix: Optional prefix to add
        ctx: FastMCP context

    Returns:
        The formatted message
    """
    if ctx:
        await ctx.info(f"Echoing message: {message[:50]}...")

    result = message
    if uppercase:
        result = result.upper()
    if prefix:
        result = f"{prefix}: {result}"

    return result

@server.tool(
    name="get_server_time",
    description="Get the current server time in ISO format"
)
def get_server_time() -> dict:
    """Get the current server time.

    Returns:
        Dictionary with timestamp and timezone info
    """
    now = datetime.datetime.now()
    return {
        "timestamp": now.isoformat(),
        "utc_timestamp": datetime.datetime.utcnow().isoformat(),
        "timezone": "local"
    }

# ============================================================================
# Custom HTTP Endpoints
# ============================================================================

@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring and load balancers.

    Returns:
        JSON response with health status
    """
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "sherpa-mcp-server",
        "version": "1.0.0",
        "auth_enabled": auth0_enabled
    })

@server.custom_route("/info", methods=["GET"])
async def server_info(request: Request) -> JSONResponse:
    """Server information endpoint.

    Returns:
        JSON response with server details
    """
    return JSONResponse({
        "name": "Sherpa MCP Server",
        "version": "1.0.0",
        "description": "Remote MCP server with personal assistant capabilities",
        "mcp_protocol": "Model Context Protocol",
        "transport": "streamable-http",
        "authentication": {
            "enabled": auth0_enabled,
            "provider": "Auth0" if auth0_enabled else None
        },
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "mcp": "/mcp",
            "oauth_metadata": "/.well-known/oauth-authorization-server" if auth0_enabled else None
        },
        "tools": [
            "test_connection",
            "echo",
            "get_server_time"
        ],
        "timestamp": datetime.datetime.now().isoformat()
    })

@server.custom_route("/", methods=["GET"])
async def root(request: Request) -> JSONResponse:
    """Root endpoint with basic information.

    Returns:
        JSON response with welcome message
    """
    return JSONResponse({
        "message": "Welcome to Sherpa MCP Server",
        "version": "1.0.0",
        "description": "Your personal assistant MCP server",
        "auth_enabled": auth0_enabled,
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "mcp": "/mcp"
        },
        "documentation": "See README.md for setup instructions"
    })

# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Sherpa MCP Server v1.0.0")
    logger.info("=" * 60)
    logger.info(f"Authentication: {'Enabled (Auth0)' if auth0_enabled else 'Disabled'}")
    logger.info(f"Server URL: {os.getenv('SERVER_BASE_URL', 'http://localhost:8000')}")
    logger.info("=" * 60)

    # Run the server with streamable-http transport
    server.run(
        transport="streamable-http",
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", "8000")),
        show_banner=True
    )
