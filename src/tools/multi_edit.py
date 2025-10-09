import os
from pathlib import Path
from typing import Any, Dict, List

from ..state.validators import ValidationError


class EditOperation:
    """Represents a single edit operation"""
    
    def __init__(self, old_string: str, new_string: str, replace_all: bool = False):
        self.old_string = old_string
        self.new_string = new_string
        self.replace_all = replace_all
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "old_string": self.old_string,
            "new_string": self.new_string,
            "replace_all": self.replace_all
        }


class MultiEditResult:
    """Represents the result of a multi-edit operation"""
    
    def __init__(self, success: bool, total_edits: int = 0, 
                 successful_edits: int = 0, failed_edit_index: int = -1,
                 error_message: str = "", file_path: str = ""):
        self.success = success
        self.total_edits = total_edits
        self.successful_edits = successful_edits
        self.failed_edit_index = failed_edit_index
        self.error_message = error_message
        self.file_path = file_path
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "total_edits": self.total_edits,
            "successful_edits": self.successful_edits,
            "failed_edit_index": self.failed_edit_index,
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


def validate_edit_operations(edits: List[Dict[str, Any]]) -> List[EditOperation]:
    """Validate and convert edit operations"""
    if not isinstance(edits, list):
        raise ValidationError("Edits must be a list")
    
    if not edits:
        raise ValidationError("Edits list cannot be empty")
    
    if len(edits) > 100:  # Reasonable limit
        raise ValidationError("Too many edits (maximum 100 allowed)")
    
    edit_operations = []
    
    for i, edit in enumerate(edits):
        if not isinstance(edit, dict):
            raise ValidationError(f"Edit {i} must be a dictionary")
        
        # Validate required fields
        required_fields = ["old_string", "new_string"]
        for field in required_fields:
            if field not in edit:
                raise ValidationError(f"Edit {i} missing required field: {field}")
        
        old_string = edit["old_string"]
        new_string = edit["new_string"]
        replace_all = edit.get("replace_all", False)
        
        # Validate field types
        if not isinstance(old_string, str):
            raise ValidationError(f"Edit {i}: old_string must be a string")
        
        if not isinstance(new_string, str):
            raise ValidationError(f"Edit {i}: new_string must be a string")
        
        if not isinstance(replace_all, bool):
            raise ValidationError(f"Edit {i}: replace_all must be a boolean")
        
        # Validate old_string is not empty
        if not old_string.strip():
            raise ValidationError(f"Edit {i}: old_string cannot be empty")
        
        edit_operations.append(EditOperation(old_string, new_string, replace_all))
    
    return edit_operations


def count_occurrences(content: str, search_string: str) -> int:
    """Count occurrences of search_string in content"""
    if not search_string:
        return 0
    return content.count(search_string)


def apply_single_edit(content: str, edit: EditOperation) -> tuple[str, int]:
    """
    Apply a single edit operation to content.
    
    Returns:
        tuple: (new_content, number_of_replacements)
    """
    # Count occurrences
    occurrences = count_occurrences(content, edit.old_string)
    
    if occurrences == 0:
        raise ValidationError(f"String not found: '{edit.old_string[:50]}{'...' if len(edit.old_string) > 50 else ''}'")
    
    if occurrences > 1 and not edit.replace_all:
        raise ValidationError(
            f"String appears {occurrences} times. Use replace_all=True to replace all occurrences, "
            f"or make old_string more specific to target a unique occurrence."
        )
    
    # Apply replacement
    if edit.replace_all:
        new_content = content.replace(edit.old_string, edit.new_string)
        replacements_made = occurrences
    else:
        new_content = content.replace(edit.old_string, edit.new_string, 1)
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


