# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- `uv sync` - Install dependencies
- `make setup` - Same as uv sync
- `make lint` - Run ruff linting with auto-fix
- `make format` - Format code with ruff
- `make clean` - Remove cache files and artifacts
- `uv run python -m src.server` - Run the MCP server directly
- `uv run python -m pytest` - Run tests (when added)

## Architecture Overview

This is a FastMCP-based Model Context Protocol server that emulates Claude Code's task management system. The architecture follows a layered approach:

### Core Components

**MCP Server Layer** (`src/server.py`):

- FastMCP server with two tools: `TodoRead()` and `TodoWrite(params)`
- Error handling with structured error responses
- Acts as the public API for the todo system

**Tool Layer** (`src/tools/`):

- `todo_read.py` - Returns current todos (no parameters)
- `todo_write.py` - Replaces entire todo list (validates input)
- Thin wrappers around the state management layer

**State Management** (`src/state/store.py`):

- Singleton store pattern with auto-initialization
- Preserves `created_at` timestamps when updating existing todos
- Manages complete todo lifecycle (read/write/clear)

**Persistence Layer** (`src/state/persistence.py`):

- File-based storage to `~/.mcp-tasks/state.json`
- Atomic writes using temporary files
- Automatic backup creation on corruption
- User-only file permissions (600)

**Validation Layer** (`src/state/validators.py`):

- Enforces business rules: unique IDs, single in-progress task
- Type validation for status/priority enums
- Required field checking

### Data Flow

1. MCP client calls `TodoRead()` or `TodoWrite(params)`
2. Server delegates to appropriate tool function
3. Tool function interacts with the singleton store
4. Store manages validation and persistence
5. Persistence layer handles atomic file operations

### Key Constraints

- **Single in-progress rule**: Only one todo can have status "in_progress"
- **Complete replacement**: TodoWrite replaces the entire list, no partial updates
- **Timestamp management**: `created_at` preserved, `updated_at` always refreshed
- **ID uniqueness**: All todo IDs must be unique within the list

### Configuration Integration

The `.cursor/rules/task-management.mdc` file contains comprehensive rules for when and how AI assistants should use this todo system. Copy this file to projects where you want consistent task management behavior.

### Running as MCP Server

Configure in IDE MCP settings with:

```json
{
  "command": "/path/to/uv",
  "args": [
    "--directory",
    "/absolute/path/to/repo",
    "run",
    "python",
    "-m",
    "src.server"
  ]
}
```

The server runs indefinitely, handling TodoRead/TodoWrite requests from MCP clients.
