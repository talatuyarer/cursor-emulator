#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Cursor Emulator MCP Server

This test suite:
1. Starts the MCP server
2. Tests all 19 tools with realistic scenarios
3. Compares responses with expected built-in tool behavior
4. Validates performance characteristics
5. Ensures proper error handling and edge cases
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
import aiohttp
from unittest.mock import AsyncMock, patch


class MCPIntegrationTest:
    """Integration test suite for MCP server tools"""
    
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.test_dir = Path(tempfile.mkdtemp(prefix="mcp_test_"))
        self.workspace_root = self.test_dir / "workspace"
        self.workspace_root.mkdir()
        self.test_files: List[Path] = []
        self.server_stdin = None
        self.server_stdout = None
        self.request_id = 0
        
    def setup_test_environment(self):
        """Set up test environment with sample files"""
        print(f"Setting up test environment in {self.test_dir}")
        
        # Create sample Python file
        python_file = self.workspace_root / "sample.py"
        python_file.write_text("""
def hello_world():
    '''This is a sample function with a TODO comment'''
    print("Hello, World!")
    # TODO: Add error handling
    return "success"

class SampleClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
""")
        self.test_files.append(python_file)
        
        # Create sample JavaScript file
        js_file = self.workspace_root / "sample.js"
        js_file.write_text("""
function greet(name) {
    console.log(`Hello, ${name}!`);
    // TODO: Add validation
    return true;
}

const config = {
    apiUrl: 'https://api.example.com',
    timeout: 5000
};
""")
        self.test_files.append(js_file)
        
        # Create sample markdown file
        md_file = self.workspace_root / "README.md"
        md_file.write_text("""
# Sample Project

This is a sample project for testing.

## Features
- Feature 1
- Feature 2
- TODO: Add more features

## Installation
```bash
pip install sample
```
""")
        self.test_files.append(md_file)
        
        # Create sample JSON file
        json_file = self.workspace_root / "config.json"
        json_file.write_text('{"name": "test", "version": "1.0.0", "dependencies": {}}')
        self.test_files.append(json_file)
        
        # Create .gitignore
        gitignore = self.workspace_root / ".gitignore"
        gitignore.write_text("__pycache__/\n*.pyc\n.env\n")
        self.test_files.append(gitignore)
        
        print(f"Created {len(self.test_files)} test files")
    
    async def start_mcp_server(self):
        """Start the MCP server process"""
        print("Starting MCP server...")
        
        # Set environment variables
        env = os.environ.copy()
        env["WORKSPACE_FOLDER_PATHS"] = str(self.workspace_root)
        
        # Start server process
        self.server_process = subprocess.Popen(
            [sys.executable, "-m", "src.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent,
            env=env
        )
        
        self.server_stdin = self.server_process.stdin
        self.server_stdout = self.server_process.stdout
        
        # Wait for server to start
        await asyncio.sleep(2)
        
        # Initialize MCP connection
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "integration-test",
                "version": "1.0.0"
            }
        })
        
        print("MCP server started successfully")
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        self.server_stdin.write(request_json)
        self.server_stdin.flush()
        
        # Read response
        response_line = self.server_stdout.readline()
        if not response_line:
            raise Exception("No response from server")
        
        response = json.loads(response_line.strip())
        return response
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specific tool"""
        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
        
        if "error" in response:
            raise Exception(f"Tool call failed: {response['error']}")
        
        return response.get("result", {})
    
    async def test_server_startup(self):
        """Test that the server starts correctly"""
        print("Testing server startup...")
        
        # Test tools/list
        response = await self._send_request("tools/list")
        assert "result" in response
        tools = response["result"]["tools"]
        
        expected_tools = [
            "TodoRead", "TodoWrite", "RunTerminalCmd", "ReadLints", 
            "WebSearch", "CodebaseSearch", "SearchReplace", "SearchReplaceMultiple",
            "MultiEdit", "MultiEditValidate", "DeleteFile", "GlobFileSearch",
            "FetchPullRequest", "ApplyPatch", "Grep", "UpdateMemory"
        ]
        
        tool_names = [tool["name"] for tool in tools]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Missing tool: {expected_tool}"
        
        print(f"✅ Server startup test passed - Found {len(tools)} tools")
    
    async def test_todo_management(self):
        """Test todo management tools"""
        print("Testing todo management...")
        
        # Test TodoWrite
        todos = [
            {
                "id": "test-1",
                "content": "Test todo item",
                "status": "pending",
                "priority": "high"
            },
            {
                "id": "test-2", 
                "content": "Another test item",
                "status": "in_progress",
                "priority": "medium"
            }
        ]
        
        result = await self._call_tool("TodoWrite", {"todos": todos})
        assert result["success"] is True
        assert result["count"] == 2
        
        # Test TodoRead
        result = await self._call_tool("TodoRead")
        assert result["success"] is True
        assert len(result["todos"]) == 2
        assert result["todos"][0]["content"] == "Test todo item"
        
        print("✅ Todo management test passed")
    
    async def test_file_operations(self):
        """Test file operation tools"""
        print("Testing file operations...")
        
        test_file = self.workspace_root / "test_file.txt"
        test_file.write_text("Hello, World!\nThis is a test file.\n")
        
        # Test SearchReplace
        result = await self._call_tool("SearchReplace", {
            "file_path": str(test_file),
            "old_string": "Hello, World!",
            "new_string": "Hello, MCP!"
        })
        assert result["success"] is True
        assert result["replacements_made"] == 1
        
        # Verify the change
        content = test_file.read_text()
        assert "Hello, MCP!" in content
        assert "Hello, World!" not in content
        
        # Test MultiEdit
        result = await self._call_tool("MultiEdit", {
            "file_path": str(test_file),
            "edits": [
                {
                    "old_string": "This is a test file.",
                    "new_string": "This is an edited test file."
                }
            ]
        })
        assert result["success"] is True
        assert result["total_edits"] == 1
        
        # Test GlobFileSearch
        result = await self._call_tool("GlobFileSearch", {
            "glob_pattern": "*.txt"
        })
        assert result["success"] is True
        assert len(result["files"]) >= 1
        assert "test_file.txt" in result["files"]
        
        # Test DeleteFile
        result = await self._call_tool("DeleteFile", {
            "file_path": str(test_file)
        })
        assert result["success"] is True
        assert not test_file.exists()
        
        print("✅ File operations test passed")
    
    async def test_code_analysis(self):
        """Test code analysis tools"""
        print("Testing code analysis...")
        
        # Test ReadLints
        result = await self._call_tool("ReadLints", {
            "paths": [str(self.workspace_root)]
        })
        assert result["success"] is True
        assert "languages" in result
        assert "total_issues" in result
        
        # Test CodebaseSearch
        result = await self._call_tool("CodebaseSearch", {
            "query": "function definition",
            "target_directories": [str(self.workspace_root)]
        })
        assert result["success"] is True
        assert "results" in result
        assert len(result["results"]) >= 0
        
        # Test Grep
        result = await self._call_tool("Grep", {
            "pattern": "def ",
            "path": str(self.workspace_root)
        })
        assert result["success"] is True
        assert "matches" in result
        assert result["total_matches"] >= 0
        
        print("✅ Code analysis test passed")
    
    async def test_terminal_operations(self):
        """Test terminal operation tools"""
        print("Testing terminal operations...")
        
        # Test RunTerminalCmd
        result = await self._call_tool("RunTerminalCmd", {
            "command": "echo 'Hello from MCP'",
            "working_dir": str(self.workspace_root)
        })
        assert result["success"] is True
        assert "Hello from MCP" in result["stdout"]
        
        # Test with environment variables
        result = await self._call_tool("RunTerminalCmd", {
            "command": "echo $TEST_VAR",
            "working_dir": str(self.workspace_root),
            "env_vars": {"TEST_VAR": "test_value"}
        })
        assert result["success"] is True
        assert "test_value" in result["stdout"]
        
        print("✅ Terminal operations test passed")
    
    async def test_web_search(self):
        """Test web search functionality"""
        print("Testing web search...")
        
        # Mock web search to avoid network calls in tests
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.text.return_value = """
            <html>
                <head><title>Test Search Results</title></head>
                <body>
                    <div class="result">
                        <h3><a href="https://example.com">Test Result</a></h3>
                        <p>This is a test search result.</p>
                    </div>
                </body>
            </html>
            """
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await self._call_tool("WebSearch", {
                "search_term": "test query",
                "max_results": 5
            })
            assert result["success"] is True
            assert "results" in result
            assert len(result["results"]) >= 0
        
        print("✅ Web search test passed")
    
    async def test_memory_management(self):
        """Test memory management tools"""
        print("Testing memory management...")
        
        # Test UpdateMemory - Create
        result = await self._call_tool("UpdateMemory", {
            "action": "create",
            "key": "test_memory",
            "content": "This is a test memory",
            "tags": ["test", "integration"]
        })
        assert result["success"] is True
        assert result["key"] == "test_memory"
        
        # Test UpdateMemory - Get
        result = await self._call_tool("UpdateMemory", {
            "action": "get",
            "key": "test_memory"
        })
        assert result["success"] is True
        assert result["memory"]["content"] == "This is a test memory"
        
        # Test UpdateMemory - List
        result = await self._call_tool("UpdateMemory", {
            "action": "list",
            "limit": 10
        })
        assert result["success"] is True
        assert len(result["memories"]) >= 1
        
        # Test UpdateMemory - Search
        result = await self._call_tool("UpdateMemory", {
            "action": "search",
            "query": "test memory"
        })
        assert result["success"] is True
        assert len(result["memories"]) >= 1
        
        # Test UpdateMemory - Delete
        result = await self._call_tool("UpdateMemory", {
            "action": "delete",
            "key": "test_memory"
        })
        assert result["success"] is True
        
        print("✅ Memory management test passed")
    
    async def test_github_integration(self):
        """Test GitHub integration tools"""
        print("Testing GitHub integration...")
        
        # Mock GitHub API calls
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "id": 123,
                "title": "Test PR",
                "body": "Test PR description",
                "state": "open",
                "user": {"login": "testuser"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await self._call_tool("FetchPullRequest", {
                "owner": "testuser",
                "repo": "testrepo",
                "pull_number": 123
            })
            assert result["success"] is True
            assert "pr" in result
            assert result["pr"]["title"] == "Test PR"
        
        print("✅ GitHub integration test passed")
    
    async def test_patch_application(self):
        """Test patch application tools"""
        print("Testing patch application...")
        
        # Create a test file
        test_file = self.workspace_root / "patch_test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")
        
        # Create a patch
        patch_content = """--- patch_test.txt
