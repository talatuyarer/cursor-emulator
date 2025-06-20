from ..state.store import store
from ..types import TodoReadResponse


async def todo_read() -> TodoReadResponse:
    """
    Read the current task list.

    Returns:
        TodoReadResponse with list of todos
    """
    # Read todos
    todos = await store.read_todos()

    # Return response
    return {"todos": todos}
