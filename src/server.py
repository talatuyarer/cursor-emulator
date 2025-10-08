from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from .state.store import store
from .state.utils import copy_cursor_rules
from .state.validators import ValidationError
from .tools.todo_read import todo_read
from .tools.todo_write import todo_write
from .tools.run_terminal_cmd import run_terminal_cmd
from .tools.read_lints import read_lints
from .tools.task_write import task_write, task_read
from .tools.web_search import web_search
from .tools.codebase_search import codebase_search


@asynccontextmanager
async def lifespan(app: FastMCP):
    """Initialize store on startup to ensure .mcp-todos.json exists"""
    # Startup
    await store.initialize()

    # Force creation of the file and all associated setup if it doesn't exist
    if not store.persistence.file_path.exists():
        # Writing an empty todo list will trigger:
        # 1. Creation of .mcp-todos.json
        # 2. Adding to .gitignore
        # 3. Copying Cursor rules
        await store.write_todos([])

    # Always ensure rules file is up to date
    copy_cursor_rules(store.persistence.workspace_path)

    yield

    # Shutdown (nothing to do)


# Create the MCP server
mcp = FastMCP(
    "Task Manager",
    instructions="Manages persistent todo lists with TodoRead and TodoWrite tools, executes terminal commands, reads linter errors, provides advanced task management, performs web searches, and provides semantic codebase search. TodoRead returns current todos, TodoWrite replaces entire list, RunTerminalCmd executes shell commands, ReadLints analyzes code quality, TaskWrite manages tasks with merge/update capabilities, TaskRead returns current tasks, WebSearch performs real-time web searches, CodebaseSearch provides semantic code understanding.",
    lifespan=lifespan,
)


@mcp.tool
async def TodoRead() -> dict[str, Any]:
    """
    Read the current task list.

    Returns a list of todos with their current state.
    """
    try:
        return await todo_read()
    except Exception as e:
        return {
            "error": {
                "code": "READ_ERROR",
                "message": f"Failed to read todos: {str(e)}",
            }
        }


