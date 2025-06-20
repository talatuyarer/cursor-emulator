from typing import Any, Dict

from fastmcp import FastMCP

from .state.validators import ValidationError
from .tools.todo_read import todo_read
from .tools.todo_write import todo_write

# Create the MCP server
mcp = FastMCP(
    "Task Manager",
    instructions="Manages persistent todo lists with TodoRead and TodoWrite tools. TodoRead returns current todos, TodoWrite replaces entire list.",
)


@mcp.tool
async def TodoRead() -> Dict[str, Any]:
    """
    Read the current task list.

    Returns a list of todos with their current state.
    """
    try:
        return await todo_read()
    except Exception as e:
        return {
            "error": {
                "code": "READ_ERROR",
                "message": f"Failed to read todos: {str(e)}",
            }
        }


@mcp.tool
async def TodoWrite(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the entire task list (complete replacement).

    Parameters:
        todos: List of todo items, each containing:
            - id: Unique identifier for the task
            - content: Task description
            - status: Current status (pending, in_progress, completed)
            - priority: Task priority (high, medium, low)
            - metadata: Optional additional data

    Returns success status and count of todos written.
    """
    try:
        return await todo_write(params)
    except ValidationError as e:
        return {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
    except Exception as e:
        return {
            "error": {
                "code": "WRITE_ERROR",
                "message": f"Failed to write todos: {str(e)}",
            }
        }


if __name__ == "__main__":
    mcp.run()
