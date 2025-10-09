from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from .state.store import store
from .state.utils import copy_cursor_rules
from .state.validators import ValidationError
from .tools.todo_read import todo_read
from .tools.todo_write import todo_write
from .tools.run_terminal_cmd import run_terminal_cmd, get_background_process_status, kill_background_process, list_background_processes
from .tools.read_lints import read_lints
from .tools.web_search import web_search
from .tools.codebase_search import codebase_search
from .tools.search_replace import search_replace, search_replace_multiple
from .tools.multi_edit import multi_edit, multi_edit_validate_only
from .tools.delete_file import delete_file
from .tools.glob_file_search import glob_file_search
from .tools.fetch_pull_request import fetch_pull_request
from .tools.apply_patch import apply_patch
from .tools.grep import grep
from .tools.update_memory import update_memory


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
    "Cursor Emulator",
    instructions="Manages persistent todo lists with TodoRead and TodoWrite tools, executes terminal commands with advanced features, reads linter errors, performs web searches, provides semantic codebase search, performs exact file editing, safely deletes files, searches for files using glob patterns, fetches GitHub pull request data, applies unified diff patches, searches for patterns in files using grep, and manages persistent memories. TodoRead/TodoWrite provide advanced task management with visual indicators, merge/update capabilities, and business rules, RunTerminalCmd executes shell commands with background execution, environment variables, streaming output, and process management, ReadLints analyzes code quality, WebSearch performs real-time web searches, CodebaseSearch provides semantic code understanding, SearchReplace performs exact string replacements in files, MultiEdit performs atomic multi-edit operations on files, DeleteFile safely deletes files with validation, GlobFileSearch finds files using glob patterns with filtering and sorting, FetchPullRequest fetches comprehensive GitHub pull request data including metadata, files, and comments, ApplyPatch applies unified diff patches to files with context validation and atomic operations using Linux patch command, Grep searches for patterns in files using Linux grep command with comprehensive filtering and output formatting, UpdateMemory manages persistent memories with create, update, delete, get, list, and search operations, GetBackgroundProcessStatus checks status of background processes, KillBackgroundProcess terminates background processes, ListBackgroundProcesses lists all background processes.",
    lifespan=lifespan,
)


