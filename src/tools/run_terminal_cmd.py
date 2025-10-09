import asyncio
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

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


# Background process management
background_processes: Dict[str, Dict[str, Any]] = {}


async def get_background_process_status(process_id: str) -> dict[str, Any]:
    """
    Get status of a background process.
    
    Parameters:
        process_id: ID of the background process to check
        
    Returns:
        Dictionary with process status information
    """
    if not isinstance(process_id, str) or not process_id.strip():
        raise ValidationError("Process ID must be a non-empty string")
    
    if process_id not in background_processes:
        raise ValidationError(f"Background process '{process_id}' not found")
    
    process_info = background_processes[process_id]
    process = process_info.get("process")
    
    # Check if process was killed or completed
    if process is None and process_info.get("status") in ["killed", "completed", "error"]:
        # Process has finished, return its final status
        return {
            "success": True,
            "process_id": process_id,
            "status": process_info["status"],
            "command": process_info["command"],
            "start_time": process_info["start_time"],
            "end_time": process_info.get("end_time", time.time()),
            "return_code": process_info.get("return_code"),
            "stdout": process_info.get("stdout", ""),
            "stderr": process_info.get("stderr", ""),
            "runtime": process_info.get("end_time", time.time()) - process_info["start_time"]
        }
    elif process is None:
        return {
            "success": False,
            "error": f"Process '{process_id}' is no longer running",
            "process_id": process_id,
            "status": "not_found"
        }
    
    # Check if process is still running
    if process.returncode is not None:
        # Process has completed
        process_info["status"] = "completed"
        process_info["end_time"] = time.time()
        process_info["return_code"] = process.returncode
        
        return {
            "success": True,
            "process_id": process_id,
            "status": "completed",
            "command": process_info["command"],
            "start_time": process_info["start_time"],
            "end_time": process_info["end_time"],
            "return_code": process.returncode,
            "stdout": process_info.get("stdout", ""),
            "stderr": process_info.get("stderr", ""),
            "runtime": process_info["end_time"] - process_info["start_time"]
        }
    else:
        # Process is still running
        runtime = time.time() - process_info["start_time"]
        return {
            "success": True,
            "process_id": process_id,
            "status": "running",
            "command": process_info["command"],
            "start_time": process_info["start_time"],
            "runtime": runtime,
            "return_code": None
        }


async def kill_background_process(process_id: str) -> dict[str, Any]:
    """
    Kill a background process.
    
    Parameters:
        process_id: ID of the background process to kill
        
    Returns:
        Dictionary with kill result
    """
    if not isinstance(process_id, str) or not process_id.strip():
        raise ValidationError("Process ID must be a non-empty string")
    
    if process_id not in background_processes:
        raise ValidationError(f"Background process '{process_id}' not found")
    
    process_info = background_processes[process_id]
    process = process_info.get("process")
    
    if process is None:
        return {
            "success": False,
            "error": f"Process '{process_id}' is no longer running",
            "process_id": process_id
        }
    
    try:
        # Kill the process
        process.terminate()
        
        # Wait a bit for graceful termination
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            # Force kill if it doesn't terminate gracefully
            process.kill()
            await process.wait()
        
        # Update process info
        process_info["status"] = "killed"
        process_info["end_time"] = time.time()
        process_info["return_code"] = process.returncode
        
        # Remove the process from the monitoring task
        process_info["process"] = None
        
        return {
            "success": True,
            "process_id": process_id,
            "status": "killed",
            "command": process_info["command"],
            "start_time": process_info["start_time"],
            "end_time": process_info["end_time"],
            "return_code": process.returncode,
            "runtime": process_info["end_time"] - process_info["start_time"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to kill process '{process_id}': {str(e)}",
            "process_id": process_id
        }


async def list_background_processes() -> dict[str, Any]:
    """
    List all background processes.
    
    Returns:
        Dictionary with list of background processes
    """
    processes = []
    
    for process_id, process_info in background_processes.items():
        process = process_info.get("process")
        
        if process is None:
            status = "not_found"
            return_code = None
            runtime = 0
        elif process.returncode is not None:
            status = "completed"
            return_code = process.returncode
            runtime = (process_info.get("end_time", time.time()) - process_info["start_time"])
        else:
            status = "running"
            return_code = None
            runtime = time.time() - process_info["start_time"]
        
        processes.append({
            "process_id": process_id,
            "command": process_info["command"],
            "status": status,
            "start_time": process_info["start_time"],
            "runtime": runtime,
            "return_code": return_code
        })
    
    return {
        "success": True,
        "processes": processes,
        "total_processes": len(processes),
        "running_processes": len([p for p in processes if p["status"] == "running"]),
        "completed_processes": len([p for p in processes if p["status"] == "completed"])
    }


async def run_background_command(command: str, cwd: Optional[str] = None, 
                               sandbox: bool = True) -> dict[str, Any]:
    """
    Run a command in the background.
    
    Parameters:
        command: Command to execute
        cwd: Working directory (optional)
        sandbox: Enable sandbox security (default: True)
        
    Returns:
        Dictionary with process information
    """
    # Validate command
    validate_command_security(command)
    
    # Get workspace root
    workspace_root = get_workspace_root()
    
    # Validate working directory
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
    
    # Generate unique process ID
    process_id = str(uuid.uuid4())
    
    try:
        # Start the process
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        
        # Store process information
        background_processes[process_id] = {
            "process": process,
            "command": command,
            "cwd": str(working_dir),
            "start_time": time.time(),
            "status": "running",
            "sandbox_enabled": sandbox
        }
        
        # Start monitoring task
        asyncio.create_task(monitor_background_process(process_id))
        
        return {
            "success": True,
            "process_id": process_id,
            "command": command,
            "cwd": str(working_dir),
            "status": "started",
            "start_time": background_processes[process_id]["start_time"],
            "sandbox_enabled": sandbox
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to start background process: {str(e)}",
            "command": command,
            "cwd": str(working_dir),
            "sandbox_enabled": sandbox
        }


async def monitor_background_process(process_id: str):
    """
    Monitor a background process and update its status when it completes.
    
    Parameters:
        process_id: ID of the background process to monitor
    """
    if process_id not in background_processes:
        return
    
    process_info = background_processes[process_id]
    process = process_info.get("process")
    
    if process is None:
        return
    
    try:
        # Wait for process to complete
        stdout_bytes, stderr_bytes = await process.communicate()
        
        # Update process info
        process_info["status"] = "completed"
        process_info["end_time"] = time.time()
        process_info["return_code"] = process.returncode
        process_info["stdout"] = stdout_bytes.decode('utf-8', errors='replace')
        process_info["stderr"] = stderr_bytes.decode('utf-8', errors='replace')
        
    except Exception as e:
        # Process was killed or errored
        process_info["status"] = "error"
        process_info["end_time"] = time.time()
        process_info["error"] = str(e)
        process_info["return_code"] = process.returncode if process.returncode is not None else -1
