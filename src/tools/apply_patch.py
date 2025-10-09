import asyncio
import tempfile
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import subprocess

from ..state.validators import ValidationError


class PatchApplier:
    """Applies patches to files using the Linux patch command with context validation"""
    
    def __init__(self):
        self.patch_command = "patch"
        self.max_retries = 3
    
    def validate_patch_format(self, patch_content: str) -> None:
        """Validate that the patch content is in unified diff format"""
        if not patch_content.strip():
            raise ValidationError("Patch content cannot be empty")
        
        # Check for unified diff format indicators
        if not any(line.startswith("---") for line in patch_content.split('\n')):
            raise ValidationError("Patch must be in unified diff format (missing '---' header)")
        
        if not any(line.startswith("+++") for line in patch_content.split('\n')):
            raise ValidationError("Patch must be in unified diff format (missing '+++' header)")
        
        # Check for hunk headers
        if not any(line.startswith("@@") for line in patch_content.split('\n')):
            raise ValidationError("Patch must contain hunk headers (lines starting with '@@')")
    
    def validate_file_path(self, file_path: Path) -> None:
        """Validate that the target file exists and is writable"""
        if not file_path.exists():
            raise ValidationError(f"Target file does not exist: {file_path}")
        
        if not file_path.is_file():
            raise ValidationError(f"Target path is not a file: {file_path}")
        
        if not os.access(file_path, os.W_OK):
            raise ValidationError(f"Target file is not writable: {file_path}")
    
    def create_patch_file(self, patch_content: str) -> Path:
        """Create a temporary file with the patch content"""
        patch_file = tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False)
        patch_file.write(patch_content)
        patch_file.close()
        return Path(patch_file.name)
    
    def create_backup_file(self, target_file: Path) -> Path:
        """Create a backup of the target file"""
        backup_file = tempfile.NamedTemporaryFile(delete=False, suffix='.backup')
        backup_file.close()
        
        # Copy the original file to backup
        import shutil
        shutil.copy2(target_file, backup_file.name)
        return Path(backup_file.name)
    
    def restore_from_backup(self, target_file: Path, backup_file: Path) -> None:
        """Restore the target file from backup"""
        import shutil
        shutil.copy2(backup_file, target_file)
    
    async def apply_patch_with_retry(self, target_file: Path, patch_file: Path, 
                                   backup_file: Path, dry_run: bool = False) -> Dict[str, Any]:
        """Apply patch with retry logic and proper error handling"""
        
        for attempt in range(self.max_retries):
            try:
                # Build patch command
                cmd = [
                    self.patch_command,
                    "-p0",  # Strip 0 path components
                    "-i", str(patch_file),  # Input patch file
                    str(target_file)  # Target file
                ]
                
                if dry_run:
                    cmd.append("--dry-run")
                
                # Execute patch command
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=target_file.parent
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    # Patch applied successfully
                    return {
                        "success": True,
                        "attempt": attempt + 1,
                        "stdout": stdout.decode('utf-8', errors='replace'),
                        "stderr": stderr.decode('utf-8', errors='replace'),
                        "dry_run": dry_run
                    }
                else:
                    # Patch failed
                    error_output = stderr.decode('utf-8', errors='replace')
                    
                    # Check for specific error conditions
                    if "Hunk #" in error_output and "FAILED" in error_output:
                        # Context mismatch - this is usually not recoverable
                        raise ValidationError(f"Patch context mismatch: {error_output}")
                    elif "No such file or directory" in error_output:
                        raise ValidationError(f"File not found: {error_output}")
                    elif "Permission denied" in error_output:
                        raise ValidationError(f"Permission denied: {error_output}")
                    else:
                        # Generic patch failure
                        if attempt < self.max_retries - 1:
                            # Restore from backup and retry
                            self.restore_from_backup(target_file, backup_file)
                            continue
                        else:
                            raise ValidationError(f"Patch application failed: {error_output}")
                            
            except asyncio.TimeoutError:
                if attempt < self.max_retries - 1:
                    # Restore from backup and retry
                    self.restore_from_backup(target_file, backup_file)
                    continue
                else:
                    raise ValidationError("Patch application timed out")
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    # Restore from backup and retry
                    self.restore_from_backup(target_file, backup_file)
                    continue
                else:
                    raise ValidationError(f"Patch application failed: {str(e)}")
        
        # If we get here, all retries failed
        raise ValidationError(f"Patch application failed after {self.max_retries} attempts")
    
    async def apply_patch(self, file_path: str, patch_content: str, 
                         dry_run: bool = False, create_backup: bool = True) -> Dict[str, Any]:
        """
        Apply a patch to a file using the Linux patch command.
        
        Args:
            file_path: Path to the target file
            patch_content: Unified diff patch content
            dry_run: If True, only validate the patch without applying it
            create_backup: If True, create a backup before applying the patch
        
        Returns:
            Dictionary with patch application results
        """
        # Convert to Path object
        target_file = Path(file_path).resolve()
        
        # Validate inputs
        self.validate_patch_format(patch_content)
        self.validate_file_path(target_file)
        
        # Create temporary files
        patch_file = None
        backup_file = None
        
        try:
            # Create patch file
            patch_file = self.create_patch_file(patch_content)
            
            # Create backup if requested
            if create_backup and not dry_run:
                backup_file = self.create_backup_file(target_file)
            
            # Apply the patch
            result = await self.apply_patch_with_retry(target_file, patch_file, backup_file, dry_run)
            
            # Add metadata to result
            result.update({
                "target_file": str(target_file),
                "patch_file": str(patch_file),
                "backup_file": str(backup_file) if backup_file else None,
                "patch_size": len(patch_content),
                "lines_changed": patch_content.count('\n')
            })
            
            return result
            
        except Exception as e:
            # Restore from backup if it exists and patch failed
            if backup_file and backup_file.exists() and not dry_run:
                try:
                    self.restore_from_backup(target_file, backup_file)
                except Exception as restore_error:
                    # Log restore error but don't mask the original error
                    pass
            
            raise e
            
        finally:
            # Clean up temporary files
            if patch_file and patch_file.exists():
                try:
                    patch_file.unlink()
                except Exception:
                    pass
            
            if backup_file and backup_file.exists():
                try:
                    backup_file.unlink()
                except Exception:
                    pass


