"""
Obsidian Module

Provides direct markdown file manipulation for Obsidian vaults.
Requires OBSIDIAN_VAULT_PATH environment variable to be set.
Designed to work with Syncthing for cross-device synchronization.
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_timezone

logger = logging.getLogger(__name__)


class ObsidianClient:
    """Client for manipulating Obsidian markdown files."""

    def __init__(self):
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
        if not vault_path:
            raise ValueError("OBSIDIAN_VAULT_PATH environment variable is required")
        self._vault_path = Path(vault_path)
        self._ensure_vault_dir()

    def _ensure_vault_dir(self) -> None:
        """Create vault directory if it doesn't exist."""
        self._vault_path.mkdir(parents=True, exist_ok=True)

        # Create default folders
        (self._vault_path / "Daily Notes").mkdir(exist_ok=True)
        (self._vault_path / "Tasks").mkdir(exist_ok=True)
        (self._vault_path / "Journal").mkdir(exist_ok=True)

    def _get_note_path(self, note_path: str) -> Path:
        """
        Get full path to a note file.

        Args:
            note_path: Relative path from vault root (e.g., "Daily Notes/2026-01-23.md")
        """
        # Ensure .md extension
        if not note_path.endswith(".md"):
            note_path += ".md"

        full_path = self._vault_path / note_path

        # Security check: ensure path is within vault
        try:
            full_path.resolve().relative_to(self._vault_path.resolve())
        except ValueError:
            raise ValueError(f"Path {note_path} is outside vault")

        return full_path

    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """
        Parse YAML frontmatter from markdown content.

        Returns:
            (frontmatter_dict, content_without_frontmatter)
        """
        frontmatter = {}
        body = content

        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1]
                body = parts[2]

                # Simple YAML parsing (key: value)
                for line in frontmatter_text.split("\n"):
                    line = line.strip()
                    if ":" in line:
                        key, value = line.split(":", 1)
                        frontmatter[key.strip()] = value.strip()

        return frontmatter, body

    def _build_frontmatter(self, metadata: Dict[str, Any]) -> str:
        """Build YAML frontmatter string from metadata dict."""
        if not metadata:
            return ""

        lines = ["---"]
        for key, value in metadata.items():
            lines.append(f"{key}: {value}")
        lines.append("---\n")
        return "\n".join(lines)

    def _now_iso(self) -> str:
        """Get current time in ISO format (local timezone)."""
        return datetime.now(get_timezone()).isoformat()

    def _today(self) -> str:
        """Get today's date as YYYY-MM-DD in configured timezone."""
        return datetime.now(get_timezone()).strftime("%Y-%m-%d")

    def create_note(
        self,
        note_path: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new note.

        Args:
            note_path: Relative path from vault root (e.g., "Daily Notes/2026-01-23.md")
            content: Markdown content
            metadata: Optional frontmatter metadata
            overwrite: If True, overwrite existing file
        """
        try:
            full_path = self._get_note_path(note_path)

            if full_path.exists() and not overwrite:
                return {
                    "error": f"Note already exists: {note_path}. Use overwrite=True to replace."
                }

            # Ensure parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Add created timestamp to metadata
            if metadata is None:
                metadata = {}
            if "created" not in metadata:
                metadata["created"] = self._now_iso()

            # Build final content
            final_content = self._build_frontmatter(metadata)
            final_content += content

            # Write file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(final_content)

            return {
                "status": "success",
                "message": f"Note created: {note_path}",
                "path": str(full_path.relative_to(self._vault_path)),
            }

        except Exception as e:
            logger.error(f"Failed to create note {note_path}: {e}")
            return {"error": str(e)}

    def read_note(self, note_path: str) -> Dict[str, Any]:
        """
        Read a note.

        Args:
            note_path: Relative path from vault root
        """
        try:
            full_path = self._get_note_path(note_path)

            if not full_path.exists():
                return {"error": f"Note not found: {note_path}"}

            with open(full_path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            frontmatter, content = self._parse_frontmatter(raw_content)

            return {
                "status": "success",
                "path": str(full_path.relative_to(self._vault_path)),
                "metadata": frontmatter,
                "content": content,
                "raw_content": raw_content,
            }

        except Exception as e:
            logger.error(f"Failed to read note {note_path}: {e}")
            return {"error": str(e)}

    def update_note(
        self,
        note_path: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        append: bool = False,
    ) -> Dict[str, Any]:
        """
        Update an existing note.

        Args:
            note_path: Relative path from vault root
            content: New content (if None, keeps existing)
            metadata: New/updated metadata (merged with existing)
            append: If True, append content instead of replacing
        """
        try:
            full_path = self._get_note_path(note_path)

            if not full_path.exists():
                return {"error": f"Note not found: {note_path}"}

            # Read existing content
            with open(full_path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            existing_metadata, existing_content = self._parse_frontmatter(raw_content)

            # Update metadata
            new_metadata = {**existing_metadata}
            if metadata:
                new_metadata.update(metadata)
            new_metadata["updated"] = self._now_iso()

            # Update content
            if content is not None:
                if append:
                    new_content = existing_content + "\n" + content
                else:
                    new_content = content
            else:
                new_content = existing_content

            # Build final content
            final_content = self._build_frontmatter(new_metadata)
            final_content += new_content

            # Write file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(final_content)

            return {
                "status": "success",
                "message": f"Note updated: {note_path}",
                "path": str(full_path.relative_to(self._vault_path)),
            }

        except Exception as e:
            logger.error(f"Failed to update note {note_path}: {e}")
            return {"error": str(e)}

    def delete_note(self, note_path: str) -> Dict[str, Any]:
        """
        Delete a note.

        Args:
            note_path: Relative path from vault root
        """
        try:
            full_path = self._get_note_path(note_path)

            if not full_path.exists():
                return {"error": f"Note not found: {note_path}"}

            full_path.unlink()

            return {
                "status": "success",
                "message": f"Note deleted: {note_path}",
            }

        except Exception as e:
            logger.error(f"Failed to delete note {note_path}: {e}")
            return {"error": str(e)}

    def list_notes(
        self,
        folder: Optional[str] = None,
        pattern: Optional[str] = None,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """
        List notes in the vault.

        Args:
            folder: Optional folder to search in (relative to vault root)
            pattern: Optional glob pattern (e.g., "*.md", "daily-*.md")
            recursive: If True, search recursively
        """
        try:
            search_path = self._vault_path
            if folder:
                search_path = self._vault_path / folder
                if not search_path.exists():
                    return {"error": f"Folder not found: {folder}"}

            glob_pattern = pattern or "*.md"
            if recursive:
                glob_pattern = "**/" + glob_pattern

            notes = []
            for note_path in search_path.glob(glob_pattern):
                if note_path.is_file():
                    relative_path = note_path.relative_to(self._vault_path)
                    notes.append({
                        "path": str(relative_path),
                        "name": note_path.name,
                        "modified": datetime.fromtimestamp(
                            note_path.stat().st_mtime, tz=get_timezone()
                        ).isoformat(),
                    })

            # Sort by modified time (newest first)
            notes.sort(key=lambda x: x["modified"], reverse=True)

            return {
                "status": "success",
                "count": len(notes),
                "notes": notes,
            }

        except Exception as e:
            logger.error(f"Failed to list notes: {e}")
            return {"error": str(e)}

    def search_notes(self, query: str, folder: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for notes containing specific text.

        Args:
            query: Search query (case-insensitive)
            folder: Optional folder to search in
        """
        try:
            search_path = self._vault_path
            if folder:
                search_path = self._vault_path / folder
                if not search_path.exists():
                    return {"error": f"Folder not found: {folder}"}

            results = []
            pattern = re.compile(re.escape(query), re.IGNORECASE)

            for note_path in search_path.glob("**/*.md"):
                if note_path.is_file():
                    try:
                        with open(note_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        matches = pattern.findall(content)
                        if matches:
                            relative_path = note_path.relative_to(self._vault_path)

                            # Get context around first match
                            match_pos = content.lower().find(query.lower())
                            context_start = max(0, match_pos - 100)
                            context_end = min(len(content), match_pos + 100)
                            context = content[context_start:context_end].strip()

                            results.append({
                                "path": str(relative_path),
                                "name": note_path.name,
                                "matches": len(matches),
                                "context": f"...{context}...",
                            })

                    except Exception as e:
                        logger.warning(f"Failed to search {note_path}: {e}")
                        continue

            # Sort by number of matches
            results.sort(key=lambda x: x["matches"], reverse=True)

            return {
                "status": "success",
                "query": query,
                "count": len(results),
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to search notes: {e}")
            return {"error": str(e)}

    def create_daily_note(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Create or update a daily note.

        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
        """
        target_date = date or self._today()
        note_path = f"Daily Notes/{target_date}.md"

        # Check if note already exists
        full_path = self._get_note_path(note_path)
        if full_path.exists():
            return {
                "status": "success",
                "message": f"Daily note already exists: {target_date}",
                "path": str(full_path.relative_to(self._vault_path)),
                "exists": True,
            }

        # Create new daily note
        metadata = {
            "date": target_date,
            "type": "daily-note",
        }

        content = f"""# {target_date}

## Tasks
- [ ]

## Notes


## Reflection


"""

        return self.create_note(note_path, content, metadata)


_client: Optional[ObsidianClient] = None


def get_obsidian_client() -> ObsidianClient:
    """Get or create the ObsidianClient singleton."""
    global _client
    if _client is None:
        _client = ObsidianClient()
    return _client


def is_obsidian_configured() -> bool:
    """Check if Obsidian vault path is configured."""
    return bool(os.getenv("OBSIDIAN_VAULT_PATH"))
