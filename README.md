# Cursor Emulator - Universal AI Code Assistant

**Transform any AI assistant into a powerful code assistant using local MCP server.**

This MCP server replicates all the advanced capabilities of Claude Code, giving any AI assistant the ability to:

- **📋 Advanced Task Management**: Track complex multi-step tasks across sessions
- **💻 Terminal Operations**: Execute shell commands with background process management
- **🔍 Code Analysis**: Multi-language linting, semantic search, and pattern matching
- **📝 File Operations**: Atomic editing, search/replace, and file management
- **🌐 Web & GitHub**: Real-time search, PR fetching, and patch application
- **🧠 Memory Management**: Persistent context and knowledge storage
- **⚡ Performance**: Sub-millisecond operations with parallel execution support

## Why You Want This

Without advanced code assistant capabilities, AI assistants:

- ❌ Can't execute terminal commands or manage background processes
- ❌ Can't perform code analysis, linting, or semantic search
- ❌ Can't edit files atomically or manage complex file operations
- ❌ Can't access web search or GitHub integration
- ❌ Can't maintain persistent memory across sessions
- ❌ Limited to basic text generation without tool integration

With Cursor Emulator:

- ✅ **Complete Tool Parity** - All 19 advanced tools from Claude Code
- ✅ **Universal Compatibility** - Works with any AI assistant via MCP
- ✅ **Local Execution** - No external dependencies or API calls
- ✅ **Persistent Memory** - Context and knowledge survive across sessions
- ✅ **Project-Scoped** - Each workspace gets isolated tool environment
- ✅ **Performance Optimized** - Sub-millisecond operations with parallel execution
- ✅ **Security Sandboxed** - Safe command execution with workspace restrictions

## Quick Start

**No installation required!** Just add this to your MCP configuration:

```json
{
  "mcpServers": {
    "cursor-emulator": {
      "command": "uvx",
      "args": ["cursor-emulator"]
    }
  }
}
```

- **Cursor**: Create `.cursor/mcp.json` in your project root
- **IntelliJ IDEA**: Add to Gemini Code Assist MCP configuration
- **Other IDEs**: Add to your MCP configuration file

**Restart your IDE** and try: _"Analyze this codebase and create a development plan"_

The system automatically downloads the package and sets up everything on first use!

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