def validate_apply_patch_parameters(file_path: str, patch_content: str) -> None:
    """Validate parameters for apply_patch function"""
    if not file_path or not isinstance(file_path, str):
        raise ValidationError("file_path must be a non-empty string")
    
    if not patch_content or not isinstance(patch_content, str):
        raise ValidationError("patch_content must be a non-empty string")
    
    # Basic file path validation
    if len(file_path) > 1000:
        raise ValidationError("file_path is too long")
    
    # Basic patch content validation
    if len(patch_content) > 1000000:  # 1MB limit
        raise ValidationError("patch_content is too large (max 1MB)")
    
    # Check for potentially dangerous patterns in patch
    dangerous_patterns = [
        "rm -rf",
        "sudo",
        "chmod 777",
        "> /dev/null",
        "&&",
        "||",
        "`",
        "$("
    ]
    
    for pattern in dangerous_patterns:
        if pattern in patch_content:
            raise ValidationError(f"Patch contains potentially dangerous pattern: {pattern}")


async def apply_patch(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply a unified diff patch to a file using the Linux patch command.
    
    Parameters:
        params: Dictionary containing:
            - file_path: Path to the target file (required)
            - patch_content: Unified diff patch content (required)
            - dry_run: If True, only validate without applying (optional, defaults to False)
            - create_backup: If True, create backup before applying (optional, defaults to True)
    
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
    # Validate params structure
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    required_fields = {"file_path", "patch_content"}
    missing_fields = required_fields - set(params.keys())
    if missing_fields:
        raise ValidationError(f"Missing required fields: {missing_fields}")
    
    file_path = params["file_path"]
    patch_content = params["patch_content"]
    dry_run = params.get("dry_run", False)
    create_backup = params.get("create_backup", True)
    
    # Validate parameters
    validate_apply_patch_parameters(file_path, patch_content)
    
    try:
        applier = PatchApplier()
        result = await applier.apply_patch(file_path, patch_content, dry_run, create_backup)
        
        return {
            "success": True,
            "result": result,
            "message": "Patch applied successfully" if not dry_run else "Patch validation successful"
        }
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to apply patch: {str(e)}")
