<general_rules>
- **Tool Development**: When creating new MCP tools, always first check the `/src/tools/` directory to see if a similar tool exists. If creating a new tool, place it in `/src/tools/` and follow the existing pattern of thin wrappers around state management functions.
- **State Management**: When adding state management functions, use the `/src/state/` directory. Follow the singleton pattern established by the `store` instance in `/src/state/store.py`. All state operations should go through the centralized store.
- **Type Annotations**: Use Python 3.11+ modern type hints consistently:
  - `list[T]` instead of `List[T]`
  - `dict[K, V]` instead of `Dict[K, V]`
  - `str | None` instead of `Optional[str]`
  - Full type annotations required for all functions and class attributes
- **Business Rules Enforcement**: Always enforce these critical business rules in validation:
  - Only one todo can have status "in_progress" at a time
  - All todo IDs must be unique within the list
  - Required fields: id, content, status, priority
- **Code Quality**: Always run `make lint` and `make format` before committing changes. The project uses ruff for both linting and formatting.
- **Development Commands**: Use `make setup` or `uv sync` to install dependencies, `make clean` to remove cache files, and `uv run python -m src.server` to run the MCP server directly.
- **Tool Integration**: When adding new tools, ensure they support parallel execution and follow the async/await pattern for optimal performance.
- **Error Handling**: All tools must include comprehensive error handling with ValidationError for parameter validation and detailed error messages.
- **Performance**: Tools should be optimized for parallel execution and handle large datasets efficiently.
</general_rules>

<repository_structure>
This is a FastMCP-based Model Context Protocol server with a comprehensive development toolkit:

**MCP Server Layer** (`/src/server.py`):
- FastMCP entry point with 19 advanced tools
- Handles error responses and acts as the public API
- Manages server lifecycle and initialization
- Supports parallel tool execution for optimal performance

**Tool Layer** (`/src/tools/`):
- **Task Management**: `todo_read.py`, `todo_write.py` - Advanced task management with visual indicators
- **Terminal Operations**: `run_terminal_cmd.py` - Shell execution with background processes
- **Code Analysis**: `read_lints.py` - Multi-language linting, `codebase_search.py` - Semantic search
- **File Operations**: `search_replace.py`, `multi_edit.py`, `delete_file.py`, `glob_file_search.py`
- **Web & GitHub**: `web_search.py`, `fetch_pull_request.py`, `apply_patch.py`
- **Search & Memory**: `grep.py`, `update_memory.py`
- Thin wrappers that delegate to the state management layer

**State Management Layer** (`/src/state/`):
- `store.py` - Singleton store pattern with auto-initialization
- `validators.py` - Enforces business rules and type validation
- `persistence.py` - File-based storage with atomic writes
- `utils.py` - Workspace detection and Cursor rules integration

**Type Definitions** (`/src/types.py`):
- TypedDict definitions for Todo, TaskStore, and API responses
- Enums for TodoStatus and TodoPriority

**Data Flow**: MCP Client → Server Tools → State Store → Validation → Persistence Layer

**Key Features**:
- **19 comprehensive tools** for development workflows
- **Parallel tool execution** support for 3-5x performance improvement
- **Persistent memory management** across sessions (`.mcp-memories.json`)
- **Multi-language code analysis** (Python, Java, JavaScript, TypeScript, Go, Rust, C++)
- **Advanced terminal operations** with background process management
- **GitHub integration** with PR fetching and patch application
- **Real-time web search** with multiple engines and caching
- **Semantic code understanding** and exploration
- **Atomic file operations** with rollback capabilities
- **Project-scoped storage** (each workspace gets its own `.mcp-todos.json`)
- **Automatic workspace detection** via environment variables
- **Auto-copying of Cursor rules** to `.cursor/rules/` directory
</repository_structure>

<dependencies_and_installation>
- **Package Manager**: This project uses `uv` as the modern Python package manager
- **Python Version**: Requires Python 3.11 or higher
- **Installation**: Run `uv sync` or `make setup` to install all dependencies
- **Main Dependencies**: 
  - FastMCP framework (`fastmcp>=2.8.1`) for MCP server functionality
  - `aiohttp>=3.8.0` for web search capabilities
  - `beautifulsoup4>=4.11.0` for HTML parsing
  - `lxml>=4.9.0` for XML processing
- **Lock File**: Dependencies are locked in `uv.lock` for reproducible builds
- **Virtual Environment**: `uv` automatically manages the virtual environment
</dependencies_and_installation>

<tool_categories>
**Task Management Tools:**
- `TodoRead` / `TodoWrite` - Advanced task management with visual indicators, merge capabilities, and business rules

**Terminal & Process Management:**
- `RunTerminalCmd` - Shell command execution with background processes, environment variables, and streaming
- `GetBackgroundProcessStatus` / `KillBackgroundProcess` / `ListBackgroundProcesses` - Process management

