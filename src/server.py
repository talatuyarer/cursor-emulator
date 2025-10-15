from contextlib import asynccontextmanager
from typing import Any
import json

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


# TodoWrite removed - use TodoWriteCompat instead for Gemini Code Assist compatibility


@mcp.tool
async def TodoWriteCompat(todos_json: str, merge: bool = False, clear: bool = False) -> dict[str, Any]:
    """
    Write advanced todos with merge/update capabilities (Gemini Code Assist compatible version).
    
    Parameters:
        todos_json: JSON string containing list of todo items
        merge: Whether to merge with existing todos (defaults to False)
        clear: Whether to clear existing todos first (defaults to False)
    
    Returns success status, todo count, summary, and formatted display.
    """
    try:
        todos = json.loads(todos_json)
        params = {
            "todos": todos,
            "merge": merge,
            "clear": clear
        }
        return await todo_write(params)
    except json.JSONDecodeError as e:
        return {"error": {"code": "JSON_ERROR", "message": f"Invalid JSON: {str(e)}"}}
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
async def RunTerminalCmd(command: str, cwd: str = "", timeout: int = 30, 
                        sandbox: bool = True, is_background: bool = False, 
                        process_id: str = "") -> dict[str, Any]:
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
        if cwd:  # If not empty string
            params["cwd"] = cwd
        if timeout != 30:
            params["timeout"] = timeout
        if process_id:  # If not empty string
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
async def RunTerminalCmdCompat(command: str, cwd: str = "", timeout: int = 30, 
                              sandbox: bool = True, is_background: bool = False, 
                              process_id: str = "", env_vars_json: str = "") -> dict[str, Any]:
    """
    Execute a terminal command (Gemini Code Assist compatible version).
    
    Parameters:
        command: The command to execute
        cwd: Working directory (optional, defaults to workspace root)
        timeout: Command timeout in seconds (optional, defaults to 30, 0 = no timeout)
        sandbox: Enable security sandbox (optional, defaults to True)
        is_background: Run command in background (optional, defaults to False)
        process_id: Process ID for background commands (optional)
        env_vars_json: Environment variables as JSON string (optional)
    
    Returns command results including stdout, stderr, return_code, execution_time,
    streaming output, and process management information.
    """
    try:
        params = {
            "command": command,
            "sandbox": sandbox,
            "is_background": is_background
        }
        if cwd:  # If not empty string
            params["cwd"] = cwd
        if timeout != 30:
            params["timeout"] = timeout
        if process_id:  # If not empty string
            params["process_id"] = process_id
        if env_vars_json:  # If not empty string
            try:
                env_vars = json.loads(env_vars_json)
                params["env_vars"] = env_vars
            except json.JSONDecodeError as e:
                return {"error": {"code": "JSON_ERROR", "message": f"Invalid env_vars JSON: {str(e)}"}}
        
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


# ReadLints removed - use ReadLintsCompat instead for Gemini Code Assist compatibility


@mcp.tool
async def WebSearch(query: str, engine: str = "", max_results: int = 10, 
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
            "max_results": max_results,
            "timeout": timeout,
            "use_cache": use_cache
        }
        if engine:  # If not empty string
            params["engine"] = engine
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


# CodebaseSearch removed - use CodebaseSearchCompat instead for Gemini Code Assist compatibility


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


# SearchReplaceMultiple removed - use SearchReplaceMultipleCompat instead for Gemini Code Assist compatibility


@mcp.tool
async def SearchReplaceMultipleCompat(file_path: str, replacements_json: str) -> dict[str, Any]:
    """
    Perform multiple string replacements in a file (Gemini Code Assist compatible version).
    
    Parameters:
        file_path: Path to the file to modify
        replacements_json: JSON string containing list of replacement objects
    
    Returns operation result with total replacements made and details.
    """
    try:
        replacements = json.loads(replacements_json)
        params = {
            "file_path": file_path,
            "replacements": replacements
        }
        return await search_replace_multiple(params)
    except json.JSONDecodeError as e:
        return {"error": {"code": "JSON_ERROR", "message": f"Invalid JSON: {str(e)}"}}
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "REPLACE_ERROR",
                "message": f"Failed to perform multiple search and replace: {str(e)}",
            }
        }


