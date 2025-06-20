from enum import Enum
from typing import Any, TypedDict


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TodoPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Todo(TypedDict):
    id: str
    content: str
    status: TodoStatus
    priority: TodoPriority
    created_at: str
    updated_at: str
    metadata: dict[str, Any] | None


class TaskStore(TypedDict):
    lastModified: str
    todos: list[Todo]


class TodoReadResponse(TypedDict):
    todos: list[Todo]


class TodoWriteParams(TypedDict):
    todos: list[dict[str, Any]]


class TodoWriteResponse(TypedDict):
    success: bool
    count: int
