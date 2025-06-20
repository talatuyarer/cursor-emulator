from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


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
    metadata: Optional[Dict[str, Any]]


class TaskStore(TypedDict):
    lastModified: str
    todos: List[Todo]


class TodoReadResponse(TypedDict):
    todos: List[Todo]


class TodoWriteParams(TypedDict):
    todos: List[Dict[str, Any]]


class TodoWriteResponse(TypedDict):
    success: bool
    count: int
