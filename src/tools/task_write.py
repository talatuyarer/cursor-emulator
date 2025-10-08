import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..state.validators import ValidationError


class TaskStatus:
    """Task status constants with emoji representations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    # Emoji representations for visual display
    EMOJIS = {
        PENDING: "⏳",
        IN_PROGRESS: "🔄", 
        COMPLETED: "✅",
        CANCELLED: "❌"
    }
    
    @classmethod
    def get_emoji(cls, status: str) -> str:
        """Get emoji for a status"""
        return cls.EMOJIS.get(status, "❓")


class TaskPriority:
    """Task priority constants"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
    # Priority indicators
    INDICATORS = {
        HIGH: "🔴",
        MEDIUM: "🟡", 
        LOW: "🟢"
    }
    
    @classmethod
    def get_indicator(cls, priority: str) -> str:
        """Get priority indicator for a priority"""
        return cls.INDICATORS.get(priority, "⚪")


class Task:
    """Represents a single task with all its properties"""
    
    def __init__(self, id: str, content: str, status: str = TaskStatus.PENDING, 
                 priority: str = TaskPriority.MEDIUM, metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.content = content
        self.status = status
        self.priority = priority
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.metadata = metadata or {}
    
    def update_status(self, new_status: str):
        """Update task status and timestamp"""
        self.status = new_status
        self.updated_at = datetime.now().isoformat()
    
    def update_content(self, new_content: str):
        """Update task content and timestamp"""
        self.content = new_content
        self.updated_at = datetime.now().isoformat()
    
    def update_priority(self, new_priority: str):
        """Update task priority and timestamp"""
        self.priority = new_priority
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary"""
        task = cls(
            id=data["id"],
            content=data["content"],
            status=data.get("status", TaskStatus.PENDING),
            priority=data.get("priority", TaskPriority.MEDIUM),
            metadata=data.get("metadata", {})
        )
        # Preserve timestamps if they exist
        if "created_at" in data:
            task.created_at = data["created_at"]
        if "updated_at" in data:
            task.updated_at = data["updated_at"]
        return task
    
    def get_display_string(self) -> str:
        """Get formatted display string with emoji"""
        emoji = TaskStatus.get_emoji(self.status)
        priority_indicator = TaskPriority.get_indicator(self.priority)
        return f"{emoji} {self.content} ({self.status}) {priority_indicator}"


class TaskManager:
    """Manages a collection of tasks with business rules"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
    
    def add_task(self, task: Task) -> None:
        """Add a new task"""
        if task.id in self.tasks:
            raise ValidationError(f"Task with ID '{task.id}' already exists")
        self.tasks[task.id] = task
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> None:
        """Update an existing task"""
        if task_id not in self.tasks:
            raise ValidationError(f"Task with ID '{task_id}' not found")
        
        task = self.tasks[task_id]
        
        # Update fields if provided
        if "content" in updates:
            task.update_content(updates["content"])
        if "status" in updates:
            task.update_status(updates["status"])
        if "priority" in updates:
            task.update_priority(updates["priority"])
        if "metadata" in updates:
            task.metadata.update(updates["metadata"])
    
    def remove_task(self, task_id: str) -> None:
        """Remove a task"""
        if task_id not in self.tasks:
            raise ValidationError(f"Task with ID '{task_id}' not found")
        del self.tasks[task_id]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        return list(self.tasks.values())
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get tasks by status"""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_tasks_by_priority(self, priority: str) -> List[Task]:
        """Get tasks by priority"""
        return [task for task in self.tasks.values() if task.priority == priority]
    
    def validate_business_rules(self) -> None:
        """Validate business rules"""
        # Rule: Only one task can be in_progress at a time
        in_progress_tasks = self.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        if len(in_progress_tasks) > 1:
            task_ids = [task.id for task in in_progress_tasks]
            raise ValidationError(f"Only one task can be in_progress at a time. Found: {task_ids}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get task summary statistics"""
        all_tasks = self.get_all_tasks()
        return {
            "total": len(all_tasks),
            "pending": len(self.get_tasks_by_status(TaskStatus.PENDING)),
            "in_progress": len(self.get_tasks_by_status(TaskStatus.IN_PROGRESS)),
            "completed": len(self.get_tasks_by_status(TaskStatus.COMPLETED)),
            "cancelled": len(self.get_tasks_by_status(TaskStatus.CANCELLED)),
            "high_priority": len(self.get_tasks_by_priority(TaskPriority.HIGH)),
            "medium_priority": len(self.get_tasks_by_priority(TaskPriority.MEDIUM)),
            "low_priority": len(self.get_tasks_by_priority(TaskPriority.LOW))
        }
    
    def get_display_list(self) -> str:
        """Get formatted display list of all tasks"""
        if not self.tasks:
            return "No tasks found."
        
        # Sort tasks by priority (high first) then by status
        priority_order = {TaskPriority.HIGH: 0, TaskPriority.MEDIUM: 1, TaskPriority.LOW: 2}
        status_order = {TaskStatus.IN_PROGRESS: 0, TaskStatus.PENDING: 1, TaskStatus.COMPLETED: 2, TaskStatus.CANCELLED: 3}
        
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: (priority_order.get(t.priority, 3), status_order.get(t.status, 4), t.created_at)
        )
        
        lines = ["Current tasks:"]
        for task in sorted_tasks:
            lines.append(f"  {task.get_display_string()}")
        
        # Add summary
        summary = self.get_summary()
        lines.append(f"\nSummary: {summary['total']} total | {summary['in_progress']} in progress | {summary['completed']} completed")
        
        return "\n".join(lines)


