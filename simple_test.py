#!/usr/bin/env python3
"""
Simple Direct Test for MCP Server Tools

This test directly imports and calls the tool functions without going through
the MCP protocol, which is useful for development and debugging.
"""

import asyncio
import tempfile
from pathlib import Path
import sys
import os

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the tool functions directly
from src.tools.todo_read import todo_read
from src.tools.todo_write import todo_write
from src.tools.run_terminal_cmd import run_terminal_cmd
from src.tools.search_replace import search_replace
from src.tools.glob_file_search import glob_file_search
from src.tools.update_memory import update_memory


async def test_todo_operations():
    """Test todo operations directly"""
    print("🧪 Testing todo operations...")
    
    # Test TodoWrite
    todos = [
        {
            "id": "test-1",
            "content": "Test todo item",
            "status": "pending",
            "priority": "high"
        }
    ]
    
    result = await todo_write({"todos": todos})
    print(f"   TodoWrite: {'✅' if result['success'] else '❌'}")
    
    # Test TodoRead
    result = await todo_read()
    print(f"   TodoRead: {'✅' if result['success'] else '❌'}")
    print(f"   TodoRead result: {result}")
    if 'todos' in result:
        print(f"   Found {len(result['todos'])} todos")
    else:
        print(f"   Result keys: {list(result.keys())}")


async def test_file_operations():
    """Test file operations directly"""
    print("🧪 Testing file operations...")
    
    # Create test file
    test_file = Path(tempfile.mktemp(suffix=".txt"))
    test_file.write_text("Hello, World!")
    
    try:
        # Test SearchReplace
        result = await search_replace({
            "file_path": str(test_file),
            "old_string": "Hello, World!",
            "new_string": "Hello, MCP!"
        })
        print(f"   SearchReplace: {'✅' if result['success'] else '❌'}")
        
        # Verify the change
        content = test_file.read_text()
        if "Hello, MCP!" in content:
            print("   ✅ File content updated correctly")
        else:
            print("   ❌ File content not updated")
        
        # Test GlobFileSearch
        result = await glob_file_search({
            "glob_pattern": "*.txt",
            "target_directory": str(test_file.parent)
        })
        print(f"   GlobFileSearch: {'✅' if result['success'] else '❌'}")
        print(f"   Found {len(result['files'])} files")
        
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


async def test_terminal_operations():
    """Test terminal operations directly"""
    print("🧪 Testing terminal operations...")
    
    # Test RunTerminalCmd
    result = await run_terminal_cmd({
        "command": "echo 'Hello from MCP'",
        "working_dir": str(Path.cwd())
    })
    print(f"   RunTerminalCmd: {'✅' if result['success'] else '❌'}")
    
    if result['success'] and "Hello from MCP" in result['stdout']:
        print("   ✅ Command output captured correctly")
    else:
        print("   ❌ Command output not captured")


async def test_memory_operations():
    """Test memory operations directly"""
    print("🧪 Testing memory operations...")
    
    # Test UpdateMemory - Create
    result = await update_memory({
        "action": "create",
        "key": "test_memory",
        "content": "Test memory content",
        "tags": ["test"]
    })
    print(f"   UpdateMemory (create): {'✅' if result['success'] else '❌'}")
    
    # Test UpdateMemory - Get
    result = await update_memory({
        "action": "get",
        "key": "test_memory"
    })
    print(f"   UpdateMemory (get): {'✅' if result['success'] else '❌'}")
    
    # Test UpdateMemory - List
    result = await update_memory({
        "action": "list"
    })
    print(f"   UpdateMemory (list): {'✅' if result['success'] else '❌'}")
    print(f"   Found {len(result['memories'])} memories")
    
    # Test UpdateMemory - Delete
    result = await update_memory({
        "action": "delete",
        "key": "test_memory"
    })
    print(f"   UpdateMemory (delete): {'✅' if result['success'] else '❌'}")


async def main():
    """Run all direct tests"""
    print("🚀 Starting Direct Tool Tests")
    print("=" * 40)
    
    try:
        await test_todo_operations()
        await test_file_operations()
        await test_terminal_operations()
        await test_memory_operations()
        
        print("=" * 40)
        print("🎉 All direct tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
