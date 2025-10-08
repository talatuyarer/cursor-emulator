import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..state.validators import ValidationError


# Security configuration
ALLOWED_COMMANDS = {
    # File operations
    'ls', 'cat', 'head', 'tail', 'grep', 'find', 'wc', 'sort', 'uniq',
    'cp', 'mv', 'mkdir', 'rmdir', 'touch', 'chmod', 'chown',
    
    # Text processing
    'sed', 'awk', 'cut', 'paste', 'tr', 'diff', 'patch',
    
    # Archive operations
    'tar', 'zip', 'unzip', 'gzip', 'gunzip',
    
    # Development tools
    'git', 'npm', 'yarn', 'pip', 'python', 'python3', 'node', 'make',
    'gcc', 'g++', 'clang', 'clang++', 'javac', 'java',
    
    # System info
    'pwd', 'whoami', 'date', 'uptime', 'ps', 'top', 'df', 'du',
    
    # Network (limited)
    'curl', 'wget', 'ping', 'nslookup',
    
    # Package managers
    'apt', 'yum', 'dnf', 'brew', 'pacman',
    
    # Build tools
    'cmake', 'make', 'ninja', 'maven', 'gradle',
    
    # Version control
    'svn', 'hg', 'bzr',
    
    # Shell utilities
    'echo', 'printf', 'test', 'true', 'false', 'which', 'whereis',
    'env', 'export', 'unset', 'alias', 'unalias',
}

# Dangerous commands that should be blocked
BLOCKED_COMMANDS = {
    'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs', 'dd',
    'shutdown', 'reboot', 'halt', 'poweroff', 'init',
    'killall', 'pkill', 'kill', 'kill -9',
    'sudo', 'su', 'passwd', 'useradd', 'userdel',
    'chroot', 'mount', 'umount', 'umount -f',
    'iptables', 'ufw', 'firewall-cmd',
    'systemctl', 'service', 'rc-service',
    'crontab', 'at', 'batch',
    'ssh', 'scp', 'rsync', 'nc', 'netcat', 'telnet',
    'wget', 'curl',  # Blocked by default, can be enabled per-command
}

# Dangerous patterns in commands
DANGEROUS_PATTERNS = [
    r'rm\s+-rf\s+/',  # rm -rf /
    r'rm\s+-rf\s+\*',  # rm -rf *
    r':\(\)\s*\{\s*:\s*\|',  # Fork bomb
    r'mkfs\.',  # Format commands
    r'fdisk',  # Disk partitioning
    r'dd\s+if=',  # dd commands
    r'>\s*/dev/',  # Writing to device files
    r'cat\s+>\s*/dev/',  # Writing to device files
    r'echo\s+.*>\s*/dev/',  # Writing to device files
    r'sudo\s+',  # sudo commands
    r'su\s+',  # su commands
    r'chmod\s+777',  # Overly permissive permissions
    r'chown\s+-R\s+root',  # Changing ownership to root
]

# Maximum command length
MAX_COMMAND_LENGTH = 1000

# Maximum timeout
MAX_TIMEOUT = 300  # 5 minutes


def validate_command_security(command: str) -> None:
    """
    Validate command against security rules.
    
    Raises:
        ValidationError: If command is deemed unsafe
    """
    # Check command length
    if len(command) > MAX_COMMAND_LENGTH:
        raise ValidationError(f"Command too long (max {MAX_COMMAND_LENGTH} characters)")
    
    # Extract the base command (first word)
    base_command = command.strip().split()[0] if command.strip() else ""
    
    # Check against blocked commands
    if base_command in BLOCKED_COMMANDS:
        raise ValidationError(f"Command '{base_command}' is not allowed for security reasons")
    
    # Check against dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            raise ValidationError(f"Command contains dangerous pattern: {pattern}")
    
    # Check if command starts with allowed command (optional whitelist)
    # This is more restrictive - uncomment to enable
    # if base_command not in ALLOWED_COMMANDS:
    #     raise ValidationError(f"Command '{base_command}' is not in the allowed commands list")


def validate_working_directory(cwd: Path, workspace_root: Path) -> None:
    """
    Validate that working directory is within allowed bounds.
    
    Args:
        cwd: The requested working directory
        workspace_root: The workspace root directory
        
    Raises:
        ValidationError: If working directory is not allowed
    """
    # Ensure working directory is within workspace
    try:
        cwd.relative_to(workspace_root)
    except ValueError:
        raise ValidationError(f"Working directory must be within workspace: {workspace_root}")


def get_workspace_root() -> Path:
    """
    Get the workspace root directory.
    
    Returns:
        Path to workspace root
    """
    # Try to get from environment variables first
    workspace_path = os.environ.get('CURSOR_WORKSPACE_PATH') or os.environ.get('WORKSPACE_PATH')
    if workspace_path:
        return Path(workspace_path).resolve()
    
    # Fall back to current working directory
    return Path.cwd().resolve()


async def run_terminal_cmd(params: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a terminal command in the workspace directory.

    Parameters:
        params: Dictionary containing:
            - command: The command to execute (required)
            - cwd: Working directory (optional, defaults to workspace root)
            - timeout: Command timeout in seconds (optional, defaults to 30)

    Returns:
        Dictionary with command results including stdout, stderr, return_code, and execution_time

    Raises:
        ValidationError: If parameters are invalid or command execution fails
    """
    # Validate params structure
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")

    if "command" not in params:
        raise ValidationError("Missing required field: command")

    command = params["command"]
    if not isinstance(command, str) or not command.strip():
        raise ValidationError("Command must be a non-empty string")

    # Get optional parameters
    cwd = params.get("cwd")
    timeout = params.get("timeout", 30)
    sandbox = params.get("sandbox", True)  # Enable sandbox by default

    # Validate timeout
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValidationError("Timeout must be a positive number")
    
    if timeout > MAX_TIMEOUT:
        raise ValidationError(f"Timeout too long (max {MAX_TIMEOUT} seconds)")

    # Security validation
    if sandbox:
        validate_command_security(command)

    # Get workspace root for security validation
    workspace_root = get_workspace_root()

    # Determine working directory
    if cwd:
        if not isinstance(cwd, str):
            raise ValidationError("Working directory must be a string")
        working_dir = Path(cwd).resolve()
        if not working_dir.exists() or not working_dir.is_dir():
            raise ValidationError(f"Working directory does not exist or is not a directory: {cwd}")
        
        # Security: Ensure working directory is within workspace
        if sandbox:
            validate_working_directory(working_dir, workspace_root)
    else:
        # Default to workspace root for security
        working_dir = workspace_root

    try:
        # Execute the command
        start_time = asyncio.get_event_loop().time()
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise ValidationError(f"Command timed out after {timeout} seconds")

        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time

        # Decode bytes to strings
        stdout = stdout_bytes.decode('utf-8', errors='replace')
        stderr = stderr_bytes.decode('utf-8', errors='replace')

        return {
            "success": True,
            "command": command,
            "cwd": str(working_dir),
            "return_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time": execution_time,
            "timed_out": False,
            "sandbox_enabled": sandbox,
            "workspace_root": str(workspace_root)
        }

    except ValidationError:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Wrap other errors
        raise ValidationError(f"Failed to execute command: {str(e)}")
