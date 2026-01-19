#!/usr/bin/env python3
"""
Sherpa MCP Server - A remote MCP server with Auth0 OAuth authentication.

This server acts as a personal assistant, managing calendar events, tasks, notes,
health data, and more. It uses Auth0 for secure authentication and FastMCP's
server composition to organize tools into logical modules.
"""
import os
import asyncio
import datetime
import logging
from fastmcp import FastMCP
from fastmcp.server.auth.providers.auth0 import Auth0Provider
from starlette.requests import Request
from starlette.responses import JSONResponse
from dotenv import load_dotenv

# Sub-servers
from servers.core import core_server
from servers.calendar import calendar_server
from servers.ticktick import ticktick_server

# Integration status checks
from google_calendar import is_calendar_configured
from ticktick import is_ticktick_configured

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Auth0 OAuth Configuration
# ============================================================================

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
        required_scopes=["openid", "profile"],
        allowed_client_redirect_uris=["http://localhost:*"],
        require_authorization_consent=os.getenv("REQUIRE_CONSENT", "true").lower() == "true",
    )
    logger.info("Auth0 OAuth configured successfully")
else:
    logger.warning("Auth0 not configured - running without authentication")
    auth = None

# ============================================================================
# Initialize Main Server with Composition
# ============================================================================

server = FastMCP(
    name="Sherpa MCP Server",
    instructions="A remote MCP server providing personal assistant capabilities with secure Auth0 authentication",
    version="1.0.0",
    auth=auth
)


async def compose_servers():
    """Import all sub-servers into the main server."""
    # Import without prefix since tools already have appropriate names
    await server.import_server(core_server)
    await server.import_server(calendar_server)
    await server.import_server(ticktick_server)
    logger.info("Server composition complete")


# ============================================================================
# Custom HTTP Endpoints
# ============================================================================

@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring and load balancers."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "sherpa-mcp-server",
        "version": "1.0.0",
        "auth_enabled": auth0_enabled,
        "google_calendar_enabled": is_calendar_configured(),
        "ticktick_enabled": is_ticktick_configured()
    })


@server.custom_route("/info", methods=["GET"])
async def server_info(request: Request) -> JSONResponse:
    """Server information endpoint."""
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
        "integrations": {
            "google_calendar": is_calendar_configured(),
            "ticktick": is_ticktick_configured()
        },
        "timestamp": datetime.datetime.now().isoformat()
    })


@server.custom_route("/", methods=["GET"])
async def root(request: Request) -> JSONResponse:
    """Root endpoint with basic information."""
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
    logger.info(f"Google Calendar: {'Enabled' if is_calendar_configured() else 'Disabled'}")
    logger.info(f"TickTick: {'Enabled' if is_ticktick_configured() else 'Disabled'}")
    logger.info(f"Server URL: {os.getenv('SERVER_BASE_URL', 'http://localhost:8000')}")
    logger.info("=" * 60)

    # Compose servers before running
    asyncio.run(compose_servers())

    # Run the server
    port = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8000")))
    host = os.getenv("SERVER_HOST", "0.0.0.0")

    logger.info(f"Starting server on {host}:{port}")

    server.run(
        transport="streamable-http",
        host=host,
        port=port,
        show_banner=True
    )
