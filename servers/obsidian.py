"""
Obsidian MCP Server - Markdown note manipulation tools.
"""

import logging
from typing import Optional

from fastmcp import Context, FastMCP

from obsidian import get_obsidian_client, is_obsidian_configured

logger = logging.getLogger(__name__)

obsidian_server = FastMCP(name="Obsidian")

NOT_CONFIGURED_ERROR = {
    "error": "Obsidian not configured",
    "message": "OBSIDIAN_VAULT_PATH environment variable is required. Set it to the path of your Obsidian vault."
}


@obsidian_server.tool(
    name="obsidian_create_note",
    description="Create a new markdown note in the Obsidian vault"
)
async def create_note(
    note_path: str,
    content: str,
    tags: Optional[str] = None,
    overwrite: bool = False,
    ctx: Context = None
) -> dict:
    """
    Create a new note in the Obsidian vault.

    Args:
        note_path: Relative path from vault root (e.g., "Daily Notes/2026-01-23.md" or "Tasks/project-ideas")
        content: Markdown content for the note
        tags: Comma-separated tags (e.g., "work,urgent,meeting")
        overwrite: If True, overwrite existing file (default: False)
    """
    if not is_obsidian_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Creating note: {note_path}")

        metadata = {}
        if tags:
            metadata["tags"] = tags

        return get_obsidian_client().create_note(
            note_path=note_path,
            content=content,
            metadata=metadata,
            overwrite=overwrite
        )
    except Exception as e:
        logger.error(f"Failed to create note: {e}")
        return {"error": str(e)}


@obsidian_server.tool(
    name="obsidian_read_note",
    description="Read a markdown note from the Obsidian vault"
)
async def read_note(
    note_path: str,
    ctx: Context = None
) -> dict:
    """
    Read a note from the Obsidian vault.

    Args:
        note_path: Relative path from vault root (e.g., "Daily Notes/2026-01-23.md")
    """
    if not is_obsidian_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Reading note: {note_path}")

        return get_obsidian_client().read_note(note_path)
    except Exception as e:
        logger.error(f"Failed to read note: {e}")
        return {"error": str(e)}


@obsidian_server.tool(
    name="obsidian_update_note",
    description="Update an existing markdown note"
)
async def update_note(
    note_path: str,
    content: Optional[str] = None,
    tags: Optional[str] = None,
    append: bool = False,
    ctx: Context = None
) -> dict:
    """
    Update an existing note in the Obsidian vault.

    Args:
        note_path: Relative path from vault root
        content: New content (if None, keeps existing content)
        tags: Comma-separated tags to add/update
        append: If True, append content instead of replacing (default: False)
    """
    if not is_obsidian_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            action = "Appending to" if append else "Updating"
            await ctx.info(f"{action} note: {note_path}")

        metadata = {}
        if tags:
            metadata["tags"] = tags

        return get_obsidian_client().update_note(
            note_path=note_path,
            content=content,
            metadata=metadata if metadata else None,
            append=append
        )
    except Exception as e:
        logger.error(f"Failed to update note: {e}")
        return {"error": str(e)}


@obsidian_server.tool(
    name="obsidian_delete_note",
    description="Delete a markdown note from the Obsidian vault"
)
async def delete_note(
    note_path: str,
    ctx: Context = None
) -> dict:
    """
    Delete a note from the Obsidian vault.

    Args:
        note_path: Relative path from vault root
    """
    if not is_obsidian_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Deleting note: {note_path}")

        return get_obsidian_client().delete_note(note_path)
    except Exception as e:
        logger.error(f"Failed to delete note: {e}")
        return {"error": str(e)}


@obsidian_server.tool(
    name="obsidian_list_notes",
    description="List markdown notes in the vault"
)
async def list_notes(
    folder: Optional[str] = None,
    pattern: Optional[str] = None,
    recursive: bool = True,
    ctx: Context = None
) -> dict:
    """
    List notes in the Obsidian vault.

    Args:
        folder: Optional folder to search in (relative to vault root, e.g., "Daily Notes")
        pattern: Optional glob pattern (e.g., "*.md", "daily-*.md")
        recursive: If True, search recursively in subfolders (default: True)
    """
    if not is_obsidian_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            location = folder or "vault"
            await ctx.info(f"Listing notes in {location}")

        return get_obsidian_client().list_notes(
            folder=folder,
            pattern=pattern,
            recursive=recursive
        )
    except Exception as e:
        logger.error(f"Failed to list notes: {e}")
        return {"error": str(e)}


@obsidian_server.tool(
    name="obsidian_search_notes",
    description="Search for text within notes"
)
async def search_notes(
    query: str,
    folder: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Search for notes containing specific text.

    Args:
        query: Search query (case-insensitive)
        folder: Optional folder to search in (relative to vault root)
    """
    if not is_obsidian_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Searching for: {query}")

        return get_obsidian_client().search_notes(
            query=query,
            folder=folder
        )
    except Exception as e:
        logger.error(f"Failed to search notes: {e}")
        return {"error": str(e)}


@obsidian_server.tool(
    name="obsidian_create_daily_note",
    description="Create or get today's daily note"
)
async def create_daily_note(
    date: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    Create or get a daily note.

    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
    """
    if not is_obsidian_configured():
        return NOT_CONFIGURED_ERROR

    try:
        if ctx:
            await ctx.info(f"Creating daily note for: {date or 'today'}")

        return get_obsidian_client().create_daily_note(date)
    except Exception as e:
        logger.error(f"Failed to create daily note: {e}")
        return {"error": str(e)}