@mcp.tool
async def TodoRead() -> dict[str, Any]:
    """
    Read the current advanced todo list with visual indicators and summaries.

    Returns todos with status indicators, priority levels, and formatted display.
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
async def TodoWrite(todos: list[dict[str, Any]], merge: bool = False, clear: bool = False) -> dict[str, Any]:
    """
    Write advanced todos with merge/update capabilities and visual indicators.

    Parameters:
        todos: List of todo items, each containing:
            - id: Unique identifier for the todo (required)
            - content: Todo description (required)
            - status: Current status (optional: pending, in_progress, completed, cancelled)
            - priority: Todo priority (optional: high, medium, low)
            - metadata: Optional additional data
        merge: Whether to merge with existing todos (optional, defaults to False)
        clear: Whether to clear existing todos first (optional, defaults to False)

    Returns success status, todo count, summary, and formatted display.
    """
    try:
        params = {
            "todos": todos,
            "merge": merge,
            "clear": clear
        }
        return await todo_write(params)
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
async def RunTerminalCmd(command: str, cwd: str | None = None, timeout: int = 30, 
                        sandbox: bool = True, is_background: bool = False, 
                        env_vars: dict[str, str] | None = None, 
                        process_id: str | None = None) -> dict[str, Any]:
    """
    Execute a terminal command with advanced features including background execution, 
    environment variables, streaming output, and process management.

    Parameters:
        command: The command to execute
        cwd: Working directory (optional, defaults to workspace root)
        timeout: Command timeout in seconds (optional, defaults to 30, 0 = no timeout)
        sandbox: Enable security sandbox (optional, defaults to True)
        is_background: Run command in background (optional, defaults to False)
        env_vars: Environment variables (optional, dict of key-value pairs)
        process_id: Process ID for background commands (optional)

    Returns command results including stdout, stderr, return_code, execution_time,
    streaming output, and process management information.
    
    Advanced Features:
    - Background execution with process tracking
    - Environment variable support
    - Real-time output streaming
    - Process management and monitoring
    - Enhanced security validation
    
    Security Features:
    - Blocks dangerous commands (rm, sudo, systemctl, etc.)
    - Restricts working directory to workspace
    - Validates command patterns against known threats
    - Limits command length and execution time
    - Validates environment variables for security
    """
    try:
        params = {
            "command": command,
            "sandbox": sandbox,
            "is_background": is_background
        }
        if cwd is not None:
            params["cwd"] = cwd
        if timeout != 30:
            params["timeout"] = timeout
        if env_vars is not None:
            params["env_vars"] = env_vars
        if process_id is not None:
            params["process_id"] = process_id
        
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


@mcp.tool
async def SearchReplace(file_path: str, old_string: str, new_string: str, 
                       replace_all: bool = False) -> dict[str, Any]:
    """
    Perform exact string replacement in a file.

    Parameters:
        file_path: Path to the file to modify
        old_string: Exact string to find and replace
        new_string: String to replace it with
        replace_all: Whether to replace all occurrences (optional, defaults to False)

    Returns operation result with number of replacements made.
    
    Features:
    - Exact string matching with uniqueness validation
    - Preserves exact formatting and indentation
    - Safety checks for file permissions and encoding
    - Atomic file writes to prevent corruption
    - Detailed error messages for debugging
    """
    try:
        params = {
            "file_path": file_path,
            "old_string": old_string,
            "new_string": new_string,
            "replace_all": replace_all
        }
        return await search_replace(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "REPLACE_ERROR",
                "message": f"Failed to perform search and replace: {str(e)}",
            }
        }


@mcp.tool
async def SearchReplaceMultiple(file_path: str, replacements: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Perform multiple string replacements in a file.

    Parameters:
        file_path: Path to the file to modify
        replacements: List of replacement objects, each containing:
            - old_string: String to find
            - new_string: String to replace with
            - replace_all: Whether to replace all occurrences (optional)

    Returns operation result with total replacements made and details.
    
    Features:
    - Batch multiple replacements in a single operation
    - Atomic file write (all or nothing)
    - Detailed results for each replacement
    - Efficient single file read/write cycle
    """
    try:
        params = {
            "file_path": file_path,
            "replacements": replacements
        }
        return await search_replace_multiple(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "REPLACE_ERROR",
                "message": f"Failed to perform multiple search and replace: {str(e)}",
            }
        }


@mcp.tool
async def MultiEdit(file_path: str, edits: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Make multiple edits to a single file in one atomic operation.

    Parameters:
        file_path: Path to the file to edit
        edits: List of edit operations, each containing:
            - old_string: String to find and replace (required)
            - new_string: String to replace with (required)
            - replace_all: Whether to replace all occurrences (optional, defaults to False)

    Returns operation result with details of all edits applied.
    
    Features:
    - Atomic operation (all edits succeed or none are applied)
    - Sequential processing (edits applied in order)
    - Comprehensive error handling with rollback
    - Detailed results for each edit operation
    - File consistency guaranteed
    """
    try:
        params = {
            "file_path": file_path,
            "edits": edits
        }
        return await multi_edit(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "EDIT_ERROR",
                "message": f"Failed to perform multi-edit operation: {str(e)}",
            }
        }


@mcp.tool
async def MultiEditValidate(file_path: str, edits: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Validate multi-edit operations without applying them.

    Parameters:
        file_path: Path to the file to validate against
        edits: List of edit operations to validate

    Returns validation results showing which edits would succeed or fail.
    
    Features:
    - Pre-validation of all edit operations
    - Check string existence and occurrence counts
    - Identify potential issues before applying edits
    - Safe way to test complex edit sequences
    """
    try:
        params = {
            "file_path": file_path,
            "edits": edits
        }
        return await multi_edit_validate_only(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": f"Failed to validate multi-edit operations: {str(e)}",
            }
        }


@mcp.tool
async def DeleteFile(target_file: str, explanation: str) -> dict[str, Any]:
    """
    Safely delete a file with comprehensive validation and error handling.

    Parameters:
        target_file: Path to the file to delete (relative or absolute)
        explanation: Explanation for why the file is being deleted

    Returns:
        Dictionary with operation result including success status and details
    
    Features:
    - Path resolution (handles both relative and absolute paths)
    - Existence validation (ensures file exists before deletion)
    - Type validation (prevents directory deletion)
    - Permission checks (validates read/write permissions)
    - Comprehensive error handling with specific error codes
    - Audit trail (requires explanation for accountability)
    - Safe deletion with proper error recovery
    """
    try:
        params = {
            "target_file": target_file,
            "explanation": explanation
        }
        return await delete_file(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "DELETE_ERROR",
                "message": f"Failed to delete file: {str(e)}",
            }
        }


