from typing import Any

from ..types import TodoPriority, TodoStatus


class ValidationError(Exception):
    """Raised when todo validation fails"""

    pass


def validate_todos(todos: list[dict[str, Any]]) -> None:
    """
    Validate a list of todos according to business rules:
    1. All todos must have required fields
    2. All IDs must be unique
    3. Only one task can be in_progress at a time
    """
    if not isinstance(todos, list):
        raise ValidationError("Todos must be a list")

    # Check for required fields
    required_fields = {"id", "content", "status", "priority"}
    for i, todo in enumerate(todos):
        if not isinstance(todo, dict):
            raise ValidationError(f"Todo at index {i} must be a dictionary")

        missing_fields = required_fields - set(todo.keys())
        if missing_fields:
            raise ValidationError(
                f"Todo at index {i} missing required fields: {missing_fields}"
            )

        # Validate field types
        if not isinstance(todo["id"], str) or not todo["id"].strip():
            raise ValidationError(f"Todo at index {i} must have a non-empty string ID")

        if not isinstance(todo["content"], str) or not todo["content"].strip():
            raise ValidationError(f"Todo at index {i} must have non-empty content")

        # Validate status
        try:
            TodoStatus(todo["status"])
        except ValueError:
            raise ValidationError(
                f"Todo at index {i} has invalid status: {todo['status']}. "
                f"Must be one of: {[s.value for s in TodoStatus]}"
            )

        # Validate priority
        try:
            TodoPriority(todo["priority"])
        except ValueError:
            raise ValidationError(
                f"Todo at index {i} has invalid priority: {todo['priority']}. "
                f"Must be one of: {[p.value for p in TodoPriority]}"
            )

    # Check for unique IDs
    ids = [todo["id"] for todo in todos]
    if len(ids) != len(set(ids)):
        duplicates = [id for id in ids if ids.count(id) > 1]
        raise ValidationError(f"Duplicate todo IDs found: {set(duplicates)}")

    # Check only one in_progress task
    in_progress_todos = [
        todo for todo in todos if todo["status"] == TodoStatus.IN_PROGRESS.value
    ]
    if len(in_progress_todos) > 1:
        raise ValidationError(
            f"Only one task can be in_progress at a time. "
            f"Found {len(in_progress_todos)} in_progress tasks."
        )
