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

- File-based storage to `.mcp-todos.json` in current working directory
- Project-scoped todos (each directory gets its own todo list)
- Atomic writes using temporary files
- User-only file permissions (600)
- Automatic recovery from corrupted files

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

The server automatically copies two rules files to your `.cursor/rules/` directory:

- `00-system-instructions.mdc` - Core behavioral enforcement (always check todos)
- `01-task-management.mdc` - Detailed guidance (examples, anti-patterns, tool reference)

These files ensure consistent task management behavior across all AI interactions in your project.

### Running as MCP Server

The package includes a console script for easy execution. Configure in IDE MCP settings:

**From PyPI (after publishing):**

```json
{
  "mcpServers": {
    "todo": {
      "command": "uvx",
      "args": ["claude-todo-emulator"]
    }
  }
}
```

**From local directory (for development):**

```json
{
  "mcpServers": {
    "todo": {
      "command": "uvx",
      "args": [
        "--from",
        "/path/to/claude-todo-emulator",
        "claude-todo-emulator"
      ]
    }
  }
}
```

**Automatic Workspace Detection**:

- The server automatically detects your workspace directory using the `WORKSPACE_FOLDER_PATHS` environment variable set by Cursor/VSCode
- Creates `.mcp-todos.json` in your current project directory
- Each project gets its own isolated todo list
- No manual configuration required!

**How it works**:

1. Cursor sets `WORKSPACE_FOLDER_PATHS=/path/to/your/project`
2. Server detects this and stores todos in `/path/to/your/project/.mcp-todos.json`
3. Switch projects → switch todo lists automatically

The server runs indefinitely, handling TodoRead/TodoWrite requests from MCP clients.

## Typing Guidelines (Python 3.11)

**Full type annotations required for all functions and class attributes**

**✅ Use Modern Built-in Types:**

- `list[T]` instead of `List[T]`
- `dict[K, V]` instead of `Dict[K, V]`
- `tuple[T, ...]` instead of `Tuple[T, ...]`
- `set[T]` instead of `Set[T]`

**✅ Use Union Operator:**

- `str | int` instead of `Union[str, int]`
- `str | None` instead of `Optional[str]`

**✅ Function Parameters (accept any sequence/mapping-like):**

- `Sequence[T]` for any sequence-like objects
- `Mapping[K, V]` for any mapping-like objects
- `Iterable[T]` for iteration-only parameters
- `MutableMapping[K, V]` for mutable mappings

**✅ Return Types (be specific):**

- `list[T]`, `dict[K, V]` for concrete return types

**✅ Security & Advanced:**

- `LiteralString` for SQL/injection-sensitive string parameters
- `Protocol` for duck typing without inheritance
- `TypedDict` for structured dictionaries
- `Self` for method chaining return types
