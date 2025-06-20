import json
import os
from datetime import datetime
from pathlib import Path

from ..types import TaskStore


class FilePersistence:
    """File-based persistence using JSON"""

    def __init__(self, path: str | None = None):
        if path is None:
            # Default to ~/.mcp-tasks/state.json
            home = Path.home()
            self.dir_path = home / ".mcp-tasks"
            self.file_path = self.dir_path / "state.json"
        else:
            self.file_path = Path(path).expanduser()
            self.dir_path = self.file_path.parent

    async def load(self) -> TaskStore:
        """Load task store from file, creating default if not exists"""
        if not self.file_path.exists():
            # Return default empty store
            return {
                "lastModified": datetime.now().isoformat(),
                "todos": [],
            }

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all required fields are present
                return {
                    "lastModified": data.get(
                        "lastModified", datetime.now().isoformat()
                    ),
                    "todos": data.get("todos", []),
                }
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, backup and return empty store
            backup_path = self.file_path.with_suffix(".json.backup")
            if self.file_path.exists():
                self.file_path.rename(backup_path)

            return {
                "lastModified": datetime.now().isoformat(),
                "todos": [],
            }

    async def save(self, store: TaskStore) -> None:
        """Save task store to file with atomic write"""
        # Ensure directory exists
        self.dir_path.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first (atomic write)
        temp_path = self.file_path.with_suffix(".json.tmp")

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(store, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(self.file_path)

            # Set appropriate permissions (user read/write only)
            os.chmod(self.file_path, 0o600)

        except Exception:
            # Clean up temp file if something went wrong
            if temp_path.exists():
                temp_path.unlink()
            raise

    async def clear(self) -> None:
        """Remove the state file"""
        if self.file_path.exists():
            self.file_path.unlink()
