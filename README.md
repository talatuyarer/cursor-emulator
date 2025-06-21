# Claude Todo MCP Server

**Add persistent task management to any AI coding assistant in Cursor, Windsurf, and other IDEs.**

This MCP server replicates Claude Code's todo system, giving your AI assistant the ability to:

- Track complex multi-step tasks across sessions
- Break down large features into manageable pieces
- Remember progress when you switch between projects
- Enforce single in-progress task focus

## Why You Want This

Without task management, AI assistants:

- ❌ Forget what they were working on between conversations
- ❌ Lose track of multi-step implementations
- ❌ Can't prioritize or organize complex work
- ❌ Leave tasks half-finished when you switch contexts

With this MCP server:

- ✅ **Persistent memory** - Tasks survive across sessions
- ✅ **Project-scoped** - Each workspace gets its own todo list
- ✅ **Automatic tracking** - AI knows when to create/update tasks
- ✅ **Progress visibility** - See exactly what's completed/pending
- ✅ **Focus enforcement** - Only one task in-progress at a time

## Quick Start

1. **Clone and install:**

   ```bash
   git clone https://github.com/joehaddad2000/claude-todo-emulator
   cd claude-todo-emulator
   uv sync
   ```

2. **Add to Cursor:** Create `.cursor/mcp.json` in your project:

   ```json
   {
     "mcpServers": {
       "task-manager": {
         "command": "/Users/yourusername/.local/bin/uv",
         "args": [
           "--directory",
           "/path/to/claude-todo-emulator",
           "run",
           "python",
           "-m",
           "src.server"
         ]
       }
     }
   }
   ```

3. **Restart Cursor** and try: _"Create a todo list for adding user authentication"_

   The rules file will be automatically copied to `.cursor/rules/` on first use.

## What You Get

Once configured, your AI assistant will automatically:

**Create todos for complex tasks:**

```
You: "Add dark mode support with user preferences"
AI: "I'll create a todo list for this multi-step feature:
- ✅ Add theme context and state management
- 🔄 Create dark mode CSS variables and styles
- ⏳ Build settings UI for theme switching
- ⏳ Add persistence to localStorage
- ⏳ Update existing components for theme support"
```

**Track progress visually:**

```
You: "What's the status on the authentication system?"
AI: "Current authentication tasks:
- ✅ Set up JWT middleware
- ✅ Create login/signup endpoints
- 🔄 Building user profile management (in progress)
- ⏳ Add password reset flow
- ⏳ Implement role-based permissions"
```

**Maintain focus:**

```
You: "Let's also add email notifications"
AI: "I'll add that to the todo list, but let me finish the current user profile task first to maintain focus."
```

## Detailed Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Cursor, Windsurf, or MCP-compatible IDE

### Step 1: Configure Your IDE

#### Option A: Direct from PyPI (Recommended)

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "uvx",
      "args": ["claude-todo-emulator"]
    }
  }
}
```

#### Option B: Local Development

```bash
git clone https://github.com/joehaddad2000/claude-todo-emulator
cd claude-todo-emulator
```

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "uvx",
      "args": [
        "--from",
        "/absolute/path/to/claude-todo-emulator",
        "claude-todo-emulator"
      ]
    }
  }
}
```

#### For Other IDEs

Most MCP-compatible IDEs use similar JSON configuration. Adjust the format as needed for your specific IDE.

### Step 2: Test the Setup (Auto-Setup Included!)

1. Restart your IDE completely
2. Start a new conversation
3. Try: _"Create a todo list for implementing user authentication"_
4. The system will automatically copy the rules file on first use

**No manual setup needed** - just install and use.

## Troubleshooting

### "spawn uv ENOENT" Error

- **Problem**: System can't find uv command
- **Solution**: Use full path like `/Users/yourusername/.local/bin/uv`
- **Find path**: Run `which uv` in terminal

### "No module named 'src'" Error

- **Problem**: Incorrect module execution
- **Solution**: Make sure you're using `python -m src.server` not `python main.py`

### AI Doesn't Create Todos

- **Problem**: Missing or incorrect rules file
- **Solution**: Verify `task-management.mdc` is in `.cursor/rules/` directory
- **Check**: Rules file should be ~200 lines with detailed instructions

### Todos Appear in Wrong Directory

- **Problem**: Workspace detection not working
- **Solution**: Verify `WORKSPACE_FOLDER_PATHS` environment variable is set by IDE
- **Check**: Look for `.mcp-todos.json` in your project root, not the MCP server directory

### Permission Errors

- **Problem**: Can't write to project directory
- **Solution**: Ensure your IDE has write permissions to the project folder

## How It Works

### Storage

- **Location**: `.mcp-todos.json` in each project directory
- **Format**: JSON with timestamps and todo arrays
- **Permissions**: User-only read/write (600)
- **Auto-Setup**: Rules file automatically copied on first use

### Workspace Detection

- Uses `WORKSPACE_FOLDER_PATHS` environment variable from IDE
- Falls back to current working directory if not found
- Automatically adds `.mcp-todos.json` to `.gitignore`

### API Reference

**TodoRead**

- Parameters: None
- Returns: `{todos: Todo[]}`

**TodoWrite**

- Parameters: `{todos: Todo[]}`
- Returns: `{success: boolean, count: number}`

**Todo Schema**

```typescript
{
  id: string;
  content: string;
  status: "pending" | "in_progress" | "completed";
  priority: "high" | "medium" | "low";
  created_at: string;
  updated_at: string;
  metadata?: object;
}
```

### Validation Rules

1. All todo IDs must be unique
2. Only one task can be "in_progress" at a time
3. Required fields: id, content, status, priority
4. Status and priority must use valid enum values

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://gofastmcp.com/)
- [Claude Code](https://www.anthropic.com/claude-code)
