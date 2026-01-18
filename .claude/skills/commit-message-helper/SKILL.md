---
name: commit-message-helper
description: Generates clear, conventional commit messages from git diffs. Use when the user asks to commit changes, write a commit message, or needs help with commits.
allowed-tools: Bash(git:*), Read, Grep
---

# Commit Message Helper

## Overview

This skill helps write clear, professional commit messages that follow conventional commit format and include the Claude Code footer. It examines staged changes and suggests well-structured messages.

## Instructions

When helping with commit messages, follow these steps:

1. **Analyze staged changes**:
   - Run `git diff --staged` to see what changes are staged
   - Run `git status` to understand the overall scope
   - Run `git log --oneline -5` to see recent commit style

2. **Determine commit type**:
   - Analyze the nature of changes (feature, fix, docs, refactor, etc.)
   - Identify the scope/area affected
   - Note if there are breaking changes

3. **Draft the commit message** with this structure:

```
<type>(<scope>): <subject>

<body>

<footer with Claude Code attribution>
```

4. **Execute the commit**:
   - Stage files if needed: `git add <files>`
   - Create commit using heredoc format for proper formatting
   - Verify with `git status`

## Commit Message Format

### Type (required)
- **feat**: New feature or capability
- **fix**: Bug fix
- **docs**: Documentation changes only
- **style**: Code style/formatting (no logic changes)
- **refactor**: Code restructuring without feature/fix
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Build, dependencies, tooling
- **ci**: CI/CD pipeline changes

### Scope (optional)
Examples for this project:
- `auth` - Authentication related
- `mcp` - MCP server/protocol
- `tools` - MCP tools implementation
- `docs` - Documentation
- `oauth` - OAuth flow
- `api` - API endpoints

### Subject (required)
- Use imperative mood: "add" not "adds" or "added"
- Don't capitalize first letter
- No period at the end
- Maximum 50 characters
- Be specific and clear

### Body (optional but recommended)
- Explain **what** and **why**, not how
- Use bullet points for multiple changes
- Wrap at 72 characters
- Leave blank line after subject
- Include implementation details if complex

### Footer (required)
ALWAYS include the Claude Code attribution:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

Optionally add before the attribution:
- Issue references: `Fixes #123` or `Relates to #456`
- Breaking changes: `BREAKING CHANGE: description`

## Examples

### Feature with scope
```
feat(tools): add calendar integration tool

Implement Google Calendar integration allowing users to:
- List upcoming events
- Create new calendar events
- Update existing events
- Delete events

Uses OAuth 2.0 for authentication and caches credentials.

Relates to #15

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Bug fix
```
fix(oauth): resolve token refresh race condition

Token refresh now uses mutex lock to prevent multiple concurrent
refresh requests. This resolves intermittent 401 errors when
multiple tools execute simultaneously.

Fixes #23

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Documentation
```
docs: add deployment guide for Railway

Add comprehensive Railway deployment documentation including:
- Environment variable configuration
- Docker setup
- Domain configuration
- Auth0 integration steps

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Refactoring
```
refactor(server): simplify endpoint registration

Replace manual route registration with decorator-based approach.
Reduces boilerplate and improves code readability.

No functional changes.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Commit Command Format

ALWAYS use heredoc format for proper multi-line handling:

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <subject>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

## Best Practices

1. **Subject Line**:
   - Keep under 50 characters
   - Be specific: "add user authentication" > "add feature"
   - Use imperative mood consistently

2. **Body**:
   - Explain the reasoning and context
   - Use bullet points for clarity
   - Focus on what and why, not how

3. **Scope**:
   - Use consistent scopes across the project
   - Keep scopes short (1-2 words)
   - Omit if change affects entire project

4. **Atomic Commits**:
   - One logical change per commit
   - Group related files together
   - Don't mix features with fixes

5. **Footer**:
   - Always include Claude Code attribution
   - Reference issues when applicable
   - Note breaking changes clearly

## Special Cases

### Multiple File Types
If changes span multiple areas, either:
- Use broader scope: `feat(server): add multiple improvements`
- Or split into multiple commits (preferred)

### Breaking Changes
Add to footer before Claude Code attribution:
```
BREAKING CHANGE: /health endpoint now requires authentication

All endpoints except /info now require valid OAuth tokens.
Update client configurations accordingly.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Initial Commit
```
chore: initial project setup

Initialize Sherpa MCP Server with:
- Basic project structure
- Python virtual environment
- Git repository configuration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Quick Checklist

Before committing, verify:
- [ ] Changes are staged (`git status`)
- [ ] Commit type is accurate
- [ ] Subject is imperative and < 50 chars
- [ ] Body explains why (if not obvious)
- [ ] Claude Code footer is included
- [ ] No sensitive data in commit message
- [ ] Heredoc format is used for multi-line messages