# Global task manager instance
task_manager = TaskManager()


def validate_task_data(data: Dict[str, Any]) -> None:
    """Validate task data"""
    required_fields = {"id", "content"}
    missing_fields = required_fields - set(data.keys())
    if missing_fields:
        raise ValidationError(f"Missing required fields: {missing_fields}")
    
    # Validate status
    if "status" in data and data["status"] not in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
        raise ValidationError(f"Invalid status: {data['status']}. Must be one of: {list(TaskStatus.EMOJIS.keys())}")
    
    # Validate priority
    if "priority" in data and data["priority"] not in [TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]:
        raise ValidationError(f"Invalid priority: {data['priority']}. Must be one of: {list(TaskPriority.INDICATORS.keys())}")


async def task_write(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Write tasks to the task manager with merge/update capabilities.
    
    Parameters:
        params: Dictionary containing:
            - tasks: List of task dictionaries (required)
            - merge: Whether to merge with existing tasks (optional, defaults to False)
            - clear: Whether to clear existing tasks first (optional, defaults to False)
    
    Returns:
        Dictionary with success status, task count, and display information
    """
    # Validate params structure
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    if "tasks" not in params:
        raise ValidationError("Missing required field: tasks")
    
    tasks_data = params["tasks"]
    if not isinstance(tasks_data, list):
        raise ValidationError("Tasks must be a list")
    
    merge = params.get("merge", False)
    clear = params.get("clear", False)
    
    # Validate each task
    for i, task_data in enumerate(tasks_data):
        if not isinstance(task_data, dict):
            raise ValidationError(f"Task at index {i} must be a dictionary")
        validate_task_data(task_data)
    
    try:
        # Clear existing tasks if requested
        if clear:
            task_manager.tasks.clear()
        
        # Process tasks
        if merge:
            # Merge mode: update existing tasks or add new ones
            for task_data in tasks_data:
                task_id = task_data["id"]
                if task_id in task_manager.tasks:
                    # Update existing task
                    updates = {k: v for k, v in task_data.items() if k != "id"}
                    task_manager.update_task(task_id, updates)
                else:
                    # Add new task
                    task = Task.from_dict(task_data)
                    task_manager.add_task(task)
        else:
            # Replace mode: clear and add all tasks
            task_manager.tasks.clear()
            for task_data in tasks_data:
                task = Task.from_dict(task_data)
                task_manager.add_task(task)
        
        # Validate business rules
        task_manager.validate_business_rules()
        
        # Get summary and display
        summary = task_manager.get_summary()
        display_list = task_manager.get_display_list()
        
        return {
            "success": True,
            "count": len(task_manager.tasks),
            "summary": summary,
            "display": display_list,
            "tasks": [task.to_dict() for task in task_manager.get_all_tasks()]
        }
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to write tasks: {str(e)}")


async def task_read() -> Dict[str, Any]:
    """
    Read all tasks from the task manager.
    
    Returns:
        Dictionary with all tasks and summary information
    """
    try:
        summary = task_manager.get_summary()
        display_list = task_manager.get_display_list()
        
        return {
            "success": True,
            "count": len(task_manager.tasks),
            "summary": summary,
            "display": display_list,
            "tasks": [task.to_dict() for task in task_manager.get_all_tasks()]
        }
        
    except Exception as e:
        raise ValidationError(f"Failed to read tasks: {str(e)}")
