#!/usr/bin/env python3
"""
Main Integration Test Runner

This script runs the complete integration test suite including:
1. MCP server startup and basic functionality
2. All tool functionality tests
3. Built-in tool comparison tests
4. Performance benchmarking
5. Error handling and edge cases
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional
import argparse


class MCPTestRunner:
    """Main test runner for MCP server integration tests"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.server_process: Optional[subprocess.Popen] = None
        self.test_dir = Path(tempfile.mkdtemp(prefix="mcp_integration_"))
        self.workspace_root = self.test_dir / "workspace"
        self.workspace_root.mkdir()
        self.server_stdin = None
        self.server_stdout = None
        self.request_id = 0
        self.test_results = {
            "server_startup": False,
            "tool_functionality": False,
            "builtin_comparison": False,
            "performance": False,
            "error_handling": False
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        if self.verbose or level in ["ERROR", "WARNING"]:
            print(f"[{timestamp}] {level}: {message}")
    
    async def start_mcp_server(self):
        """Start the MCP server process"""
        self.log("Starting MCP server...")
        
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
                "name": "integration-test-runner",
                "version": "1.0.0"
            }
        })
        
        self.log("MCP server started successfully")
    
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
        self.log("Testing server startup...")
        
        try:
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
            missing_tools = [tool for tool in expected_tools if tool not in tool_names]
            
            if missing_tools:
                raise Exception(f"Missing tools: {missing_tools}")
            
            self.log(f"Found {len(tools)} tools", "INFO")
            self.test_results["server_startup"] = True
            return True
            
        except Exception as e:
            self.log(f"Server startup test failed: {e}", "ERROR")
            return False
    
    async def run_basic_functionality_tests(self):
        """Run basic functionality tests for all tools"""
        self.log("Running basic functionality tests...")
        
        try:
            # Test TodoWrite and TodoRead
            test_todos = [
                {
                    "id": "test-1",
                    "content": "Test todo item",
                    "status": "pending",
                    "priority": "high"
                }
            ]
            
            result = await self._call_tool("TodoWrite", {"todos": test_todos})
            assert result["success"] is True
            
            result = await self._call_tool("TodoRead")
            assert result["success"] is True
            assert len(result["todos"]) == 1
            
            # Test file operations
            test_file = self.workspace_root / "test.txt"
            test_file.write_text("Hello, World!")
            
            result = await self._call_tool("SearchReplace", {
                "file_path": str(test_file),
                "old_string": "Hello, World!",
                "new_string": "Hello, MCP!"
            })
            assert result["success"] is True
            
            # Test terminal command
            result = await self._call_tool("RunTerminalCmd", {
                "command": "echo 'test'",
                "working_dir": str(self.workspace_root)
            })
            assert result["success"] is True
            assert "test" in result["stdout"]
            
            # Test memory operations
            result = await self._call_tool("UpdateMemory", {
                "action": "create",
                "key": "test_memory",
                "content": "Test content"
            })
            assert result["success"] is True
            
            result = await self._call_tool("UpdateMemory", {
                "action": "get",
                "key": "test_memory"
            })
            assert result["success"] is True
            
            # Clean up
            await self._call_tool("UpdateMemory", {
                "action": "delete",
                "key": "test_memory"
            })
            
            self.test_results["tool_functionality"] = True
            self.log("Basic functionality tests passed")
            return True
            
        except Exception as e:
            self.log(f"Basic functionality tests failed: {e}", "ERROR")
            return False
    
    async def run_comparison_tests(self):
        """Run built-in tool comparison tests"""
        self.log("Running built-in tool comparison tests...")
        
        try:
            # Import and run comparison tests
            from test_builtin_comparison import run_comparison_tests
            
            # Create a mock MCP client for comparison tests
            class MockMCPClient:
                def __init__(self, test_runner):
                    self.test_runner = test_runner
                
                async def _call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
                    return await self.test_runner._call_tool(tool_name, arguments)
            
            mock_client = MockMCPClient(self)
            await run_comparison_tests(mock_client)
            
            self.test_results["builtin_comparison"] = True
            self.log("Built-in comparison tests passed")
            return True
            
        except Exception as e:
            self.log(f"Built-in comparison tests failed: {e}", "ERROR")
            return False
    
    async def run_performance_tests(self):
        """Run performance benchmark tests"""
        self.log("Running performance benchmark tests...")
        
        try:
            # Import and run performance tests
            from test_performance import run_performance_benchmarks
            
            # Create a mock MCP client for performance tests
            class MockMCPClient:
                def __init__(self, test_runner):
                    self.test_runner = test_runner
                
                async def _call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
                    return await self.test_runner._call_tool(tool_name, arguments)
            
            mock_client = MockMCPClient(self)
            performance_ok = await run_performance_benchmarks(mock_client)
            
            self.test_results["performance"] = performance_ok
            if performance_ok:
                self.log("Performance tests passed")
            else:
                self.log("Performance tests failed", "WARNING")
            return performance_ok
            
        except Exception as e:
            self.log(f"Performance tests failed: {e}", "ERROR")
            return False
    
    async def test_error_handling(self):
        """Test error handling and edge cases"""
        self.log("Testing error handling...")
        
        try:
            # Test invalid file path
            result = await self._call_tool("SearchReplace", {
                "file_path": "/nonexistent/file.txt",
                "old_string": "test",
                "new_string": "test"
            })
            assert result["success"] is False
            
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
            
            self.test_results["error_handling"] = True
            self.log("Error handling tests passed")
            return True
            
        except Exception as e:
            self.log(f"Error handling tests failed: {e}", "ERROR")
            return False
    
    async def cleanup(self):
        """Clean up test environment"""
        self.log("Cleaning up test environment...")
        
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
        
        # Clean up test directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        self.log("Cleanup completed")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🎯 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title():<25} {status}")
        
        print("-" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("Your MCP server is ready for production use!")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} TESTS FAILED")
            print("Please review the failed tests and fix the issues.")
        
        print("=" * 60)
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting MCP Server Integration Test Suite")
        print("=" * 60)
        
        try:
            await self.start_mcp_server()
            
            # Run all test suites
            await self.test_server_startup()
            await self.run_basic_functionality_tests()
            await self.run_comparison_tests()
            await self.run_performance_tests()
            await self.test_error_handling()
            
        except Exception as e:
            self.log(f"Integration test suite failed: {e}", "ERROR")
            raise
        finally:
            await self.cleanup()
            self.print_summary()
        
        return all(self.test_results.values())


async def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run MCP server integration tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only (skip performance)")
    
    args = parser.parse_args()
    
    test_runner = MCPTestRunner(verbose=args.verbose)
    
    if args.quick:
        # Skip performance tests for quick runs
        test_runner.test_results["performance"] = True
    
    success = await test_runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
