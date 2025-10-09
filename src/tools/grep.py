"""
Grep tool implementation for MCP server.

Provides fast pattern searching using Linux grep command with comprehensive filtering and output formatting.
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..state.validators import ValidationError


class GrepResult:
    """Result of a grep search operation."""
    
    def __init__(
        self,
        success: bool,
        matches: List[Dict[str, Any]],
        pattern: str,
        total_matches: int,
        files_searched: int,
        files_matched: int,
        search_paths: List[str],
        error_code: str = "",
        error_details: str = ""
    ):
        self.success = success
        self.matches = matches
        self.pattern = pattern
        self.total_matches = total_matches
        self.files_searched = files_searched
        self.files_matched = files_matched
        self.search_paths = search_paths
        self.error_code = error_code
        self.error_details = error_details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        result = {
            "success": self.success,
            "matches": self.matches,
            "pattern": self.pattern,
            "total_matches": self.total_matches,
            "files_searched": self.files_searched,
            "files_matched": self.files_matched,
            "search_paths": self.search_paths
        }
        
        if not self.success:
            result["error"] = {
                "code": self.error_code,
                "message": self.error_details
            }
        
        return result


class GrepSearcher:
    """Grep search implementation using Linux grep command."""
    
    def __init__(self):
        self.grep_command = "grep"
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit per file
    
    def validate_grep_parameters(self, params: Dict[str, Any]) -> None:
        """Validate grep search parameters."""
        if not isinstance(params, dict):
            raise ValidationError("Parameters must be a dictionary")
        
        if "pattern" not in params:
            raise ValidationError("Missing required field: pattern")
        
        if not isinstance(params["pattern"], str):
            raise ValidationError("pattern must be a string")
        
        if not params["pattern"].strip():
            raise ValidationError("pattern cannot be empty")
        
        # Validate optional parameters
        if "paths" in params:
            if not isinstance(params["paths"], list):
                raise ValidationError("paths must be a list")
            for path in params["paths"]:
                if not isinstance(path, str):
                    raise ValidationError("All paths must be strings")
        
        if "case_sensitive" in params:
            if not isinstance(params["case_sensitive"], bool):
                raise ValidationError("case_sensitive must be a boolean")
        
        if "whole_word" in params:
            if not isinstance(params["whole_word"], bool):
                raise ValidationError("whole_word must be a boolean")
        
        if "regex" in params:
            if not isinstance(params["regex"], bool):
                raise ValidationError("regex must be a boolean")
        
        if "max_results" in params:
            if not isinstance(params["max_results"], int) or params["max_results"] < 1:
                raise ValidationError("max_results must be a positive integer")
        
        if "include_patterns" in params:
            if not isinstance(params["include_patterns"], list):
                raise ValidationError("include_patterns must be a list")
            for pattern in params["include_patterns"]:
                if not isinstance(pattern, str):
                    raise ValidationError("All include_patterns must be strings")
        
        if "exclude_patterns" in params:
            if not isinstance(params["exclude_patterns"], list):
                raise ValidationError("exclude_patterns must be a list")
            for pattern in params["exclude_patterns"]:
                if not isinstance(pattern, str):
                    raise ValidationError("All exclude_patterns must be strings")
    
    def resolve_search_paths(self, paths: Optional[List[str]]) -> List[Path]:
        """Resolve and validate search paths."""
        if not paths:
            return [Path.cwd()]
        
        resolved_paths = []
        for path_str in paths:
            path = Path(path_str)
            
            # If it's already absolute, use it as-is
            if path.is_absolute():
                resolved_paths.append(path)
            else:
                # Otherwise, resolve relative to current working directory
                resolved_paths.append(path.resolve())
        
        return resolved_paths
    
    def build_grep_command(
        self,
        pattern: str,
        search_paths: List[Path],
        case_sensitive: bool = True,
        whole_word: bool = False,
        regex: bool = True,
        max_results: int = 1000,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """Build grep command with all options."""
        if include_patterns is None:
            include_patterns = []
        if exclude_patterns is None:
            exclude_patterns = []
        
        # Start with basic grep command
        cmd = [self.grep_command]
        
        # Add basic options
        if not case_sensitive:
            cmd.append("-i")
        
        if whole_word:
            cmd.append("-w")
        
        if regex:
            cmd.append("-E")  # Extended regex
        else:
            cmd.append("-F")  # Fixed string
        
        # Add line numbers
        cmd.append("-n")
        
        # Add file names
        cmd.append("-H")
        
        # Add color (will be stripped later)
        cmd.append("--color=always")
        
        # Add include patterns
        for include_pattern in include_patterns:
            cmd.extend(["--include", include_pattern])
        
        # Add exclude patterns
        for exclude_pattern in exclude_patterns:
            cmd.extend(["--exclude", exclude_pattern])
        
        # Add max count per file
        cmd.extend(["-m", str(max_results)])
        
        # Add recursive flag
        cmd.append("-r")
        
        # Add the pattern
        cmd.append(pattern)
        
        # Add search paths
        for path in search_paths:
            cmd.append(str(path))
        
        return cmd
    
    def parse_grep_output(self, output: str, search_paths: List[Path]) -> List[Dict[str, Any]]:
        """Parse grep output into structured results."""
        matches = []
        files_searched = set()
        files_matched = set()
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            # Remove ANSI color codes
            import re
            clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
            
            # Parse grep output format: file:line:content
            # Handle cases where file paths contain colons
            parts = clean_line.split(':', 2)
            if len(parts) >= 3:
                file_path = parts[0]
                line_number = parts[1]
                content = parts[2]
                
                try:
                    line_num = int(line_number)
                    
                    # Convert to relative path if possible
                    file_path_obj = Path(file_path)
                    relative_path = None
                    
                    for search_path in search_paths:
                        try:
                            relative_path = file_path_obj.relative_to(search_path)
                            break
                        except ValueError:
                            continue
                    
                    if relative_path is None:
                        relative_path = file_path_obj
                    
                    match = {
                        "file": str(relative_path),
                        "line_number": line_num,
                        "content": content.strip(),
                        "absolute_path": str(file_path_obj)
                    }
                    
                    matches.append(match)
                    files_searched.add(str(file_path_obj))
                    files_matched.add(str(file_path_obj))
                    
                except ValueError:
                    # Skip lines that don't match expected format
                    continue
        
        return matches, list(files_searched), list(files_matched)
    
    async def search_with_grep(
        self,
        pattern: str,
        search_paths: List[Path],
        case_sensitive: bool = True,
        whole_word: bool = False,
        regex: bool = True,
        max_results: int = 1000,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> GrepResult:
        """Perform grep search using Linux grep command."""
        try:
            # Build grep command
            cmd = self.build_grep_command(
                pattern, search_paths, case_sensitive, whole_word, regex,
                max_results, include_patterns, exclude_patterns
            )
            
            # Execute grep command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd()
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse output
            output = stdout.decode('utf-8', errors='replace')
            error_output = stderr.decode('utf-8', errors='replace')
            
            if process.returncode == 0:
                # Success - parse results
                matches, files_searched, files_matched = self.parse_grep_output(output, search_paths)
                
                return GrepResult(
                    success=True,
                    matches=matches,
                    pattern=pattern,
                    total_matches=len(matches),
                    files_searched=len(files_searched),
                    files_matched=len(files_matched),
                    search_paths=[str(p) for p in search_paths]
                )
            
            elif process.returncode == 1:
                # No matches found - this is not an error
                return GrepResult(
                    success=True,
                    matches=[],
                    pattern=pattern,
                    total_matches=0,
                    files_searched=0,
                    files_matched=0,
                    search_paths=[str(p) for p in search_paths]
                )
            
            else:
                # Actual error
                return GrepResult(
                    success=False,
                    matches=[],
                    pattern=pattern,
                    total_matches=0,
                    files_searched=0,
                    files_matched=0,
                    search_paths=[str(p) for p in search_paths],
                    error_code="GREP_ERROR",
                    error_details=f"Grep command failed: {error_output}"
                )
                
        except Exception as e:
            return GrepResult(
                success=False,
                matches=[],
                pattern=pattern,
                total_matches=0,
                files_searched=0,
                files_matched=0,
                search_paths=[str(p) for p in search_paths],
                error_code="SEARCH_ERROR",
                error_details=f"Failed to execute grep search: {str(e)}"
            )


async def grep(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for patterns in files using Linux grep command.
    
    Parameters:
        params: Dictionary containing:
            - pattern: Pattern to search for (required)
            - paths: List of paths to search in (optional, defaults to current directory)
            - case_sensitive: Whether search is case sensitive (optional, defaults to True)
            - whole_word: Whether to match whole words only (optional, defaults to False)
            - regex: Whether pattern is a regex (optional, defaults to True)
            - max_results: Maximum results per file (optional, defaults to 1000)
            - include_patterns: File patterns to include (optional, e.g., ["*.py", "*.js"])
            - exclude_patterns: File patterns to exclude (optional, e.g., ["*.pyc", "node_modules"])
    
    Returns:
        Dictionary with search results including matches, file counts, and metadata
    """
    # Validate parameters
    searcher = GrepSearcher()
    searcher.validate_grep_parameters(params)
    
    try:
        # Extract parameters
        pattern = params["pattern"].strip()
        paths = params.get("paths")
        case_sensitive = params.get("case_sensitive", True)
        whole_word = params.get("whole_word", False)
        regex = params.get("regex", True)
        max_results = params.get("max_results", 1000)
        include_patterns = params.get("include_patterns")
        exclude_patterns = params.get("exclude_patterns")
        
        # Resolve search paths
        search_paths = searcher.resolve_search_paths(paths)
        
        # Validate search paths exist
        valid_paths = []
        for path in search_paths:
            if path.exists():
                valid_paths.append(path)
            else:
                # Log warning but continue with other paths
                pass
        
        if not valid_paths:
            return GrepResult(
                success=False,
                matches=[],
                pattern=pattern,
                total_matches=0,
                files_searched=0,
                files_matched=0,
                search_paths=[str(p) for p in search_paths],
                error_code="NO_VALID_PATHS",
                error_details="No valid search paths found"
            ).to_dict()
        
        # Perform search
        result = await searcher.search_with_grep(
            pattern, valid_paths, case_sensitive, whole_word, regex,
            max_results, include_patterns, exclude_patterns
        )
        
        return result.to_dict()
        
    except Exception as e:
        return GrepResult(
            success=False,
            matches=[],
            pattern=params.get("pattern", "unknown"),
            total_matches=0,
            files_searched=0,
            files_matched=0,
            search_paths=[],
            error_code="UNEXPECTED_ERROR",
            error_details=f"Unexpected error during grep search: {str(e)}"
        ).to_dict()
