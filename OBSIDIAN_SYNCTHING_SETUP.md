# Obsidian + Syncthing Setup Guide

This guide will help you set up Obsidian integration with Syncthing for cross-device synchronization. The Sherpa MCP Server will directly manipulate markdown files in your Obsidian vault, and Syncthing will keep those files synchronized across all your devices.

## Overview

**Architecture:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Claude/MCP    │────▶│  Sherpa Server  │────▶│ Obsidian Vault  │
│     Client      │     │   (Obsidian)    │     │  (Markdown)     │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                                                    Syncthing
                                                          │
                        ┌─────────────────────────────────┼─────────────────────────────────┐
                        │                                 │                                 │
                        ▼                                 ▼                                 ▼
                ┌──────────────┐                  ┌──────────────┐                  ┌──────────────┐
                │  Desktop PC  │                  │    Laptop    │                  │    Mobile    │
                │  (Obsidian)  │                  │  (Obsidian)  │                  │  (Obsidian)  │
                └──────────────┘                  └──────────────┘                  └──────────────┘
```

**Key Benefits:**
- Direct markdown file manipulation (no API dependencies)
- Real-time sync across all devices
- Works offline on each device
- No vendor lock-in (standard markdown files)
- Full Obsidian feature compatibility

## Prerequisites

1. **Obsidian** - Install from [obsidian.md](https://obsidian.md)
2. **Syncthing** - Install from [syncthing.net](https://syncthing.net)
3. **Sherpa MCP Server** - Running instance (see main README.md)

## Step 1: Create Obsidian Vault

### Option A: New Vault

1. Open Obsidian
2. Click "Create new vault"
3. Name it (e.g., "Sherpa Notes")
4. Choose a location (e.g., `~/Documents/ObsidianVault`)
5. Create the vault

### Option B: Use Existing Vault

If you already have an Obsidian vault, you can use it directly. The Sherpa tools will create notes in subfolders to keep things organized.

## Step 2: Configure Sherpa MCP Server

1. Set the vault path in your `.env` file:

```bash
OBSIDIAN_VAULT_PATH=/path/to/your/vault
```

**Examples:**
- macOS: `OBSIDIAN_VAULT_PATH=/Users/username/Documents/ObsidianVault`
- Linux: `OBSIDIAN_VAULT_PATH=/home/username/Documents/ObsidianVault`
- Windows: `OBSIDIAN_VAULT_PATH=C:/Users/username/Documents/ObsidianVault`

2. Restart the Sherpa server:

```bash
python server.py
```

3. Verify Obsidian is enabled:

```bash
curl http://localhost:8000/health
```

Look for `"obsidian_enabled": true` in the response.

## Step 3: Install Syncthing

### macOS

```bash
brew install syncthing
brew services start syncthing
```

Or download from: https://syncthing.net/downloads/

### Linux (Debian/Ubuntu)

```bash
sudo apt install syncthing
systemctl --user enable syncthing
systemctl --user start syncthing
```

### Windows

Download installer from: https://syncthing.net/downloads/

### Mobile (Android/iOS)

- **Android**: Install "Syncthing" from Google Play Store
- **iOS**: Install "Möbius Sync" from App Store (Syncthing-compatible)

## Step 4: Configure Syncthing

### On Your Primary Device (e.g., Desktop)

1. Open Syncthing web UI: http://localhost:8384
2. Click "Add Folder"
3. Configure the folder:
   - **Folder Label**: "Obsidian Vault"
   - **Folder Path**: `/path/to/your/vault` (same as OBSIDIAN_VAULT_PATH)
   - **Folder ID**: (auto-generated, e.g., `obsidian-vault`)
4. Click "Save"

### On Secondary Devices

1. Open Syncthing web UI on the second device
2. In the "Remote Devices" section, you'll see a device ID from your primary device
3. Accept the connection
4. Accept the folder share request
5. Set the local path where you want the vault synced

**Important:** Make sure the Obsidian app on each device points to the synced folder location.

## Step 5: Set Up Obsidian on Each Device

### Desktop/Laptop

1. Open Obsidian
2. Click "Open folder as vault"
3. Select the Syncthing-synced folder
4. Open the vault

### Mobile

1. Ensure Syncthing has synced the vault to your mobile device
2. Open Obsidian mobile app
3. Tap "Open folder as vault"
4. Navigate to the Syncthing folder location
5. Open the vault

**Android:** Usually in `Internal Storage/Sync/ObsidianVault`
**iOS:** Depends on Möbius Sync configuration

## Step 6: Test the Integration

### Using MCP Tools

With Claude Desktop or any MCP client connected to Sherpa:

```
User: Create a test note in Obsidian

