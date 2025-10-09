import os
from pathlib import Path
from typing import Any, Dict

from ..state.validators import ValidationError


class SearchReplaceResult:
    """Represents the result of a search and replace operation"""
    
    def __init__(self, success: bool, replacements_made: int = 0, 
                 error_message: str = "", file_path: str = ""):
        self.success = success
        self.replacements_made = replacements_made
        self.error_message = error_message
        self.file_path = file_path
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "replacements_made": self.replacements_made,
            "error_message": self.error_message,
            "file_path": self.file_path
        }


def validate_file_path(file_path: str) -> Path:
    """Validate and resolve file path"""
    if not isinstance(file_path, str) or not file_path.strip():
        raise ValidationError("File path must be a non-empty string")
    
    path = Path(file_path).resolve()
    
    if not path.exists():
        raise ValidationError(f"File does not exist: {file_path}")
    
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")
    
    # Check if file is readable
    if not os.access(path, os.R_OK):
        raise ValidationError(f"File is not readable: {file_path}")
    
    return path


def validate_strings(old_string: str, new_string: str) -> None:
    """Validate old_string and new_string parameters"""
    if not isinstance(old_string, str):
        raise ValidationError("old_string must be a string")
    
    if not isinstance(new_string, str):
        raise ValidationError("new_string must be a string")
    
    # Note: We allow empty strings for both old_string and new_string
    # Empty old_string would be invalid, but we'll check that in the main function


def count_occurrences(content: str, search_string: str) -> int:
    """Count occurrences of search_string in content"""
    if not search_string:
        return 0
    return content.count(search_string)


def perform_replacement(content: str, old_string: str, new_string: str, 
                       replace_all: bool = False) -> tuple[str, int]:
    """
    Perform the string replacement operation.
    
    Returns:
        tuple: (new_content, number_of_replacements)
    """
    if not old_string:
        raise ValidationError("old_string cannot be empty")
    
    # Count occurrences
    occurrences = count_occurrences(content, old_string)
    
    if occurrences == 0:
        raise ValidationError(f"String not found in file: '{old_string[:50]}{'...' if len(old_string) > 50 else ''}'")
    
    if occurrences > 1 and not replace_all:
        raise ValidationError(
            f"String appears {occurrences} times in file. Use replace_all=True to replace all occurrences, "
            f"or make old_string more specific to target a unique occurrence."
        )
    
    # Perform replacement
    if replace_all:
        new_content = content.replace(old_string, new_string)
        replacements_made = occurrences
    else:
        new_content = content.replace(old_string, new_string, 1)
        replacements_made = 1
    
    return new_content, replacements_made


def write_file_safely(file_path: Path, content: str) -> None:
    """Write content to file with safety checks"""
    # Check if file is writable
    if not os.access(file_path, os.W_OK):
        raise ValidationError(f"File is not writable: {file_path}")
    
    try:
        # Write to a temporary file first, then rename (atomic operation)
        temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Atomic rename
        temp_path.replace(file_path)
        
    except Exception as e:
        # Clean up temp file if it exists
        temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
        if temp_path.exists():
            temp_path.unlink()
        raise ValidationError(f"Failed to write file: {str(e)}")


async def search_replace(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform exact string replacement in a file.
    
    Parameters:
        params: Dictionary containing:
            - file_path: Path to the file to modify (required)
            - old_string: Exact string to find and replace (required)
            - new_string: String to replace it with (required)
            - replace_all: Whether to replace all occurrences (optional, defaults to False)
    
    Returns:
        Dictionary with operation result and metadata
    """
    # Validate params structure
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    # Extract and validate required parameters
    required_fields = ["file_path", "old_string", "new_string"]
    for field in required_fields:
        if field not in params:
            raise ValidationError(f"Missing required field: {field}")
    
    file_path_str = params["file_path"]
    old_string = params["old_string"]
    new_string = params["new_string"]
    replace_all = params.get("replace_all", False)
    
    # Validate parameter types
    if not isinstance(replace_all, bool):
        raise ValidationError("replace_all must be a boolean")
    
    try:
        # Validate file path
        file_path = validate_file_path(file_path_str)
        
        # Validate strings
        validate_strings(old_string, new_string)
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    original_content = f.read()
            except Exception as e:
                raise ValidationError(f"Failed to read file (encoding issue): {str(e)}")
        except Exception as e:
            raise ValidationError(f"Failed to read file: {str(e)}")
        
        # Perform replacement
        new_content, replacements_made = perform_replacement(
            original_content, old_string, new_string, replace_all
        )
        
        # Write back to file if content changed
        if new_content != original_content:
            write_file_safely(file_path, new_content)
        
        return SearchReplaceResult(
            success=True,
            replacements_made=replacements_made,
            file_path=str(file_path)
        ).to_dict()
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Search and replace operation failed: {str(e)}")


async def search_replace_multiple(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform multiple string replacements in a file.
    
    Parameters:
        params: Dictionary containing:
            - file_path: Path to the file to modify (required)
            - replacements: List of replacement objects, each containing:
                - old_string: String to find
                - new_string: String to replace with
                - replace_all: Whether to replace all occurrences (optional)
    
    Returns:
        Dictionary with operation result and metadata
    """
    # Validate params structure
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    if "file_path" not in params:
        raise ValidationError("Missing required field: file_path")
    
    if "replacements" not in params:
        raise ValidationError("Missing required field: replacements")
    
    file_path_str = params["file_path"]
    replacements = params["replacements"]
    
    if not isinstance(replacements, list):
        raise ValidationError("replacements must be a list")
    
    if not replacements:
        raise ValidationError("replacements list cannot be empty")
    
    try:
        # Validate file path
        file_path = validate_file_path(file_path_str)
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                raise ValidationError(f"Failed to read file (encoding issue): {str(e)}")
        except Exception as e:
            raise ValidationError(f"Failed to read file: {str(e)}")
        
        original_content = content
        total_replacements = 0
        replacement_details = []
        
        # Process each replacement
        for i, replacement in enumerate(replacements):
            if not isinstance(replacement, dict):
                raise ValidationError(f"Replacement {i} must be a dictionary")
            
            if "old_string" not in replacement or "new_string" not in replacement:
                raise ValidationError(f"Replacement {i} missing required fields: old_string, new_string")
            
            old_string = replacement["old_string"]
            new_string = replacement["new_string"]
            replace_all = replacement.get("replace_all", False)
            
            # Validate strings
            validate_strings(old_string, new_string)
            
            if not isinstance(replace_all, bool):
                raise ValidationError(f"Replacement {i}: replace_all must be a boolean")
            
            # Perform replacement
            try:
                content, replacements_made = perform_replacement(
                    content, old_string, new_string, replace_all
                )
                total_replacements += replacements_made
                replacement_details.append({
                    "index": i,
                    "old_string": old_string[:50] + "..." if len(old_string) > 50 else old_string,
                    "new_string": new_string[:50] + "..." if len(new_string) > 50 else new_string,
                    "replacements_made": replacements_made,
                    "replace_all": replace_all
                })
            except ValidationError as e:
                raise ValidationError(f"Replacement {i} failed: {str(e)}")
        
        # Write back to file if content changed
        if content != original_content:
            write_file_safely(file_path, content)
        
        return {
            "success": True,
            "total_replacements": total_replacements,
            "file_path": str(file_path),
            "replacement_details": replacement_details
        }
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Multiple search and replace operation failed: {str(e)}")