**Code Analysis & Quality:**
- `ReadLints` - Multi-language linting (Python, Java, JavaScript, TypeScript, Go, Rust, C++)
- `CodebaseSearch` - Semantic code understanding and exploration
- `Grep` - Pattern search using Linux grep command

**File Operations:**
- `SearchReplace` / `SearchReplaceMultiple` - Exact string replacements
- `MultiEdit` / `MultiEditValidate` - Atomic multi-edit operations
- `DeleteFile` - Safe file deletion with validation
- `GlobFileSearch` - File discovery using glob patterns

**Web & GitHub Integration:**
- `WebSearch` - Real-time web search with multiple engines
- `FetchPullRequest` - GitHub pull request data retrieval
- `ApplyPatch` - Unified diff patch application

**Memory & Context Management:**
- `UpdateMemory` - Persistent memory management for context and preferences
</tool_categories>

<performance_characteristics>
**Tool Performance:**
- **File Operations**: Sub-millisecond for most operations
- **Search Operations**: 0.002-0.01s for typical codebases
- **Web Search**: 1-3s depending on network and engine
- **Terminal Commands**: Varies by command complexity
- **Memory Operations**: < 0.001s for typical operations

**Parallel Execution:**
- Supports concurrent tool execution
- 3-5x performance improvement for multiple operations
- Optimized for development workflows

**Scalability:**
- Handles large codebases efficiently
- Memory usage scales with workspace size
- Persistent storage for cross-session context
</performance_characteristics>

<testing_instructions>
**Current State**: Comprehensive testing has been implemented and validated for all tools.

**Testing Framework**:
- **Framework**: pytest with pytest-asyncio for async testing
- **Test Execution**: Run tests via `uv run python -m pytest`
- **Test Coverage**: All 19 tools have been tested with comprehensive test suites

**Test Coverage Areas**:
- **Validation logic** in `/src/state/validators.py`
- **State management operations** in `/src/state/store.py`
- **Persistence mechanisms** and atomic writes
- **Tool functionality** and error handling
- **Business rule enforcement** (single in-progress task, unique IDs)
- **Performance testing** for all tools
- **Parallel execution** validation
- **Memory management** operations
- **File operations** with atomic writes
- **Terminal command execution** with background processes
- **Web search** functionality
- **GitHub integration** features

**Testing Guidelines**:
- Test files mirror the source structure
- Focus on testing business logic and validation rules
- Mock file system operations for persistence tests
- Ensure error handling paths are covered
- Test both success and failure scenarios
- Validate performance characteristics
- Test parallel execution capabilities
</testing_instructions>

<usage_examples>
**Common Development Workflows:**

**New Project Setup:**
1. Use `CodebaseSearch` to understand project structure
2. Use `ReadLints` to check code quality
3. Use `UpdateMemory` to store project context
4. Use `TodoWrite` to create initial task list

**Feature Development:**
1. Use `CodebaseSearch` to find related code
2. Use `Grep` to locate specific functions/classes
3. Use `SearchReplace`/`MultiEdit` for code changes
4. Use `ReadLints` to validate changes
5. Use `TodoWrite` to track progress

**Bug Investigation:**
1. Use `CodebaseSearch` to understand error context
2. Use `Grep` to find error patterns
3. Use `ReadLints` to identify code issues
4. Use `SearchReplace` to fix problems
5. Use `UpdateMemory` to store bug patterns

**Code Review:**
1. Use `FetchPullRequest` to get PR details
2. Use `CodebaseSearch` to understand changes
3. Use `ReadLints` to check code quality
4. Use `ApplyPatch` to test changes locally
5. Use `UpdateMemory` to store review notes

**Performance Optimization:**
- Use parallel tool calls for multiple operations
- Batch related operations together
- Use appropriate limits for large result sets
- Monitor execution times and optimize tool selection
</usage_examples>

<pull_request_formatting>
**Pull Request Guidelines:**

**Title Format**: `feat: Add new tool name` or `fix: Fix issue description`

**Description Template**:
```markdown
## Description
Brief description of changes

## Changes Made
- [ ] Added new tool: `ToolName`
- [ ] Updated existing functionality
- [ ] Fixed bugs/issues
- [ ] Updated documentation

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Performance tests completed
- [ ] Manual testing performed

## Performance Impact
- Tool execution time: Xms
- Memory usage: XMB
- Parallel execution: Supported/Not supported

## Breaking Changes
- None / List any breaking changes

## Dependencies
- Added: `package>=version`
- Updated: `package>=version`
- Removed: `package`
```

**Review Checklist**:
- [ ] Code follows project style guidelines
- [ ] All tools support parallel execution
- [ ] Comprehensive error handling implemented
- [ ] Performance characteristics documented
- [ ] Tests cover success and failure scenarios
- [ ] Documentation updated
</pull_request_formatting>