# MultiEdit and MultiEditValidate removed - use MultiEditCompat and MultiEditValidateCompat instead for Gemini Code Assist compatibility


@mcp.tool
async def MultiEditCompat(file_path: str, edits_json: str) -> dict[str, Any]:
    """
    Make multiple edits to a single file in one atomic operation (Gemini Code Assist compatible version).
    
    Parameters:
        file_path: Path to the file to edit
        edits_json: JSON string containing list of edit operations
    
    Returns operation result with details of all edits applied.
    """
    try:
        edits = json.loads(edits_json)
        params = {
            "file_path": file_path,
            "edits": edits
        }
        return await multi_edit(params)
    except json.JSONDecodeError as e:
        return {"error": {"code": "JSON_ERROR", "message": f"Invalid JSON: {str(e)}"}}
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
async def MultiEditValidateCompat(file_path: str, edits_json: str) -> dict[str, Any]:
    """
    Validate multi-edit operations without applying them (Gemini Code Assist compatible version).
    
    Parameters:
        file_path: Path to the file to validate against
        edits_json: JSON string containing list of edit operations to validate
    
    Returns validation results showing which edits would succeed or fail.
    """
    try:
        edits = json.loads(edits_json)
        params = {
            "file_path": file_path,
            "edits": edits
        }
        return await multi_edit_validate_only(params)
    except json.JSONDecodeError as e:
        return {"error": {"code": "JSON_ERROR", "message": f"Invalid JSON: {str(e)}"}}
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


# GlobFileSearch removed - use GlobFileSearchCompat instead for Gemini Code Assist compatibility




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


# Grep removed - use GrepCompat instead for Gemini Code Assist compatibility