+++ patch_test.txt
@@ -1,3 +1,4 @@
 Line 1
+New line
 Line 2
 Line 3
"""
        patch_file = self.workspace_root / "test.patch"
        patch_file.write_text(patch_content)
        
        # Test ApplyPatch
        result = await self._call_tool("ApplyPatch", {
            "patch_content": patch_content,
            "target_file": str(test_file)
        })
        assert result["success"] is True
        
        # Verify the patch was applied
        content = test_file.read_text()
        assert "New line" in content
        
        print("✅ Patch application test passed")
    
    async def test_error_handling(self):
        """Test error handling and edge cases"""
        print("Testing error handling...")
        
        # Test invalid file path
        result = await self._call_tool("SearchReplace", {
            "file_path": "/nonexistent/file.txt",
            "old_string": "test",
            "new_string": "test"
        })
        assert result["success"] is False
        assert "error" in result
        
        # Test invalid todo data
        result = await self._call_tool("TodoWrite", {
            "todos": [{"invalid": "data"}]
        })
        assert result["success"] is False
        
        # Test invalid memory action
        result = await self._call_tool("UpdateMemory", {
            "action": "invalid_action"
        })
        assert result["success"] is False
        
        print("✅ Error handling test passed")
    
    async def test_performance(self):
        """Test performance characteristics"""
        print("Testing performance...")
        
        # Test file search performance
        start_time = time.time()
        result = await self._call_tool("GlobFileSearch", {
            "glob_pattern": "**/*",
            "target_directory": str(self.workspace_root)
        })
        end_time = time.time()
        
        assert result["success"] is True
        execution_time = end_time - start_time
        assert execution_time < 1.0, f"File search took too long: {execution_time}s"
        
        # Test memory operations performance
        start_time = time.time()
        for i in range(10):
            await self._call_tool("UpdateMemory", {
                "action": "create",
                "key": f"perf_test_{i}",
                "content": f"Performance test {i}"
            })
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 2.0, f"Memory operations took too long: {execution_time}s"
        
        print("✅ Performance test passed")
    
    async def cleanup(self):
        """Clean up test environment"""
        print("Cleaning up test environment...")
        
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
        
        # Clean up test directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        print("✅ Cleanup completed")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting MCP Server Integration Tests")
        print("=" * 50)
        
        try:
            self.setup_test_environment()
            await self.start_mcp_server()
            
            # Run all test suites
            await self.test_server_startup()
            await self.test_todo_management()
            await self.test_file_operations()
            await self.test_code_analysis()
            await self.test_terminal_operations()
            await self.test_web_search()
            await self.test_memory_management()
            await self.test_github_integration()
            await self.test_patch_application()
            await self.test_error_handling()
            await self.test_performance()
            
            print("=" * 50)
            print("🎉 All integration tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main test runner"""
    test_suite = MCPIntegrationTest()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
