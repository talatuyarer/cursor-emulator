from ..state.store import store
from ..state.validators import ValidationError
from ..types import TodoWriteParams, TodoWriteResponse


async def todo_write(params: TodoWriteParams) -> TodoWriteResponse:
    """
    Update the entire task list (complete replacement).

    Parameters:
        params: Dictionary containing 'todos' list

    Returns:
        TodoWriteResponse with success status and todo count

    Raises:
        ValidationError: If todos fail validation
    """
    # Validate params structure
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")

    if "todos" not in params:
        raise ValidationError("Missing required field: todos")

    todos = params["todos"]

    try:
        # Write todos (validation happens inside)
        count = await store.write_todos(todos)

        return {"success": True, "count": count}
    except ValidationError:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Wrap other errors
        raise ValidationError(f"Failed to write todos: {str(e)}")
