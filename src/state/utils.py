import os
from importlib.resources import files
from pathlib import Path


def detect_workspace_path() -> Path:
    """
    Detect the workspace directory from environment variables.
    Falls back to current working directory if not found.
    """
    # Try to detect workspace from Cursor's environment variable
    workspace_env = os.environ.get("WORKSPACE_FOLDER_PATHS")
    if workspace_env:
        # WORKSPACE_FOLDER_PATHS might contain multiple paths, take the first one
        workspace_path = workspace_env.split(",")[0].strip()
        return Path(workspace_path)

    return Path.cwd()


def add_to_gitignore(workspace_path: Path, filename: str) -> None:
    """
    Add filename to .gitignore if it exists and entry is not already present.

    Args:
        workspace_path: Path to the workspace directory
        filename: Filename to add to .gitignore
    """
    gitignore_path = workspace_path / ".gitignore"

    if not gitignore_path.exists():
        return

    # Check if already in .gitignore
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        if filename in content:
            return  # Already present

        # Add to .gitignore
        with open(gitignore_path, "a", encoding="utf-8") as f:
            if content and not content.endswith("\n"):
                f.write("\n")
            f.write(f"\n# MCP todo list\n{filename}\n")

    except (IOError, UnicodeDecodeError):
        # If we can't read/write .gitignore, silently fail
        pass


def copy_cursor_rules(workspace_path: Path) -> bool:
    """
    Copy both system-instructions and task-management rules files to workspace .cursor/rules/ directory.
    Always overwrites existing files to ensure latest version.

    Args:
        workspace_path: Path to the workspace directory

    Returns:
        True if both rules files were copied, False if any failed
    """
    # Create .cursor/rules directory if it doesn't exist
    cursor_rules_dir = workspace_path / ".cursor" / "rules"
    cursor_rules_dir.mkdir(parents=True, exist_ok=True)

    # Files to copy
    rules_files = [
        ("00-system-instructions.mdc", "00-system-instructions.mdc"),
        ("01-task-management.mdc", "01-task-management.mdc"),
    ]

    success_count = 0

    for source_filename, target_filename in rules_files:
        target_path = cursor_rules_dir / target_filename

        try:
            # Access the template file from the state package
            template_content = files("src.state").joinpath(source_filename).read_text(encoding="utf-8")

            # Write the content to the target location
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(template_content)
            success_count += 1
        except (IOError, OSError, FileNotFoundError):
            # If we can't copy this file, continue with others
            continue

    return success_count == len(rules_files)
