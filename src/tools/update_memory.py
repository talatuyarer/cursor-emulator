#!/usr/bin/env python3
"""
Update Memory Tool - Persistent memory management for MCP server.
Provides create, update, delete, and retrieve operations for persistent memories.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict
from uuid import uuid4

from ..state.validators import ValidationError


class Memory(TypedDict):
    """Memory data structure."""
    key: str
    content: str
    created_at: str
    updated_at: str
    access_count: int
    tags: List[str]
    expires_at: Optional[str]
    metadata: Dict[str, Any]


class MemoryResult(TypedDict):
    """Memory operation result."""
    success: bool
    action: str
    key: str
    memory: Optional[Memory]
    message: str
    total_memories: int
    error_code: str
    error_details: str


class MemoryManager:
    """Memory management system with persistent storage."""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.memory_file = workspace_path / ".mcp-memories.json"
        self.memories: Dict[str, Memory] = {}
        self._load_memories()
    
    def _load_memories(self) -> None:
        """Load memories from persistent storage."""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = {k: Memory(v) for k, v in data.items()}
            else:
                self.memories = {}
        except (json.JSONDecodeError, IOError) as e:
            # If file is corrupted, start fresh
            self.memories = {}
            print(f"Warning: Could not load memories: {e}")
    
    def _save_memories(self) -> None:
        """Save memories to persistent storage."""
        try:
            # Ensure directory exists
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with atomic write
            temp_file = self.memory_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_file.replace(self.memory_file)
            
        except IOError as e:
            raise ValidationError(f"Failed to save memories: {e}")
    
    def _cleanup_expired_memories(self) -> None:
        """Remove expired memories."""
        current_time = datetime.now()
        expired_keys = []
        
        for key, memory in self.memories.items():
            if memory.get('expires_at'):
                try:
                    expires_at = datetime.fromisoformat(memory['expires_at'])
                    if current_time > expires_at:
                        expired_keys.append(key)
                except ValueError:
                    # Invalid date format, remove the memory
                    expired_keys.append(key)
        
        for key in expired_keys:
            del self.memories[key]
        
        if expired_keys:
            self._save_memories()
    
    def _generate_key(self, content: str, tags: List[str]) -> str:
        """Generate a unique key for memory content."""
        # Create a hash-based key from content and tags
        import hashlib
        key_data = f"{content}:{':'.join(sorted(tags))}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"memory_{key_hash}"
    
    def create_memory(self, key: Optional[str], content: str, tags: List[str] = None, 
                     expires_at: Optional[str] = None, metadata: Dict[str, Any] = None) -> MemoryResult:
        """Create a new memory."""
        try:
            # Cleanup expired memories first
            self._cleanup_expired_memories()
            
            # Validate inputs
            if not content or not content.strip():
                return MemoryResult(
                    success=False,
                    action="create",
                    key=key or "unknown",
                    memory=None,
                    message="Memory content cannot be empty",
                    total_memories=len(self.memories),
                    error_code="INVALID_CONTENT",
                    error_details="Content must be a non-empty string"
                )
            
            # Generate key if not provided
            if not key:
                key = self._generate_key(content, tags or [])
            
            # Check if key already exists
            if key in self.memories:
                return MemoryResult(
                    success=False,
                    action="create",
                    key=key,
                    memory=None,
                    message=f"Memory with key '{key}' already exists",
                    total_memories=len(self.memories),
                    error_code="KEY_EXISTS",
                    error_details="Use update action to modify existing memory"
                )
            
            # Validate expiration date
            if expires_at:
                try:
                    datetime.fromisoformat(expires_at)
                except ValueError:
                    return MemoryResult(
                        success=False,
                        action="create",
                        key=key,
                        memory=None,
                        message="Invalid expiration date format",
                        total_memories=len(self.memories),
                        error_code="INVALID_DATE",
                        error_details="Expiration date must be in ISO format (YYYY-MM-DDTHH:MM:SS)"
                    )
            
            # Create memory
            current_time = datetime.now().isoformat()
            memory = Memory(
                key=key,
                content=content.strip(),
                created_at=current_time,
                updated_at=current_time,
                access_count=0,
                tags=tags or [],
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            self.memories[key] = memory
            self._save_memories()
            
            return MemoryResult(
                success=True,
                action="create",
                key=key,
                memory=memory,
                message=f"Memory '{key}' created successfully",
                total_memories=len(self.memories),
                error_code="",
                error_details=""
            )
            
        except Exception as e:
            return MemoryResult(
                success=False,
                action="create",
                key=key or "unknown",
                memory=None,
                message=f"Failed to create memory: {str(e)}",
                total_memories=len(self.memories),
                error_code="CREATE_ERROR",
                error_details=str(e)
            )
    
    def update_memory(self, key: str, content: Optional[str] = None, tags: Optional[List[str]] = None,
                     expires_at: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> MemoryResult:
        """Update an existing memory."""
        try:
            # Cleanup expired memories first
            self._cleanup_expired_memories()
            
            # Check if memory exists
            if key not in self.memories:
                return MemoryResult(
                    success=False,
                    action="update",
                    key=key,
                    memory=None,
                    message=f"Memory with key '{key}' not found",
                    total_memories=len(self.memories),
                    error_code="NOT_FOUND",
                    error_details="Memory does not exist"
                )
            
            # Update memory
            memory = self.memories[key]
            current_time = datetime.now().isoformat()
            
            if content is not None:
                if not content.strip():
                    return MemoryResult(
                        success=False,
                        action="update",
                        key=key,
                        memory=None,
                        message="Memory content cannot be empty",
                        total_memories=len(self.memories),
                        error_code="INVALID_CONTENT",
                        error_details="Content must be a non-empty string"
                    )
                memory['content'] = content.strip()
            
            if tags is not None:
                memory['tags'] = tags
            
            if expires_at is not None:
                if expires_at:
                    try:
                        datetime.fromisoformat(expires_at)
                    except ValueError:
                        return MemoryResult(
                            success=False,
                            action="update",
                            key=key,
                            memory=None,
                            message="Invalid expiration date format",
                            total_memories=len(self.memories),
                            error_code="INVALID_DATE",
                            error_details="Expiration date must be in ISO format (YYYY-MM-DDTHH:MM:SS)"
                        )
                memory['expires_at'] = expires_at
            
            if metadata is not None:
                memory['metadata'].update(metadata)
            
            memory['updated_at'] = current_time
            self.memories[key] = memory
            self._save_memories()
            
            return MemoryResult(
                success=True,
                action="update",
                key=key,
                memory=memory,
                message=f"Memory '{key}' updated successfully",
                total_memories=len(self.memories),
                error_code="",
                error_details=""
            )
            
        except Exception as e:
            return MemoryResult(
                success=False,
                action="update",
                key=key,
                memory=None,
                message=f"Failed to update memory: {str(e)}",
                total_memories=len(self.memories),
                error_code="UPDATE_ERROR",
                error_details=str(e)
            )
    
    def delete_memory(self, key: str) -> MemoryResult:
        """Delete a memory."""
        try:
            # Cleanup expired memories first
            self._cleanup_expired_memories()
            
            # Check if memory exists
            if key not in self.memories:
                return MemoryResult(
                    success=False,
                    action="delete",
                    key=key,
                    memory=None,
                    message=f"Memory with key '{key}' not found",
                    total_memories=len(self.memories),
                    error_code="NOT_FOUND",
                    error_details="Memory does not exist"
                )
            
            # Delete memory
            memory = self.memories[key]
            del self.memories[key]
            self._save_memories()
            
            return MemoryResult(
                success=True,
                action="delete",
                key=key,
                memory=memory,
                message=f"Memory '{key}' deleted successfully",
                total_memories=len(self.memories),
                error_code="",
                error_details=""
            )
            
        except Exception as e:
            return MemoryResult(
                success=False,
                action="delete",
                key=key,
                memory=None,
                message=f"Failed to delete memory: {str(e)}",
                total_memories=len(self.memories),
                error_code="DELETE_ERROR",
                error_details=str(e)
            )
    
    def get_memory(self, key: str) -> MemoryResult:
        """Get a specific memory."""
        try:
            # Cleanup expired memories first
            self._cleanup_expired_memories()
            
            # Check if memory exists
            if key not in self.memories:
                return MemoryResult(
                    success=False,
                    action="get",
                    key=key,
                    memory=None,
                    message=f"Memory with key '{key}' not found",
                    total_memories=len(self.memories),
                    error_code="NOT_FOUND",
                    error_details="Memory does not exist"
                )
            
            # Update access count
            memory = self.memories[key]
            memory['access_count'] += 1
            memory['updated_at'] = datetime.now().isoformat()
            self.memories[key] = memory
            self._save_memories()
            
            return MemoryResult(
                success=True,
                action="get",
                key=key,
                memory=memory,
                message=f"Memory '{key}' retrieved successfully",
                total_memories=len(self.memories),
                error_code="",
                error_details=""
            )
            
        except Exception as e:
            return MemoryResult(
                success=False,
                action="get",
                key=key,
                memory=None,
                message=f"Failed to get memory: {str(e)}",
                total_memories=len(self.memories),
                error_code="GET_ERROR",
                error_details=str(e)
            )
    
    def list_memories(self, tags: Optional[List[str]] = None, limit: int = 100) -> Dict[str, Any]:
        """List all memories with optional filtering."""
        try:
            # Cleanup expired memories first
            self._cleanup_expired_memories()
            
            # Filter memories by tags if provided
            filtered_memories = {}
            if tags:
                for key, memory in self.memories.items():
                    if any(tag in memory.get('tags', []) for tag in tags):
                        filtered_memories[key] = memory
            else:
                filtered_memories = self.memories.copy()
            
            # Sort by updated_at (most recent first)
            sorted_memories = dict(sorted(
                filtered_memories.items(),
                key=lambda x: x[1].get('updated_at', ''),
                reverse=True
            ))
            
            # Apply limit
            if limit > 0:
                sorted_memories = dict(list(sorted_memories.items())[:limit])
            
            return {
                "success": True,
                "memories": sorted_memories,
                "total_count": len(sorted_memories),
                "total_memories": len(self.memories),
                "tags_filter": tags,
                "limit": limit
            }
            
        except Exception as e:
            return {
                "success": False,
                "memories": {},
                "total_count": 0,
                "total_memories": len(self.memories),
                "error": str(e)
            }
    
    def search_memories(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search memories by content and tags."""
        try:
            # Cleanup expired memories first
            self._cleanup_expired_memories()
            
            query_lower = query.lower()
            matching_memories = {}
            
            for key, memory in self.memories.items():
                # Search in content
                if query_lower in memory.get('content', '').lower():
                    matching_memories[key] = memory
                    continue
                
                # Search in tags
                if any(query_lower in tag.lower() for tag in memory.get('tags', [])):
                    matching_memories[key] = memory
                    continue
                
                # Search in metadata
                if any(query_lower in str(value).lower() for value in memory.get('metadata', {}).values()):
                    matching_memories[key] = memory
            
            # Sort by relevance (access count and recency)
            sorted_memories = dict(sorted(
                matching_memories.items(),
                key=lambda x: (
                    x[1].get('access_count', 0),
                    x[1].get('updated_at', '')
                ),
                reverse=True
            ))
            
            # Apply limit
            if limit > 0:
                sorted_memories = dict(list(sorted_memories.items())[:limit])
            
            return {
                "success": True,
                "memories": sorted_memories,
                "total_count": len(sorted_memories),
                "total_memories": len(self.memories),
                "query": query,
                "limit": limit
            }
            
        except Exception as e:
            return {
                "success": False,
                "memories": {},
                "total_count": 0,
                "total_memories": len(self.memories),
                "error": str(e)
            }


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(workspace_path: Path) -> MemoryManager:
    """Get or create the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(workspace_path)
    return _memory_manager


def validate_memory_parameters(params: Dict[str, Any]) -> None:
    """Validate memory operation parameters."""
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    action = params.get("action", "").lower()
    if action not in ["create", "update", "delete", "get", "list", "search"]:
        raise ValidationError(f"Invalid action: {action}. Must be one of: create, update, delete, get, list, search")
    
    # Validate required fields based on action
    if action in ["create", "update"]:
        if "content" not in params and action == "create":
            raise ValidationError("Content is required for create action")
    
    if action in ["update", "delete", "get"]:
        if "key" not in params:
            raise ValidationError("Key is required for update, delete, and get actions")
    
    if action == "search":
        if "query" not in params:
            raise ValidationError("Query is required for search action")


async def update_memory(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update memory tool - Create, update, delete, get, list, or search memories.
    
    Parameters:
        action: Action to perform (create, update, delete, get, list, search)
        key: Memory key (required for update, delete, get)
        content: Memory content (required for create, optional for update)
        tags: List of tags (optional)
        expires_at: Expiration date in ISO format (optional)
        metadata: Additional metadata dictionary (optional)
        query: Search query (required for search)
        limit: Maximum number of results (optional, defaults to 100 for list, 20 for search)
    
    Returns:
        Dictionary with operation result and memory data
    """
    try:
        validate_memory_parameters(params)
        
        # Get workspace path
        from ..state.utils import get_workspace_path
        workspace_path = get_workspace_path()
        
        # Get memory manager
        memory_manager = get_memory_manager(workspace_path)
        
        action = params["action"].lower()
        
        if action == "create":
            result = memory_manager.create_memory(
                key=params.get("key"),
                content=params["content"],
                tags=params.get("tags", []),
                expires_at=params.get("expires_at"),
                metadata=params.get("metadata", {})
            )
        
        elif action == "update":
            result = memory_manager.update_memory(
                key=params["key"],
                content=params.get("content"),
                tags=params.get("tags"),
                expires_at=params.get("expires_at"),
                metadata=params.get("metadata")
            )
        
        elif action == "delete":
            result = memory_manager.delete_memory(params["key"])
        
        elif action == "get":
            result = memory_manager.get_memory(params["key"])
        
        elif action == "list":
            result = memory_manager.list_memories(
                tags=params.get("tags"),
                limit=params.get("limit", 100)
            )
        
        elif action == "search":
            result = memory_manager.search_memories(
                query=params["query"],
                limit=params.get("limit", 20)
            )
        
        else:
            raise ValidationError(f"Unknown action: {action}")
        
        return result
        
    except ValidationError as e:
        return {
            "success": False,
            "action": params.get("action", "unknown"),
            "key": params.get("key", "unknown"),
            "memory": None,
            "message": f"Validation error: {str(e)}",
            "total_memories": 0,
            "error_code": "VALIDATION_ERROR",
            "error_details": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "action": params.get("action", "unknown"),
            "key": params.get("key", "unknown"),
            "memory": None,
            "message": f"Memory operation failed: {str(e)}",
            "total_memories": 0,
            "error_code": "OPERATION_ERROR",
            "error_details": str(e)
        }
