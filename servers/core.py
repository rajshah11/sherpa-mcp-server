"""
Core MCP Server - Basic utility tools.
"""

import datetime
from fastmcp import FastMCP, Context

core_server = FastMCP(name="Core Tools")


@core_server.tool(
    name="test_connection",
    description="Test the connection to the MCP server and get server status"
)
async def test_connection(ctx: Context) -> str:
    """Test the connection to the server."""
    await ctx.info("Testing connection to Sherpa MCP Server...")
    timestamp = datetime.datetime.now().isoformat()
    return f"Connection successful!\nServer time: {timestamp}"


@core_server.tool(
    name="echo",
    description="Echo back a message with optional formatting"
)
async def echo_tool(
    message: str,
    uppercase: bool = False,
    prefix: str = "",
    ctx: Context = None
) -> str:
    """Echo back a message with optional formatting."""
    if ctx:
        await ctx.info(f"Echoing message: {message[:50]}...")

    result = message
    if uppercase:
        result = result.upper()
    if prefix:
        result = f"{prefix}: {result}"

    return result


@core_server.tool(
    name="get_server_time",
    description="Get the current server time in ISO format"
)
def get_server_time() -> dict:
    """Get the current server time."""
    now = datetime.datetime.now()
    return {
        "timestamp": now.isoformat(),
        "utc_timestamp": datetime.datetime.utcnow().isoformat(),
        "timezone": "local"
    }
