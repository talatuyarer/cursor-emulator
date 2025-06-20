from datetime import datetime
from typing import Any

from ..types import TaskStore, Todo
from .persistence import FilePersistence
from .validators import validate_todos


class TodoStore:
    """Manages todo state with persistence"""

    def __init__(self, workspace_path: str | None = None):
        self.persistence = FilePersistence(workspace_path)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the store (load from persistence)"""
        if not self._initialized:
            await self.persistence.load()
            self._initialized = True

    async def read_todos(self) -> list[Todo]:
        """Read all todos from the store"""
        await self.initialize()
        store = await self.persistence.load()
        return store["todos"]

    async def write_todos(self, todos: list[dict[str, Any]]) -> int:
        """
        Write todos to the store (complete replacement)
        Returns the number of todos written
        """
        await self.initialize()

        # Validate todos
        validate_todos(todos)

        # Process todos - add/update timestamps
        processed_todos = []
        current_time = datetime.now().isoformat()

        # Load existing store to preserve created_at timestamps
        existing_store = await self.persistence.load()
        existing_todos_map = {todo["id"]: todo for todo in existing_store["todos"]}

        for todo in todos:
            # Preserve created_at if todo already exists
            if todo["id"] in existing_todos_map:
                created_at = existing_todos_map[todo["id"]].get(
                    "created_at", current_time
                )
            else:
                created_at = todo.get("created_at", current_time)

            processed_todo = {
                "id": todo["id"],
                "content": todo["content"],
                "status": todo["status"],
                "priority": todo["priority"],
                "created_at": created_at,
                "updated_at": current_time,
                "metadata": todo.get("metadata", None),
            }
            processed_todos.append(processed_todo)

        # Create new store
        new_store: TaskStore = {
            "lastModified": current_time,
            "todos": processed_todos,
        }

        # Save to persistence
        await self.persistence.save(new_store)

        return len(processed_todos)

    async def clear(self) -> None:
        """Clear all todos"""
        await self.persistence.clear()
        self._initialized = False


# Default store instance
store = TodoStore()
