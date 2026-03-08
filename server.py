#!/usr/bin/env python3
"""
Sherpa MCP Server - A remote MCP server with Auth0 OAuth authentication.

This server acts as a personal assistant, managing calendar events, tasks, notes,
health data, and more. It uses Auth0 for secure authentication and FastMCP's
server composition to organize tools into logical modules.
"""
import asyncio
import datetime
import logging
import os
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.auth0 import Auth0Provider
import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse

from config import get_timezone
from google_calendar import is_calendar_configured
from meal_logger import is_meal_logger_configured
from servers.calendar import calendar_server
from servers.core import core_server
from servers.meal_logger import meal_logger_server
from servers.ticktick import ticktick_server
from ticktick import is_ticktick_configured

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERSION = "1.0.0"

# ============================================================================
# Auth0 OAuth Configuration
# ============================================================================

AUTH0_ENV_VARS = ["AUTH0_CONFIG_URL", "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET", "AUTH0_AUDIENCE"]
auth0_enabled = all(os.getenv(var) for var in AUTH0_ENV_VARS)


def _parse_csv_env(var_name: str, default: list[str]) -> list[str]:
    """Parse comma-separated environment variable into a cleaned list."""
    value = os.getenv(var_name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


DEFAULT_ALLOWED_REDIRECT_URIS = [
    "http://localhost:*",
    "https://chat.openai.com/aip/*",
    "https://chatgpt.com/aip/*",
]

required_scopes = _parse_csv_env("AUTH_REQUIRED_SCOPES", default=[])
allowed_redirect_uris = _parse_csv_env("AUTH_ALLOWED_REDIRECT_URIS", default=DEFAULT_ALLOWED_REDIRECT_URIS)

if auth0_enabled:
    logger.info("Configuring Auth0 OAuth authentication...")
    auth = Auth0Provider(
        config_url=os.getenv("AUTH0_CONFIG_URL"),
        client_id=os.getenv("AUTH0_CLIENT_ID"),
        client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
        audience=os.getenv("AUTH0_AUDIENCE"),
        base_url=os.getenv("SERVER_BASE_URL", "http://localhost:8000"),
        required_scopes=required_scopes,
        allowed_client_redirect_uris=allowed_redirect_uris,
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
    version=VERSION,
    auth=auth
)


async def compose_servers():
    """Import all sub-servers into the main server."""
    await server.import_server(core_server)
    await server.import_server(calendar_server)
    await server.import_server(ticktick_server)
    await server.import_server(meal_logger_server)
    logger.info("Server composition complete")


# ============================================================================
# Custom HTTP Endpoints
# ============================================================================

def _get_integration_status() -> dict:
    """Return current integration status."""
    return {
        "google_calendar": is_calendar_configured(),
        "ticktick": is_ticktick_configured(),
        "meal_logger": is_meal_logger_configured()
    }


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring and load balancers."""
    integrations = _get_integration_status()
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "sherpa-mcp-server",
        "version": VERSION,
        "auth_enabled": auth0_enabled,
        "google_calendar_enabled": integrations["google_calendar"],
        "ticktick_enabled": integrations["ticktick"],
        "meal_logger_enabled": integrations["meal_logger"]
    })


@server.custom_route("/info", methods=["GET"])
async def server_info(request: Request) -> JSONResponse:
    """Server information endpoint."""
    return JSONResponse({
        "name": "Sherpa MCP Server",
        "version": VERSION,
        "description": "Remote MCP server with personal assistant capabilities",
        "mcp_protocol": "Model Context Protocol",
        "transport": "streamable-http",
        "authentication": {
            "enabled": auth0_enabled,
            "provider": "Auth0" if auth0_enabled else None,
            "required_scopes": required_scopes if auth0_enabled else [],
            "allowed_client_redirect_uris": allowed_redirect_uris if auth0_enabled else []
        },
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "mcp": "/mcp",
            "oauth_metadata": "/.well-known/oauth-authorization-server" if auth0_enabled else None
        },
        "integrations": _get_integration_status(),
        "timestamp": datetime.datetime.now().isoformat()
    })


@server.custom_route("/.well-known/openid-configuration", methods=["GET"])
async def openid_configuration(request: Request) -> JSONResponse:
    """
    OIDC discovery endpoint at the MCP server origin.

    Some MCP clients probe this path on the server host during OAuth discovery.
    We proxy Auth0's discovery document so discovery succeeds consistently.
    """
    if not auth0_enabled:
        return JSONResponse(
            {
                "error": "authentication_not_configured",
                "error_description": "Auth0 is not configured on this server"
            },
            status_code=404,
        )

    config_url = os.getenv("AUTH0_CONFIG_URL")
    if not config_url:
        return JSONResponse(
            {
                "error": "server_error",
                "error_description": "AUTH0_CONFIG_URL is not set"
            },
            status_code=500,
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(config_url)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return JSONResponse(payload)
    except Exception as exc:  # pragma: no cover - defensive runtime path
        logger.exception("Failed to fetch Auth0 OIDC discovery document")
        return JSONResponse(
            {
                "error": "server_error",
                "error_description": f"Failed to fetch Auth0 discovery document: {exc}"
            },
            status_code=502,
        )


@server.custom_route("/", methods=["GET"])
async def root(request: Request) -> JSONResponse:
    """Root endpoint with basic information."""
    return JSONResponse({
        "message": "Welcome to Sherpa MCP Server",
        "version": VERSION,
        "description": "Your personal assistant MCP server",
        "auth_enabled": auth0_enabled,
        "endpoints": {"health": "/health", "info": "/info", "mcp": "/mcp"},
        "documentation": "See README.md for setup instructions"
    })


# ============================================================================
# Server Entry Point
# ============================================================================

def _log_startup_info():
    """Log startup configuration details."""
    integrations = _get_integration_status()
    separator = "=" * 60

    logger.info(separator)
    logger.info(f"Starting Sherpa MCP Server v{VERSION}")
    logger.info(separator)
    logger.info(f"Timezone: {get_timezone()}")
    logger.info(f"Authentication: {'Enabled (Auth0)' if auth0_enabled else 'Disabled'}")
    logger.info(f"Google Calendar: {'Enabled' if integrations['google_calendar'] else 'Disabled'}")
    logger.info(f"TickTick: {'Enabled' if integrations['ticktick'] else 'Disabled'}")
    logger.info(f"Meal Logger: {'Enabled' if integrations['meal_logger'] else 'Disabled'}")
    logger.info(f"Server URL: {os.getenv('SERVER_BASE_URL', 'http://localhost:8000')}")
    logger.info(separator)


if __name__ == "__main__":
    _log_startup_info()
    asyncio.run(compose_servers())

    port = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8000")))
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    logger.info(f"Starting server on {host}:{port}")

    server.run(transport="streamable-http", host=host, port=port, show_banner=True)
