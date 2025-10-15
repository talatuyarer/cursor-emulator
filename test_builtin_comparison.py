#!/usr/bin/env python3
"""
Built-in Tool Comparison Test Suite

This test suite compares MCP server tool responses with expected built-in tool behavior
to ensure functional parity and response format consistency.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List
import pytest


class BuiltinComparisonTest:
    """Test suite for comparing MCP tools with built-in tool expectations"""
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.test_dir = Path(tempfile.mkdtemp(prefix="comparison_test_"))
        self.workspace_root = self.test_dir / "workspace"
        self.workspace_root.mkdir()
        
    def setup_comparison_data(self):
        """Set up test data for comparison tests"""
        # Create comprehensive test files
        test_files = {
            "python_file.py": '''
def calculate_fibonacci(n):
    """Calculate nth Fibonacci number"""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class MathUtils:
    def __init__(self):
        self.cache = {}
    
    def factorial(self, n):
        """Calculate factorial of n"""
        if n in self.cache:
            return self.cache[n]
        
        if n <= 1:
            result = 1
        else:
            result = n * self.factorial(n-1)
        
        self.cache[n] = result
        return result

# TODO: Add more mathematical functions
# FIXME: Optimize recursive functions
''',
            "javascript_file.js": '''
function processData(data) {
    // TODO: Add input validation
    const processed = data.map(item => {
        return {
            id: item.id,
            name: item.name.toUpperCase(),
            processed: true
        };
    });
    
    return processed;
}

class DataProcessor {
    constructor() {
        this.cache = new Map();
    }
    
    async fetchData(url) {
        // FIXME: Add error handling
        const response = await fetch(url);
        return response.json();
    }
}
''',
            "markdown_file.md": '''
# Test Project

This is a comprehensive test project.

## Features
- Feature A
- Feature B
- TODO: Add Feature C

## Installation
```bash
npm install
```

## Usage
```javascript
const processor = new DataProcessor();
processor.fetchData('https://api.example.com');
```

## Known Issues
- FIXME: Memory leak in recursive functions
- TODO: Add unit tests
''',
            "config.json": '''
{
    "name": "test-project",
    "version": "1.0.0",
    "dependencies": {
        "express": "^4.18.0",
        "lodash": "^4.17.21"
    },
    "scripts": {
        "start": "node index.js",
        "test": "jest"
    }
}
'''
        }
        
        for filename, content in test_files.items():
            file_path = self.workspace_root / filename
            file_path.write_text(content)
    
    async def compare_todo_management(self):
        """Compare todo management with built-in expectations"""
        print("Comparing todo management...")
        
        # Test data matching built-in todo_write expectations
        test_todos = [
            {
                "id": "task-1",
                "content": "Implement user authentication",
                "status": "pending",
                "priority": "high"
            },
            {
                "id": "task-2",
                "content": "Add input validation",
                "status": "in_progress", 
                "priority": "medium"
            },
            {
                "id": "task-3",
                "content": "Write unit tests",
                "status": "completed",
                "priority": "low"
            }
        ]
        
        # Test TodoWrite
        result = await self.mcp_client._call_tool("TodoWrite", {"todos": test_todos})
        
        # Expected built-in behavior
        expected_keys = ["success", "count", "message"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert result["count"] == 3
        
        # Test TodoRead
        result = await self.mcp_client._call_tool("TodoRead")
        
        # Expected built-in behavior
        expected_keys = ["success", "count", "todos", "summary"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert len(result["todos"]) == 3
        
        # Verify todo structure matches built-in expectations
        for todo in result["todos"]:
            required_fields = ["id", "content", "status", "priority"]
            for field in required_fields:
                assert field in todo, f"Missing todo field: {field}"
        
        print("✅ Todo management comparison passed")
    
    async def compare_file_operations(self):
        """Compare file operations with built-in expectations"""
        print("Comparing file operations...")
        
        test_file = self.workspace_root / "test_edit.txt"
        test_file.write_text("Original content\nLine 2\nLine 3\n")
        
        # Test SearchReplace - should match built-in behavior
        result = await self.mcp_client._call_tool("SearchReplace", {
            "file_path": str(test_file),
            "old_string": "Original content",
            "new_string": "Modified content"
        })
        
        # Expected built-in behavior
        expected_keys = ["success", "replacements_made", "file_path"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert result["replacements_made"] == 1
        
        # Verify file was actually modified
        content = test_file.read_text()
        assert "Modified content" in content
        assert "Original content" not in content
        
        # Test MultiEdit - should match built-in behavior
        result = await self.mcp_client._call_tool("MultiEdit", {
            "file_path": str(test_file),
            "edits": [
                {
                    "old_string": "Line 2",
                    "new_string": "Updated Line 2"
                },
                {
                    "old_string": "Line 3",
                    "new_string": "Updated Line 3"
                }
            ]
        })
        
        # Expected built-in behavior
        expected_keys = ["success", "total_edits", "file_path"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert result["total_edits"] == 2
        
        # Test GlobFileSearch - should match built-in behavior
        result = await self.mcp_client._call_tool("GlobFileSearch", {
            "glob_pattern": "*.py",
            "target_directory": str(self.workspace_root)
        })
        
        # Expected built-in behavior
        expected_keys = ["success", "files", "total_found", "pattern"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert "python_file.py" in result["files"]
        
        print("✅ File operations comparison passed")
    
    async def compare_code_analysis(self):
        """Compare code analysis with built-in expectations"""
        print("Comparing code analysis...")
        
        # Test ReadLints - should match built-in behavior
        result = await self.mcp_client._call_tool("ReadLints", {
            "paths": [str(self.workspace_root)]
        })
        
        # Expected built-in behavior
        expected_keys = ["success", "languages", "total_issues", "issues_by_language"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert isinstance(result["languages"], list)
        assert isinstance(result["total_issues"], int)
        
        # Test CodebaseSearch - should match built-in behavior
        result = await self.mcp_client._call_tool("CodebaseSearch", {
            "query": "function definition",
            "target_directories": [str(self.workspace_root)]
        })
        
        # Expected built-in behavior
        expected_keys = ["success", "results", "total_results", "query"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert isinstance(result["results"], list)
        
        # Test Grep - should match built-in behavior
        result = await self.mcp_client._call_tool("Grep", {
            "pattern": "TODO",
            "path": str(self.workspace_root)
        })
        
        # Expected built-in behavior
        expected_keys = ["success", "matches", "total_matches", "pattern"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert result["total_matches"] > 0  # Should find TODO comments
        
        print("✅ Code analysis comparison passed")
    
    async def compare_terminal_operations(self):
        """Compare terminal operations with built-in expectations"""
        print("Comparing terminal operations...")
        
        # Test RunTerminalCmd - should match built-in behavior
        result = await self.mcp_client._call_tool("RunTerminalCmd", {
            "command": "echo 'Hello World'",
            "working_dir": str(self.workspace_root)
        })
        
        # Expected built-in behavior
        expected_keys = ["success", "stdout", "stderr", "return_code"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert "Hello World" in result["stdout"]
        assert result["return_code"] == 0
        
        # Test with environment variables
        result = await self.mcp_client._call_tool("RunTerminalCmd", {
            "command": "echo $TEST_ENV",
            "working_dir": str(self.workspace_root),
            "env_vars": {"TEST_ENV": "test_value"}
        })
        
        assert result["success"] is True
        assert "test_value" in result["stdout"]
        
        print("✅ Terminal operations comparison passed")
    
    async def compare_web_search(self):
        """Compare web search with built-in expectations"""
        print("Comparing web search...")
        
        # Mock web search to avoid network calls
        from unittest.mock import patch, AsyncMock
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.text.return_value = '''
            <html>
                <head><title>Search Results</title></head>
                <body>
                    <div class="result">
                        <h3><a href="https://example.com">Example Result</a></h3>
                        <p>This is an example search result.</p>
                    </div>
                </body>
            </html>
            '''
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await self.mcp_client._call_tool("WebSearch", {
                "search_term": "python programming",
                "max_results": 5
            })
            
            # Expected built-in behavior
            expected_keys = ["success", "results", "total_results", "search_term"]
            for key in expected_keys:
                assert key in result, f"Missing key: {key}"
            
            assert result["success"] is True
            assert isinstance(result["results"], list)
            assert result["search_term"] == "python programming"
        
        print("✅ Web search comparison passed")
    
    async def compare_memory_management(self):
        """Compare memory management with built-in expectations"""
        print("Comparing memory management...")
        
        # Test UpdateMemory - Create
        result = await self.mcp_client._call_tool("UpdateMemory", {
            "action": "create",
            "key": "test_key",
            "content": "Test memory content",
            "tags": ["test", "comparison"]
        })
        
        # Expected built-in behavior
        expected_keys = ["success", "action", "key", "memory", "message"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert result["action"] == "create"
        assert result["key"] == "test_key"
        
        # Test UpdateMemory - Get
        result = await self.mcp_client._call_tool("UpdateMemory", {
            "action": "get",
            "key": "test_key"
        })
        
        assert result["success"] is True
        assert result["memory"]["content"] == "Test memory content"
        
        # Test UpdateMemory - List
        result = await self.mcp_client._call_tool("UpdateMemory", {
            "action": "list"
        })
        
        expected_keys = ["success", "action", "memories", "message"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        
        assert result["success"] is True
        assert len(result["memories"]) >= 1
        
        # Test UpdateMemory - Search
        result = await self.mcp_client._call_tool("UpdateMemory", {
            "action": "search",
            "query": "test memory"
        })
        
        assert result["success"] is True
        assert len(result["memories"]) >= 1
        
        # Test UpdateMemory - Delete
        result = await self.mcp_client._call_tool("UpdateMemory", {
            "action": "delete",
            "key": "test_key"
        })
        
        assert result["success"] is True
        
        print("✅ Memory management comparison passed")
    
    async def compare_error_handling(self):
        """Compare error handling with built-in expectations"""
        print("Comparing error handling...")
        
        # Test invalid file path
        result = await self.mcp_client._call_tool("SearchReplace", {
            "file_path": "/nonexistent/file.txt",
            "old_string": "test",
            "new_string": "test"
        })
        
        # Expected built-in behavior
        assert result["success"] is False
        assert "error" in result or "error_message" in result
        
        # Test invalid todo data
        result = await self.mcp_client._call_tool("TodoWrite", {
            "todos": [{"invalid": "data"}]
        })
        
        assert result["success"] is False
        
        # Test invalid memory action
        result = await self.mcp_client._call_tool("UpdateMemory", {
            "action": "invalid_action"
        })
        
        assert result["success"] is False
        
        print("✅ Error handling comparison passed")
    
    async def compare_response_formats(self):
        """Compare response formats with built-in expectations"""
        print("Comparing response formats...")
        
        # Test that all tools return consistent response formats
        tools_to_test = [
            ("TodoRead", {}),
            ("GlobFileSearch", {"glob_pattern": "*.py"}),
            ("Grep", {"pattern": "def ", "path": str(self.workspace_root)})
        ]
        
        for tool_name, args in tools_to_test:
            result = await self.mcp_client._call_tool(tool_name, args)
            
            # All tools should have success field
            assert "success" in result, f"Tool {tool_name} missing success field"
            
            # Successful tools should not have error fields
            if result["success"]:
                assert "error" not in result, f"Tool {tool_name} has error field despite success=True"
            else:
                assert "error" in result or "error_message" in result, f"Tool {tool_name} failed but no error field"
        
        print("✅ Response format comparison passed")
    
    async def run_all_comparisons(self):
        """Run all comparison tests"""
        print("🔍 Starting Built-in Tool Comparison Tests")
        print("=" * 50)
        
        try:
            self.setup_comparison_data()
            
            await self.compare_todo_management()
            await self.compare_file_operations()
            await self.compare_code_analysis()
            await self.compare_terminal_operations()
            await self.compare_web_search()
            await self.compare_memory_management()
            await self.compare_error_handling()
            await self.compare_response_formats()
            
            print("=" * 50)
            print("🎉 All comparison tests passed!")
            
        except Exception as e:
            print(f"❌ Comparison test failed: {e}")
            raise
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)


async def run_comparison_tests(mcp_client):
    """Run comparison tests with MCP client"""
    comparison_test = BuiltinComparisonTest(mcp_client)
    await comparison_test.run_all_comparisons()


if __name__ == "__main__":
    # This would be called from the main integration test
    print("Built-in comparison test module loaded")