Claude will use: obsidian_create_note
- note_path: "test.md"
- content: "This is a test note created via MCP"
```

### Verify Sync

1. Check Obsidian on your primary device - you should see the new note
2. Wait a few seconds for Syncthing to sync
3. Check Obsidian on your secondary device - the note should appear
4. Edit the note in Obsidian on any device
5. Verify the changes sync to other devices

## Available MCP Tools

The Obsidian integration provides these tools:

### `obsidian_create_note`
Create a new markdown note
- **note_path**: Relative path from vault root (e.g., "Daily Notes/2026-01-23.md")
- **content**: Markdown content
- **tags**: Optional comma-separated tags
- **overwrite**: If true, replace existing file

### `obsidian_read_note`
Read a note from the vault
- **note_path**: Relative path to the note

### `obsidian_update_note`
Update an existing note
- **note_path**: Relative path to the note
- **content**: New content (optional)
- **tags**: Update tags (optional)
- **append**: If true, append content instead of replacing

### `obsidian_delete_note`
Delete a note
- **note_path**: Relative path to the note

### `obsidian_list_notes`
List notes in the vault
- **folder**: Optional folder to search in
- **pattern**: Optional glob pattern (e.g., "*.md", "daily-*.md")
- **recursive**: Search subdirectories (default: true)

### `obsidian_search_notes`
Search for text within notes
- **query**: Search term (case-insensitive)
- **folder**: Optional folder to limit search

### `obsidian_create_daily_note`
Create or get today's daily note
- **date**: Optional date in YYYY-MM-DD format (defaults to today)

## Vault Structure

The Sherpa server creates these default folders:

```
ObsidianVault/
├── Daily Notes/     # Daily notes (YYYY-MM-DD.md)
├── Tasks/           # Task and project notes
├── Journal/         # Journal entries
└── ...              # Your custom folders
```

## Usage Examples

### Create a Daily Note

```
User: Create today's daily note in Obsidian

Claude uses: obsidian_create_daily_note()
Creates: Daily Notes/2026-01-23.md with template
```

### Add Meeting Notes

```
User: Create a note about today's standup meeting

Claude uses: obsidian_create_note(
  note_path="Meetings/standup-2026-01-23.md",
  content="## Standup Notes\n\n- Discussed...",
  tags="meeting,standup"
)
```

### Search for Information

```
User: Find all notes mentioning "project deadline"

Claude uses: obsidian_search_notes(query="project deadline")
Returns: List of matching notes with context
```

### Append to Daily Note

```
User: Add "Buy milk" to today's tasks

Claude uses: obsidian_update_note(
  note_path="Daily Notes/2026-01-23.md",
  content="\n- [ ] Buy milk",
  append=true
)
```

## Frontmatter Support

Notes support YAML frontmatter for metadata:

```markdown
---
created: 2026-01-23T10:30:00-06:00
updated: 2026-01-23T14:15:00-06:00
tags: work,urgent
---

# Note Content

Your markdown content here...
```

The tools automatically manage `created` and `updated` timestamps.

## Syncthing Best Practices

### Ignore Patterns

Add these to Syncthing ignore patterns to avoid syncing temporary files:

```
.obsidian/workspace*
.obsidian/cache
.DS_Store
.trash/
.stfolder
*.tmp
```

### Conflict Resolution

If two devices edit the same file simultaneously:
1. Syncthing creates a conflict file (e.g., `note.sync-conflict-20260123-143022.md`)
2. Manually merge the changes in Obsidian
3. Delete the conflict file after merging

### Performance Tips

- **Selective Sync**: Only sync folders you need on mobile devices
- **Ignore Large Files**: Add patterns for large attachments if needed
- **Version Control**: Consider using git for vault history (optional)

## Troubleshooting

### Syncthing Not Syncing

1. Check Syncthing status: http://localhost:8384
2. Verify both devices show "Up to Date"
3. Check for errors in Syncthing logs
4. Ensure firewall allows Syncthing (default port 22000)

### Obsidian Can't Find Vault

1. Verify OBSIDIAN_VAULT_PATH is correct
2. Check folder permissions (readable/writable)
3. Ensure no typos in the path
4. Try absolute path instead of relative path

### Notes Not Appearing in Obsidian

1. Check Obsidian is pointing to the correct vault folder
2. Refresh Obsidian (Cmd+R / Ctrl+R)
3. Check Syncthing has finished syncing
4. Verify the file was created (check filesystem)

### Permission Errors

Ensure the Sherpa server has read/write access to the vault directory:

```bash
chmod -R u+rw /path/to/vault
```

## Security Considerations

### Local Network Sync

For security, Syncthing uses:
- **TLS encryption** for all connections
- **Device IDs** (not IP addresses) for authentication
- **Folder IDs** for selective sharing

### Remote Sync

To sync over the internet:
1. Syncthing uses relay servers (encrypted)
2. Or configure port forwarding (advanced)
3. Or use Syncthing's NAT traversal

### Sensitive Data

If your vault contains sensitive information:
- Enable Syncthing's **untrusted device** mode
- Consider encrypting the vault folder
- Use Obsidian's native encryption for specific notes
- Review Syncthing's privacy settings

## Advanced Configuration

### Custom Folder Structure

You can organize your vault however you like. The tools support any path structure:

```
obsidian_create_note(
  note_path="Work/Projects/Q1/initiative.md",
  content="..."
)
```

### Templates

Create template notes and use them as a base:

```python
# Read template
template = obsidian_read_note("Templates/meeting-notes.md")

# Create note from template
obsidian_create_note(
  note_path="Meetings/2026-01-23-standup.md",
  content=template["content"]
)
```

### Automation

Combine with other Sherpa tools:

```
User: Summarize today's calendar events and add to daily note

Claude will:
1. calendar_list_events() - Get today's events
2. Summarize the events
3. obsidian_update_note() - Append to daily note
```

## Support

- **Obsidian**: https://help.obsidian.md
- **Syncthing**: https://docs.syncthing.net
- **Sherpa Issues**: https://github.com/your-repo/issues

## What's Next?

- Set up daily note automation
- Create task tracking workflows
- Integrate with calendar and task management
- Build custom note templates
- Explore Obsidian plugins (git, kanban, calendar, etc.)

Happy note-taking!