@mcp.tool
async def GlobFileSearch(glob_pattern: str, target_directory: str | None = None, 
                        ignore_globs: list[str] | None = None) -> dict[str, Any]:
    """
    Search for files using glob patterns with comprehensive filtering and sorting.

    Parameters:
        glob_pattern: Glob pattern to match files (e.g., "*.py", "**/test_*.py", "src/**/*.js")
        target_directory: Directory to search in (defaults to current directory)
        ignore_globs: List of patterns to ignore (e.g., ["**/node_modules/**", "*.pyc", "**/__pycache__/**"])

    Returns:
        Dictionary with search results including file paths and metadata
    
    Features:
    - Fast file discovery using glob patterns
    - Recursive search with ** pattern support
    - Ignore pattern support for common exclusions (node_modules, __pycache__, etc.)
    - Results sorted by modification time (newest first)
    - Cross-platform path handling
    - Comprehensive error handling with specific error codes
    - Support for complex glob patterns and filtering
    """
    try:
        params = {
            "glob_pattern": glob_pattern,
            "target_directory": target_directory,
            "ignore_globs": ignore_globs or []
        }
        return await glob_file_search(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "SEARCH_ERROR",
                "message": f"Failed to search for files: {str(e)}",
            }
        }




@mcp.tool
async def FetchPullRequest(owner: str, repo: str, pull_number: int, token: str | None = None) -> dict[str, Any]:
    """
    Fetch GitHub pull request data including metadata, files, and comments.

    Parameters:
        owner: GitHub repository owner (required)
        repo: GitHub repository name (required)
        pull_number: Pull request number (required)
        token: GitHub personal access token (optional, for private repos or higher rate limits)

    Returns:
        Dictionary with comprehensive PR data including:
        - Basic metadata (title, description, author, status)
        - Timestamps (created, updated, merged, closed)
        - Statistics (commits, additions, deletions, changed files)
        - Branch information (head and base)
        - Files changed in the PR
        - Comments on the PR
        - Labels, assignees, and reviewers
    """
    try:
        params = {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number
        }
        if token is not None:
            params["token"] = token
        
        return await fetch_pull_request(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "PR_FETCH_ERROR",
                "message": f"Failed to fetch pull request: {str(e)}",
            }
        }


@mcp.tool
async def ApplyPatch(file_path: str, patch_content: str, dry_run: bool = False, create_backup: bool = True) -> dict[str, Any]:
    """
    Apply a unified diff patch to a file using the Linux patch command with context validation.

    Parameters:
        file_path: Path to the target file (required)
        patch_content: Unified diff patch content (required)
        dry_run: If True, only validate the patch without applying it (optional, defaults to False)
        create_backup: If True, create backup before applying (optional, defaults to True)

    Returns:
        Dictionary with patch application results including:
        - success: Whether the patch was applied successfully
        - target_file: Path to the target file
        - attempt: Number of attempts made
        - stdout: Standard output from patch command
        - stderr: Standard error from patch command
        - patch_size: Size of the patch content
        - lines_changed: Number of lines in the patch
        - backup_file: Path to backup file (if created)
    """
    try:
        params = {
            "file_path": file_path,
            "patch_content": patch_content,
            "dry_run": dry_run,
            "create_backup": create_backup
        }
        
        return await apply_patch(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "PATCH_ERROR",
                "message": f"Failed to apply patch: {str(e)}",
            }
        }