def read_file_safely(file_path: Path) -> str:
    """Read file content with encoding fallback"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            raise ValidationError(f"Failed to read file (encoding issue): {str(e)}")
    except Exception as e:
        raise ValidationError(f"Failed to read file: {str(e)}")


async def multi_edit(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform multiple edits to a single file in one atomic operation.
    
    Parameters:
        params: Dictionary containing:
            - file_path: Path to the file to edit (required)
            - edits: List of edit operations, each containing:
                - old_string: String to find and replace (required)
                - new_string: String to replace with (required)
                - replace_all: Whether to replace all occurrences (optional, defaults to False)
    
    Returns:
        Dictionary with operation result and metadata
    """
    # Validate params structure
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    # Extract and validate required parameters
    if "file_path" not in params:
        raise ValidationError("Missing required field: file_path")
    
    if "edits" not in params:
        raise ValidationError("Missing required field: edits")
    
    file_path_str = params["file_path"]
    edits_data = params["edits"]
    
    try:
        # Validate file path
        file_path = validate_file_path(file_path_str)
        
        # Validate edit operations
        edit_operations = validate_edit_operations(edits_data)
        
        # Read original file content
        original_content = read_file_safely(file_path)
        current_content = original_content
        
        # Apply all edits sequentially
        successful_edits = 0
        total_replacements = 0
        edit_details = []
        
        for i, edit in enumerate(edit_operations):
            try:
                # Apply the edit
                new_content, replacements_made = apply_single_edit(current_content, edit)
                current_content = new_content
                successful_edits += 1
                total_replacements += replacements_made
                
                edit_details.append({
                    "index": i,
                    "old_string": edit.old_string[:50] + "..." if len(edit.old_string) > 50 else edit.old_string,
                    "new_string": edit.new_string[:50] + "..." if len(edit.new_string) > 50 else edit.new_string,
                    "replacements_made": replacements_made,
                    "replace_all": edit.replace_all,
                    "success": True
                })
                
            except ValidationError as e:
                # Edit failed - return error with details
                edit_details.append({
                    "index": i,
                    "old_string": edit.old_string[:50] + "..." if len(edit.old_string) > 50 else edit.old_string,
                    "new_string": edit.new_string[:50] + "..." if len(edit.new_string) > 50 else edit.new_string,
                    "replace_all": edit.replace_all,
                    "success": False,
                    "error": str(e)
                })
                
                return {
                    "success": False,
                    "total_edits": len(edit_operations),
                    "successful_edits": successful_edits,
                    "failed_edit_index": i,
                    "error_message": f"Edit {i} failed: {str(e)}",
                    "file_path": str(file_path),
                    "edit_details": edit_details
                }
        
        # All edits succeeded - write the file
        if current_content != original_content:
            write_file_safely(file_path, current_content)
        
        return {
            "success": True,
            "total_edits": len(edit_operations),
            "successful_edits": successful_edits,
            "total_replacements": total_replacements,
            "file_path": str(file_path),
            "edit_details": edit_details
        }
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Multi-edit operation failed: {str(e)}")


async def multi_edit_validate_only(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate multi-edit operations without applying them.
    
    Parameters:
        params: Dictionary containing:
            - file_path: Path to the file to validate against (required)
            - edits: List of edit operations to validate (required)
    
    Returns:
        Dictionary with validation results
    """
    # Validate params structure
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    if "file_path" not in params:
        raise ValidationError("Missing required field: file_path")
    
    if "edits" not in params:
        raise ValidationError("Missing required field: edits")
    
    file_path_str = params["file_path"]
    edits_data = params["edits"]
    
    try:
        # Validate file path
        file_path = validate_file_path(file_path_str)
        
        # Validate edit operations
        edit_operations = validate_edit_operations(edits_data)
        
        # Read file content
        content = read_file_safely(file_path)
        
        # Validate each edit
        validation_results = []
        all_valid = True
        
        for i, edit in enumerate(edit_operations):
            try:
                # Check if string exists
                occurrences = count_occurrences(content, edit.old_string)
                
                if occurrences == 0:
                    validation_results.append({
                        "index": i,
                        "valid": False,
                        "error": "String not found",
                        "occurrences": 0
                    })
                    all_valid = False
                elif occurrences > 1 and not edit.replace_all:
                    validation_results.append({
                        "index": i,
                        "valid": False,
                        "error": f"String appears {occurrences} times. Use replace_all=True",
                        "occurrences": occurrences
                    })
                    all_valid = False
                else:
                    validation_results.append({
                        "index": i,
                        "valid": True,
                        "error": None,
                        "occurrences": occurrences
                    })
                    
            except Exception as e:
                validation_results.append({
                    "index": i,
                    "valid": False,
                    "error": str(e),
                    "occurrences": 0
                })
                all_valid = False
        
        return {
            "success": True,
            "all_valid": all_valid,
            "total_edits": len(edit_operations),
            "valid_edits": sum(1 for r in validation_results if r["valid"]),
            "file_path": str(file_path),
            "validation_results": validation_results
        }
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Multi-edit validation failed: {str(e)}")