@mcp.tool
async def TodoWrite(todos: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Update the entire task list (complete replacement).

    Parameters:
        todos: List of todo items, each containing:
            - id: Unique identifier for the task
            - content: Task description
            - status: Current status (pending, in_progress, completed)
            - priority: Task priority (high, medium, low)
            - metadata: Optional additional data

    Returns success status and count of todos written.
    """
    try:
        return await todo_write({"todos": todos})
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "WRITE_ERROR",
                "message": f"Failed to write todos: {str(e)}",
            }
        }


@mcp.tool
async def RunTerminalCmd(command: str, cwd: str | None = None, timeout: int = 30, sandbox: bool = True) -> dict[str, Any]:
    """
    Execute a terminal command in the workspace directory with sandbox security.

    Parameters:
        command: The command to execute
        cwd: Working directory (optional, defaults to workspace root)
        timeout: Command timeout in seconds (optional, defaults to 30, max 300)
        sandbox: Enable security sandbox (optional, defaults to True)

    Returns command results including stdout, stderr, return_code, execution_time, and security info.
    
    Security Features:
    - Blocks dangerous commands (rm, sudo, systemctl, etc.)
    - Restricts working directory to workspace
    - Validates command patterns against known threats
    - Limits command length and execution time
    """
    try:
        params = {"command": command, "sandbox": sandbox}
        if cwd is not None:
            params["cwd"] = cwd
        if timeout != 30:
            params["timeout"] = timeout
        
        return await run_terminal_cmd(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "COMMAND_ERROR",
                "message": f"Failed to execute command: {str(e)}",
            }
        }


@mcp.tool
async def ReadLints(paths: list[str] | None = None, languages: list[str] | None = None, 
                   timeout: int = 30, recursive: bool = True) -> dict[str, Any]:
    """
    Read linter errors from the workspace with multi-language support.

    Parameters:
        paths: List of file/directory paths to check (optional, defaults to current directory)
        languages: List of languages to check (optional, auto-detect if not provided)
        timeout: Linter timeout in seconds (optional, defaults to 30, max 300)
        recursive: Whether to search recursively in directories (optional, defaults to True)

    Returns linting results with errors, warnings, and info grouped by severity.
    
    Supported Languages:
    - Python: ruff, flake8, pylint
    - Java: checkstyle, spotbugs, pmd
    - JavaScript: eslint, jshint
    - TypeScript: eslint, tsc
    - Go: golangci-lint, gofmt
    - Rust: clippy, rustfmt
    - C++: clang-tidy, cppcheck
    """
    try:
        params = {}
        if paths is not None:
            params["paths"] = paths
        if languages is not None:
            params["languages"] = languages
        if timeout != 30:
            params["timeout"] = timeout
        if not recursive:
            params["recursive"] = recursive
        
        return await read_lints(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "LINT_ERROR",
                "message": f"Failed to read lints: {str(e)}",
            }
        }


@mcp.tool
async def TaskWrite(tasks: list[dict[str, Any]], merge: bool = False, clear: bool = False) -> dict[str, Any]:
    """
    Write tasks to the task manager with merge/update capabilities.

    Parameters:
        tasks: List of task dictionaries, each containing:
            - id: Unique identifier for the task (required)
            - content: Task description (required)
            - status: Task status (optional: pending, in_progress, completed, cancelled)
            - priority: Task priority (optional: high, medium, low)
            - metadata: Optional additional data
        merge: Whether to merge with existing tasks (optional, defaults to False)
        clear: Whether to clear existing tasks first (optional, defaults to False)

    Returns success status, task count, summary, and formatted display.
    
    Features:
    - Visual status indicators (⏳🔄✅❌)
    - Priority indicators (🔴🟡🟢)
    - Business rule enforcement (only one in_progress task)
    - Merge/update capabilities
    - Real-time progress tracking
    """
    try:
        params = {"tasks": tasks, "merge": merge, "clear": clear}
        return await task_write(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "TASK_ERROR",
                "message": f"Failed to write tasks: {str(e)}",
            }
        }


@mcp.tool
async def TaskRead() -> dict[str, Any]:
    """
    Read all tasks from the task manager.

    Returns current tasks with summary statistics and formatted display.
    
    Features:
    - Complete task list with status and priority
    - Summary statistics (total, by status, by priority)
    - Formatted display with emoji indicators
    - Real-time task state
    """
    try:
        return await task_read()
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "TASK_ERROR",
                "message": f"Failed to read tasks: {str(e)}",
            }
        }


@mcp.tool
async def WebSearch(query: str, engine: str | None = None, max_results: int = 10, 
                   timeout: int = 30, use_cache: bool = True) -> dict[str, Any]:
    """
    Perform a web search and return real-time results.

    Parameters:
        query: Search query string
        engine: Search engine to use (optional: duckduckgo, google)
        max_results: Maximum number of results (optional, defaults to 10, max 50)
        timeout: Search timeout in seconds (optional, defaults to 30, max 120)
        use_cache: Whether to use cached results (optional, defaults to True)

    Returns search results with metadata including relevance scores and sources.
    
    Features:
    - Multiple search engines (DuckDuckGo, Google)
    - Result caching for performance
    - Relevance scoring and ranking
    - Source domain extraction
    - Timeout protection
    - Real-time web scraping
    """
    try:
        params = {
            "query": query,
            "engine": engine,
            "max_results": max_results,
            "timeout": timeout,
            "use_cache": use_cache
        }
        return await web_search(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "SEARCH_ERROR",
                "message": f"Failed to perform web search: {str(e)}",
            }
        }


@mcp.tool
async def CodebaseSearch(query: str, target_directories: list[str] | None = None, 
                        max_results: int = 20) -> dict[str, Any]:
    """
    Perform semantic codebase search to understand code by meaning.

    Parameters:
        query: Natural language search query (e.g., "How does authentication work?")
        target_directories: List of directories to search (optional, defaults to current directory)
        max_results: Maximum number of results (optional, defaults to 20, max 100)

    Returns search results with context and relevance scoring.
    
    Features:
    - Natural language query understanding
    - Multi-language code support (Python, JavaScript, TypeScript, Java, Go, Rust, C++)
    - Context extraction with surrounding code
    - Intelligent result ranking
    - Pattern-based semantic matching
    - File structure analysis
    """
    try:
        params = {
            "query": query,
            "target_directories": target_directories,
            "max_results": max_results
        }
        return await codebase_search(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "SEARCH_ERROR",
                "message": f"Failed to perform codebase search: {str(e)}",
            }
        }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