# UpdateMemory removed - use UpdateMemoryCompat instead for Gemini Code Assist compatibility


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
async def ReadLintsCompat(paths_json: str = "[]", languages_json: str = "[]", 
                         timeout: int = 30, recursive: bool = True) -> dict[str, Any]:
    """
    Read linter errors from the workspace (Gemini Code Assist compatible version).
    
    Parameters:
        paths_json: JSON string containing list of file/directory paths to check
        languages_json: JSON string containing list of languages to check
        timeout: Linter timeout in seconds (optional, defaults to 30, max 300)
        recursive: Whether to search recursively in directories (optional, defaults to True)
    
    Returns linting results with errors, warnings, and info grouped by severity.
    """
    try:
        params = {
            "timeout": timeout,
            "recursive": recursive
        }
        
        if paths_json != "[]":
            try:
                paths = json.loads(paths_json)
                params["paths"] = paths
            except json.JSONDecodeError as e:
                return {"error": {"code": "JSON_ERROR", "message": f"Invalid paths JSON: {str(e)}"}}
        
        if languages_json != "[]":
            try:
                languages = json.loads(languages_json)
                params["languages"] = languages
            except json.JSONDecodeError as e:
                return {"error": {"code": "JSON_ERROR", "message": f"Invalid languages JSON: {str(e)}"}}
        
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
async def CodebaseSearchCompat(query: str, target_directories_json: str = "[]", 
                              max_results: int = 20) -> dict[str, Any]:
    """
    Perform semantic codebase search (Gemini Code Assist compatible version).
    
    Parameters:
        query: Natural language search query
        target_directories_json: JSON string containing list of directories to search
        max_results: Maximum number of results (optional, defaults to 20, max 100)
    
    Returns search results with context and relevance scoring.
    """
    try:
        params = {
            "query": query,
            "max_results": max_results
        }
        
        if target_directories_json != "[]":
            try:
                target_directories = json.loads(target_directories_json)
                params["target_directories"] = target_directories
            except json.JSONDecodeError as e:
                return {"error": {"code": "JSON_ERROR", "message": f"Invalid target_directories JSON: {str(e)}"}}
        
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
async def GlobFileSearchCompat(glob_pattern: str, target_directory: str = "", 
                              ignore_globs_json: str = "[]") -> dict[str, Any]:
    """
    Search for files using glob patterns (Gemini Code Assist compatible version).
    
    Parameters:
        glob_pattern: Glob pattern to match files
        target_directory: Directory to search in (defaults to current directory)
        ignore_globs_json: JSON string containing list of patterns to ignore
    
    Returns search results including file paths and metadata.
    """
    try:
        params = {
            "glob_pattern": glob_pattern
        }
        
        if target_directory:  # If not empty string
            params["target_directory"] = target_directory
        
        if ignore_globs_json != "[]":
            try:
                ignore_globs = json.loads(ignore_globs_json)
                params["ignore_globs"] = ignore_globs
            except json.JSONDecodeError as e:
                return {"error": {"code": "JSON_ERROR", "message": f"Invalid ignore_globs JSON: {str(e)}"}}
        
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
async def GrepCompat(pattern: str, paths_json: str = "[]", case_sensitive: bool = True, 
                    whole_word: bool = False, regex: bool = True, max_results: int = 1000,
                    include_patterns_json: str = "[]", exclude_patterns_json: str = "[]") -> dict[str, Any]:
    """
    Search for patterns in files using Linux grep command (Gemini Code Assist compatible version).
    
    Parameters:
        pattern: Pattern to search for
        paths_json: JSON string containing list of paths to search in
        case_sensitive: Whether search is case sensitive (optional, defaults to True)
        whole_word: Whether to match whole words only (optional, defaults to False)
        regex: Whether pattern is a regex (optional, defaults to True)
        max_results: Maximum results per file (optional, defaults to 1000)
        include_patterns_json: JSON string containing file patterns to include
        exclude_patterns_json: JSON string containing file patterns to exclude
    
    Returns search results including matches and metadata.
    """
    try:
        params = {
            "pattern": pattern,
            "case_sensitive": case_sensitive,
            "whole_word": whole_word,
            "regex": regex,
            "max_results": max_results
        }
        
        if paths_json != "[]":
            try:
                paths = json.loads(paths_json)
                params["paths"] = paths
            except json.JSONDecodeError as e:
                return {"error": {"code": "JSON_ERROR", "message": f"Invalid paths JSON: {str(e)}"}}
        
        if include_patterns_json != "[]":
            try:
                include_patterns = json.loads(include_patterns_json)
                params["include_patterns"] = include_patterns
            except json.JSONDecodeError as e:
                return {"error": {"code": "JSON_ERROR", "message": f"Invalid include_patterns JSON: {str(e)}"}}
        
        if exclude_patterns_json != "[]":
            try:
                exclude_patterns = json.loads(exclude_patterns_json)
                params["exclude_patterns"] = exclude_patterns
            except json.JSONDecodeError as e:
                return {"error": {"code": "JSON_ERROR", "message": f"Invalid exclude_patterns JSON: {str(e)}"}}
        
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
async def UpdateMemoryCompat(action: str, key: str = "", content: str = "", 
                            tags_json: str = "[]", expires_at: str = "",
                            metadata_json: str = "{}", query: str = "",
                            limit: int = 0) -> dict[str, Any]:
    """
    Manage persistent memories (Gemini Code Assist compatible version).
    
    Parameters:
        action: Action to perform (required: create, update, delete, get, list, search)
        key: Memory key (required for update, delete, get; optional for create)
        content: Memory content (required for create, optional for update)
        tags_json: JSON string containing list of tags for categorization
        expires_at: Expiration date in ISO format
        metadata_json: JSON string containing additional metadata dictionary
        query: Search query (required for search action)
        limit: Maximum number of results (optional, defaults to 100 for list, 20 for search)
    
    Returns operation result including success status and memory data.
    """
    try:
        params = {
            "action": action
        }
        
        if key:  # If not empty string
            params["key"] = key
        if content:  # If not empty string
            params["content"] = content
        if expires_at:  # If not empty string
            params["expires_at"] = expires_at
        if query:  # If not empty string
            params["query"] = query
        if limit > 0:
            params["limit"] = limit
        
        if tags_json != "[]":
            try:
                tags = json.loads(tags_json)
                params["tags"] = tags
            except json.JSONDecodeError as e:
                return {"error": {"code": "JSON_ERROR", "message": f"Invalid tags JSON: {str(e)}"}}
        
        if metadata_json != "{}":
            try:
                metadata = json.loads(metadata_json)
                params["metadata"] = metadata
            except json.JSONDecodeError as e:
                return {"error": {"code": "JSON_ERROR", "message": f"Invalid metadata JSON: {str(e)}"}}
        
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
