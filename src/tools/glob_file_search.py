"""
Glob file search tool implementation for MCP server.

Provides fast file discovery using Linux find command with comprehensive filtering and sorting.
"""

import asyncio
import fnmatch
import os
import subprocess
from pathlib import Path
from typing import Any

from ..state.validators import ValidationError


class GlobSearchResult:
    """Result of a glob file search operation."""
    
    def __init__(
        self,
        success: bool,
        files: list[str],
        pattern: str,
        total_found: int,
        search_directory: str = "",
        error_code: str = "",
        error_details: str = ""
    ):
        self.success = success
        self.files = files
        self.pattern = pattern
        self.total_found = total_found
        self.search_directory = search_directory
        self.error_code = error_code
        self.error_details = error_details
    
    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format."""
        result = {
            "success": self.success,
            "files": self.files,
            "pattern": self.pattern,
            "total_found": self.total_found,
            "search_directory": self.search_directory
        }
        
        if not self.success:
            result["error"] = {
                "code": self.error_code,
                "message": self.error_details
            }
        
        return result


def validate_glob_parameters(params: dict[str, Any]) -> None:
    """Validate glob file search parameters."""
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    if "glob_pattern" not in params:
        raise ValidationError("Missing required field: glob_pattern")
    
    if not isinstance(params["glob_pattern"], str):
        raise ValidationError("glob_pattern must be a string")
    
    if not params["glob_pattern"].strip():
        raise ValidationError("glob_pattern cannot be empty")
    
    # Validate optional parameters
    if "target_directory" in params:
        if not isinstance(params["target_directory"], str):
            raise ValidationError("target_directory must be a string")
    
    if "ignore_globs" in params:
        if not isinstance(params["ignore_globs"], list):
            raise ValidationError("ignore_globs must be a list")
        for ignore_glob in params["ignore_globs"]:
            if not isinstance(ignore_glob, str):
                raise ValidationError("All ignore_globs must be strings")


def resolve_search_directory(target_directory: str | None) -> Path:
    """Resolve the search directory path."""
    if target_directory is None:
        return Path.cwd()
    
    path = Path(target_directory)
    
    # If it's already absolute, use it as-is
    if path.is_absolute():
        return path
    
    # Otherwise, resolve relative to current working directory
    return path.resolve()


def should_ignore_path(path: Path, ignore_globs: list[str]) -> bool:
    """Check if a path should be ignored based on ignore patterns."""
    if not ignore_globs:
        return False
    
    # Convert path to string for pattern matching
    path_str = str(path)
    
    for ignore_pattern in ignore_globs:
        # Handle patterns that don't start with **/
        if not ignore_pattern.startswith("**/"):
            ignore_pattern = "**/" + ignore_pattern
        
        # Use fnmatch for pattern matching
        if fnmatch.fnmatch(path_str, ignore_pattern):
            return True
        
        # Also check if any parent directory matches
        for parent in path.parents:
            if fnmatch.fnmatch(str(parent), ignore_pattern):
                return True
    
    return False


def expand_glob_pattern(pattern: str) -> str:
    """Expand glob pattern to ensure proper recursive behavior."""
    # If pattern doesn't start with **/, prepend it for recursive search
    if not pattern.startswith("**/"):
        return "**/" + pattern
    
    return pattern


def get_file_modification_time(file_path: Path) -> float:
    """Get file modification time for sorting."""
    try:
        return file_path.stat().st_mtime
    except (OSError, FileNotFoundError):
        return 0.0


def convert_glob_to_find_pattern(pattern: str) -> str:
    """Convert glob pattern to find command pattern."""
    # Handle ** pattern (recursive) - for find, we don't need special handling
    # since find is recursive by default
    if pattern.startswith("**/"):
        pattern = pattern[3:]  # Remove **/ prefix
    
    # Handle simple patterns
    if "*" in pattern or "?" in pattern or "[" in pattern:
        return pattern
    
    # For exact matches, quote the pattern
    return f'"{pattern}"'


def build_find_command(
    pattern: str,
    search_dir: Path,
    ignore_globs: list[str] | None = None
) -> list[str]:
    """Build find command with pattern and ignore options."""
    if ignore_globs is None:
        ignore_globs = []
    
    # Start with basic find command
    cmd = ["find", str(search_dir), "-type", "f"]
    
    # Handle different pattern types
    if pattern.startswith("**/"):
        # Recursive pattern - find will search all subdirectories
        find_pattern = convert_glob_to_find_pattern(pattern)
        cmd.extend(["-name", find_pattern])
    elif "/" in pattern:
        # Pattern with directory - use -path instead of -name
        cmd.extend(["-path", f"*/{pattern}"])
    else:
        # Simple pattern - use -name
        cmd.extend(["-name", pattern])
    
    # Add ignore patterns using -not -path
    for ignore_pattern in ignore_globs:
        # Convert ignore pattern to find format
        if ignore_pattern.startswith("**/"):
            ignore_pattern = ignore_pattern[3:]
        
        # Handle directory patterns
        if ignore_pattern.endswith("/**"):
            ignore_pattern = ignore_pattern[:-3] + "/*"
        
        cmd.extend(["-not", "-path", f"*/{ignore_pattern}"])
        cmd.extend(["-not", "-path", f"*/{ignore_pattern}/*"])
    
    # Don't use -printf as it's not available on macOS
    # We'll sort by modification time in Python instead
    return cmd


async def find_files_with_find(
    pattern: str,
    search_dir: Path,
    ignore_globs: list[str] | None = None
) -> list[Path]:
    """Find files using Linux find command with ignore support."""
    try:
        # Build find command
        cmd = build_find_command(pattern, search_dir, ignore_globs)
        
        # Execute find command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(search_dir)
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            # If find command fails, fall back to Python implementation
            return find_files_with_glob_fallback(pattern, search_dir, ignore_globs)
        
        # Parse output - just file paths, no timestamps
        found_files = []
        output_lines = stdout.decode('utf-8', errors='replace').strip().split('\n')
        
        for line in output_lines:
            if not line.strip():
                continue
            
            # Each line is just a file path
            file_path = Path(line.strip())
            found_files.append(file_path)
        
        # Sort by modification time (newest first) using Python
        found_files.sort(key=get_file_modification_time, reverse=True)
        return found_files
        
    except Exception:
        # If find command fails for any reason, fall back to Python implementation
        return find_files_with_glob_fallback(pattern, search_dir, ignore_globs)


def find_files_with_glob_fallback(
    pattern: str,
    search_dir: Path,
    ignore_globs: list[str] | None = None
) -> list[Path]:
    """Fallback Python implementation for file finding."""
    if ignore_globs is None:
        ignore_globs = []
    
    # Expand pattern for recursive search
    expanded_pattern = expand_glob_pattern(pattern)
    
    found_files = []
    
    # Walk through directory tree
    for root, dirs, files in os.walk(search_dir):
        root_path = Path(root)
        
        # Check if current directory should be ignored
        if should_ignore_path(root_path, ignore_globs):
            # Skip this directory and its subdirectories
            dirs.clear()
            continue
        
        # Filter out ignored directories from dirs list
        dirs[:] = [d for d in dirs if not should_ignore_path(root_path / d, ignore_globs)]
        
        # Check files in current directory
        for file in files:
            file_path = root_path / file
            
            # Check if file should be ignored
            if should_ignore_path(file_path, ignore_globs):
                continue
            
            # Check if file matches the pattern
            if fnmatch.fnmatch(str(file_path.relative_to(search_dir)), expanded_pattern):
                found_files.append(file_path)
    
    return found_files


async def glob_file_search(params: dict[str, Any]) -> dict[str, Any]:
    """
    Search for files using Linux find command with comprehensive filtering.
    
    Args:
        params: Dictionary containing:
            - glob_pattern (str): Glob pattern to match files (e.g., "*.py", "**/test_*.py")
            - target_directory (str, optional): Directory to search in (defaults to current directory)
            - ignore_globs (list[str], optional): Patterns to ignore (e.g., ["**/node_modules/**", "*.pyc"])
    
    Returns:
        Dictionary with search results including file paths and metadata
    
    Features:
    - Ultra-fast file discovery using Linux find command
    - Recursive search with ** pattern support
    - Ignore pattern support for common exclusions
    - Results sorted by modification time (newest first)
    - Automatic fallback to Python implementation if find command fails
    - Comprehensive error handling
    - Cross-platform path handling
    """
    try:
        # Validate input parameters
        validate_glob_parameters(params)
        
        glob_pattern = params["glob_pattern"].strip()
        target_directory = params.get("target_directory")
        ignore_globs = params.get("ignore_globs", [])
        
        # Resolve search directory
        search_dir = resolve_search_directory(target_directory)
        
        # Validate search directory exists
        if not search_dir.exists():
            return GlobSearchResult(
                success=False,
                files=[],
                pattern=glob_pattern,
                total_found=0,
                search_directory=str(search_dir),
                error_code="DIRECTORY_NOT_FOUND",
                error_details=f"Search directory does not exist: {search_dir}"
            ).to_dict()
        
        if not search_dir.is_dir():
            return GlobSearchResult(
                success=False,
                files=[],
                pattern=glob_pattern,
                total_found=0,
                search_directory=str(search_dir),
                error_code="NOT_A_DIRECTORY",
                error_details=f"Path is not a directory: {search_dir}"
            ).to_dict()
        
        # Find matching files using Linux find command
        found_files = await find_files_with_find(glob_pattern, search_dir, ignore_globs)
        
        # Convert to relative paths from search directory
        relative_files = []
        for file_path in found_files:
            try:
                relative_path = file_path.relative_to(search_dir)
                relative_files.append(str(relative_path))
            except ValueError:
                # If relative_to fails, use absolute path
                relative_files.append(str(file_path))
        
        # Return success result
        return GlobSearchResult(
            success=True,
            files=relative_files,
            pattern=glob_pattern,
            total_found=len(relative_files),
            search_directory=str(search_dir)
        ).to_dict()
        
    except ValidationError as e:
        return GlobSearchResult(
            success=False,
            files=[],
            pattern=params.get("glob_pattern", "unknown"),
            total_found=0,
            error_code="VALIDATION_ERROR",
            error_details=str(e)
        ).to_dict()
        
    except PermissionError as e:
        return GlobSearchResult(
            success=False,
            files=[],
            pattern=params.get("glob_pattern", "unknown"),
            total_found=0,
            search_directory=str(params.get("target_directory", "")),
            error_code="PERMISSION_DENIED",
            error_details=str(e)
        ).to_dict()
        
    except Exception as e:
        return GlobSearchResult(
            success=False,
            files=[],
            pattern=params.get("glob_pattern", "unknown"),
            total_found=0,
            search_directory=str(params.get("target_directory", "")),
            error_code="SEARCH_ERROR",
            error_details=f"Unexpected error during file search: {str(e)}"
        ).to_dict()