@mcp.tool
async def Grep(pattern: str, paths: list[str] | None = None, case_sensitive: bool = True, 
              whole_word: bool = False, regex: bool = True, max_results: int = 1000,
              include_patterns: list[str] | None = None, exclude_patterns: list[str] | None = None) -> dict[str, Any]:
    """
    Search for patterns in files using Linux grep command with comprehensive filtering.

    Parameters:
        pattern: Pattern to search for (required)
        paths: List of paths to search in (optional, defaults to current directory)
        case_sensitive: Whether search is case sensitive (optional, defaults to True)
        whole_word: Whether to match whole words only (optional, defaults to False)
        regex: Whether pattern is a regex (optional, defaults to True)
        max_results: Maximum results per file (optional, defaults to 1000)
        include_patterns: File patterns to include (optional, e.g., ["*.py", "*.js"])
        exclude_patterns: File patterns to exclude (optional, e.g., ["*.pyc", "node_modules"])

    Returns:
        Dictionary with search results including:
        - success: Whether the search was successful
        - matches: List of matches with file, line_number, content, and absolute_path
        - pattern: The search pattern used
        - total_matches: Total number of matches found
        - files_searched: Number of files searched
        - files_matched: Number of files that contained matches
        - search_paths: List of paths that were searched
    """
    try:
        params = {
            "pattern": pattern,
            "paths": paths,
            "case_sensitive": case_sensitive,
            "whole_word": whole_word,
            "regex": regex,
            "max_results": max_results,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns
        }
        
        return await grep(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "GREP_ERROR",
                "message": f"Failed to perform grep search: {str(e)}",
            }
        }


@mcp.tool
async def UpdateMemory(action: str, key: str | None = None, content: str | None = None, 
                      tags: list[str] | None = None, expires_at: str | None = None,
                      metadata: dict[str, Any] | None = None, query: str | None = None,
                      limit: int | None = None) -> dict[str, Any]:
    """
    Manage persistent memories with create, update, delete, get, list, and search operations.

    Parameters:
        action: Action to perform (required: create, update, delete, get, list, search)
        key: Memory key (required for update, delete, get; optional for create)
        content: Memory content (required for create, optional for update)
        tags: List of tags for categorization (optional)
        expires_at: Expiration date in ISO format (optional, e.g., "2024-12-31T23:59:59")
        metadata: Additional metadata dictionary (optional)
        query: Search query (required for search action)
        limit: Maximum number of results (optional, defaults to 100 for list, 20 for search)

    Returns:
        Dictionary with operation result including:
        - success: Whether the operation was successful
        - action: The action performed
        - key: The memory key
        - memory: The memory data (for create, update, get actions)
        - message: Human-readable result message
        - total_memories: Total number of memories in storage
        - error_code: Error code if operation failed
        - error_details: Detailed error information

    Features:
    - Persistent storage across sessions
    - Automatic expiration handling
    - Tag-based organization and filtering
    - Content and metadata search
    - Access count tracking
    - Atomic operations with rollback
    - Comprehensive error handling
    - Memory deduplication
    - Automatic cleanup of expired memories
    """
    try:
        params = {
            "action": action,
            "key": key,
            "content": content,
            "tags": tags,
            "expires_at": expires_at,
            "metadata": metadata,
            "query": query,
            "limit": limit
        }
        
        return await update_memory(params)
    except ValidationError as e:
        return {
            "success": False,
            "action": action,
            "key": key or "unknown",
            "memory": None,
            "message": f"Validation error: {str(e)}",
            "total_memories": 0,
            "error_code": "VALIDATION_ERROR",
            "error_details": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "action": action,
            "key": key or "unknown",
            "memory": None,
            "message": f"Memory operation failed: {str(e)}",
            "total_memories": 0,
            "error_code": "OPERATION_ERROR",
            "error_details": str(e)
        }


@mcp.tool
async def GetBackgroundProcessStatus(process_id: str) -> dict[str, Any]:
    """
    Get status of a background process.

    Parameters:
        process_id: ID of the background process to check

    Returns:
        Dictionary with process status information including runtime, output, and completion status
    """
    try:
        return await get_background_process_status(process_id)
    except Exception as e:
        return {
            "error": {
                "code": "PROCESS_ERROR",
                "message": f"Failed to get process status: {str(e)}",
            }
        }


@mcp.tool
async def KillBackgroundProcess(process_id: str) -> dict[str, Any]:
    """
    Kill a background process.

    Parameters:
        process_id: Process ID to kill

    Returns:
        Dictionary with kill result and process status
    """
    try:
        return await kill_background_process(process_id)
    except Exception as e:
        return {
            "error": {
                "code": "PROCESS_ERROR",
                "message": f"Failed to kill process: {str(e)}",
            }
        }


@mcp.tool
async def ListBackgroundProcesses() -> dict[str, Any]:
    """
    List all background processes.

    Returns:
        Dictionary with list of all background processes and their status
    """
    try:
        return await list_background_processes()
    except Exception as e:
        return {
            "error": {
                "code": "PROCESS_ERROR",
                "message": f"Failed to list processes: {str(e)}",
            }
        }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
