# Claude Todo MCP Server

A Model Context Protocol (MCP) server that emulates Claude Code's task management system, providing persistent todo functionality for AI coding assistants in IDEs like Cursor, Windsurf, and others.

## Features

- **TodoRead**: Retrieve current task list
- **TodoWrite**: Replace entire task list with validation
- **Persistent Storage**: Tasks saved to `~/.mcp-tasks/state.json`
- **Validation**: Enforces business rules (unique IDs, single in-progress task)
- **Timestamps**: Automatic created_at/updated_at management
- **Atomic Writes**: Safe file operations with backup on corruption

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
git clone https://github.com/yourusername/claude-todo-emulator
cd claude-todo-emulator
uv sync
```

## Configuration

### For Cursor

Create `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "/path/to/uv",
      "args": [
        "--directory",
        "/absolute/path/to/claude-todo-emulator",
        "run",
        "python",
        "-m",
        "src.server"
      ]
    }
  }
}
```

### For Other IDEs

Most MCP-compatible IDEs use similar configuration. Replace `/path/to/uv` with your actual uv path (find it with `which uv`) and update the directory path to your clone location.

### Cursor Rules Integration

This repository includes `.cursor/rules/task-management.mdc` - a comprehensive rule file that teaches AI coding assistants how and when to use the todo system effectively. **Copy this file to your projects** to ensure the agent understands:

- When to create todo lists (complex multi-step tasks)
- When NOT to create todos (simple single tasks)
- How to manage task status and priorities
- Business rules and constraints

The rule file ensures consistent, effective task management across all your AI interactions.

## Usage

Once configured, you can use the todo system in your AI conversations:

```
"Create a todo list for implementing user authentication"
"Show me my current tasks"
"Mark the first task as completed"
```

## API Reference

### TodoRead

- **Parameters**: None
- **Returns**: `{todos: Todo[]}`

### TodoWrite

- **Parameters**: `{todos: Todo[]}`
- **Returns**: `{success: boolean, count: number}`

### Todo Schema

```typescript
{
  id: string;                    // Unique identifier
  content: string;               // Task description
  status: "pending" | "in_progress" | "completed";
  priority: "high" | "medium" | "low";
  created_at: string;            // ISO timestamp (auto-managed)
  updated_at: string;            // ISO timestamp (auto-managed)
  metadata?: object;             // Optional additional data
}
```

## Validation Rules

1. **Required Fields**: `id`, `content`, `status`, `priority`
2. **Unique IDs**: All todo IDs must be unique
3. **Single In-Progress**: Only one task can be "in_progress" at a time
4. **Valid Enums**: Status and priority must use valid values

## Storage

- **Location**: `~/.mcp-tasks/state.json`
- **Format**: JSON with `lastModified` timestamp and `todos` array
- **Backup**: Corrupted files are backed up to `.json.backup`
- **Permissions**: File is created with user-only read/write (600)

## Why This Exists

This server replicates the task management system used by Claude Code, allowing other AI assistants to have similar todo functionality. It provides:

- Structured task tracking for complex, multi-step operations
- Persistent state across sessions
- Validation to maintain data integrity
- A familiar interface for users coming from Claude Code

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Related

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://gofastmcp.com/)
- [Claude Code](https://www.anthropic.com/claude-code)
