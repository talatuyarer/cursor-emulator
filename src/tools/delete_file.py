"""
Delete file tool implementation for MCP server.

Provides safe file deletion with comprehensive validation and error handling.
"""

import os
from pathlib import Path
from typing import Any

from ..state.validators import ValidationError


class DeleteFileResult:
    """Result of a delete file operation."""
    
    def __init__(
        self,
        success: bool,
        file_path: str,
        message: str = "",
        error_code: str = "",
        error_details: str = ""
    ):
        self.success = success
        self.file_path = file_path
        self.message = message
        self.error_code = error_code
        self.error_details = error_details
    
    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format."""
        result = {
            "success": self.success,
            "file_path": self.file_path,
            "message": self.message
        }
        
        if not self.success:
            result["error"] = {
                "code": self.error_code,
                "message": self.error_details
            }
        
        return result


def validate_delete_parameters(params: dict[str, Any]) -> None:
    """Validate delete file parameters."""
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    if "target_file" not in params:
        raise ValidationError("Missing required field: target_file")
    
    if not isinstance(params["target_file"], str):
        raise ValidationError("target_file must be a string")
    
    if not params["target_file"].strip():
        raise ValidationError("target_file cannot be empty")
    
    if "explanation" not in params:
        raise ValidationError("Missing required field: explanation")
    
    if not isinstance(params["explanation"], str):
        raise ValidationError("explanation must be a string")
    
    if not params["explanation"].strip():
        raise ValidationError("explanation cannot be empty")


def resolve_file_path(target_file: str) -> Path:
    """Resolve file path to absolute path."""
    path = Path(target_file)
    
    # If it's already absolute, use it as-is
    if path.is_absolute():
        return path
    
    # Otherwise, resolve relative to current working directory
    return path.resolve()


def validate_file_for_deletion(file_path: Path) -> None:
    """Validate that a file can be safely deleted."""
    # Check if path exists
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    # Check if it's a file (not a directory)
    if not file_path.is_file():
        if file_path.is_dir():
            raise IsADirectoryError(f"Cannot delete directory: {file_path}")
        else:
            raise ValueError(f"Path is not a file: {file_path}")
    
    # Check read permissions (to verify we can access it)
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"No read permission for file: {file_path}")
    
    # Check write permissions (needed for deletion)
    if not os.access(file_path, os.W_OK):
        raise PermissionError(f"No write permission for file: {file_path}")


def safe_delete_file(file_path: Path) -> None:
    """Safely delete a file with error handling."""
    try:
        file_path.unlink()
    except OSError as e:
        if e.errno == 2:  # No such file or directory
            raise FileNotFoundError(f"File does not exist: {file_path}") from e
        elif e.errno == 13:  # Permission denied
            raise PermissionError(f"Permission denied deleting file: {file_path}") from e
        elif e.errno == 21:  # Is a directory
            raise IsADirectoryError(f"Cannot delete directory: {file_path}") from e
        else:
            raise OSError(f"Failed to delete file {file_path}: {e}") from e


async def delete_file(params: dict[str, Any]) -> dict[str, Any]:
    """
    Delete a file safely with comprehensive validation.
    
    Args:
        params: Dictionary containing:
            - target_file (str): Path to file to delete (relative or absolute)
            - explanation (str): Explanation for why file is being deleted
    
    Returns:
        Dictionary with operation result including success status and details
    """
    try:
        # Validate input parameters
        validate_delete_parameters(params)
        
        target_file = params["target_file"].strip()
        explanation = params["explanation"].strip()
        
        # Resolve file path
        file_path = resolve_file_path(target_file)
        
        # Validate file can be deleted
        validate_file_for_deletion(file_path)
        
        # Perform the deletion
        safe_delete_file(file_path)
        
        # Return success result
        return DeleteFileResult(
            success=True,
            file_path=str(file_path),
            message=f"Successfully deleted file: {file_path} (Reason: {explanation})"
        ).to_dict()
        
    except ValidationError as e:
        return DeleteFileResult(
            success=False,
            file_path=params.get("target_file", "unknown"),
            error_code="VALIDATION_ERROR",
            error_details=str(e)
        ).to_dict()
        
    except FileNotFoundError as e:
        return DeleteFileResult(
            success=False,
            file_path=params.get("target_file", "unknown"),
            error_code="FILE_NOT_FOUND",
            error_details=str(e)
        ).to_dict()
        
    except IsADirectoryError as e:
        return DeleteFileResult(
            success=False,
            file_path=params.get("target_file", "unknown"),
            error_code="IS_DIRECTORY",
            error_details=str(e)
        ).to_dict()
        
    except PermissionError as e:
        return DeleteFileResult(
            success=False,
            file_path=params.get("target_file", "unknown"),
            error_code="PERMISSION_DENIED",
            error_details=str(e)
        ).to_dict()
        
    except OSError as e:
        return DeleteFileResult(
            success=False,
            file_path=params.get("target_file", "unknown"),
            error_code="SYSTEM_ERROR",
            error_details=str(e)
        ).to_dict()
        
    except Exception as e:
        return DeleteFileResult(
            success=False,
            file_path=params.get("target_file", "unknown"),
            error_code="UNKNOWN_ERROR",
            error_details=f"Unexpected error: {str(e)}"
        ).to_dict()
