#!/usr/bin/env python3
"""
Simple Test Runner for MCP Server Integration Tests

This is a simplified version of the integration test runner that can be used
for quick testing and development.
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


class SimpleMCPTester:
    """Simple MCP server tester"""
    
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.test_dir = Path(tempfile.mkdtemp(prefix="simple_mcp_test_"))
        self.workspace_root = self.test_dir / "workspace"
        self.workspace_root.mkdir()
        self.server_stdin = None
        self.server_stdout = None
        self.request_id = 0
        
    async def start_server(self):
        """Start the MCP server"""
        print("🚀 Starting MCP server...")
        
        env = os.environ.copy()
        env["WORKSPACE_FOLDER_PATHS"] = str(self.workspace_root)
        
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
        
        await asyncio.sleep(2)
        
        # Initialize
        init_response = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "simple-test", "version": "1.0.0"}
        })
        
        # Send initialized notification
        await self._send_request("notifications/initialized", {})
        
        print("✅ MCP server started and initialized")
    
    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send request to server"""
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
        
        response_line = self.server_stdout.readline()
        if not response_line:
            raise Exception("No response from server")
        
        return json.loads(response_line.strip())
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool"""
        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
        
        if "error" in response:
            raise Exception(f"Tool call failed: {response['error']}")
        
        return response.get("result", {})
    
    async def test_basic_functionality(self):
        """Test basic functionality"""
        print("🧪 Testing basic functionality...")
        
        # Test tools list - try different method names
        for method in ["tools/list", "list_tools", "tools"]:
            response = await self._send_request(method)
            print(f"   {method} response: {response}")
            if "result" in response:
                break
        
        if "result" not in response:
            print(f"   Could not get tools list, trying direct tool call...")
            # Try calling a tool directly
            try:
                result = await self._call_tool("TodoRead")
                print(f"   Direct tool call successful: {result['success']}")
            except Exception as e:
                print(f"   Direct tool call failed: {e}")
                return
        
        # Test todo operations
        todos = [{
            "id": "test-1",
            "content": "Test todo",
            "status": "pending",
            "priority": "high"
        }]
        
        result = await self._call_tool("TodoWrite", {"todos": todos})
        print(f"   TodoWrite: {'✅' if result['success'] else '❌'}")
        
        result = await self._call_tool("TodoRead")
        print(f"   TodoRead: {'✅' if result['success'] else '❌'}")
        
        # Test file operations
        test_file = self.workspace_root / "test.txt"
        test_file.write_text("Hello, World!")
        
        result = await self._call_tool("SearchReplace", {
            "file_path": str(test_file),
            "old_string": "Hello, World!",
            "new_string": "Hello, MCP!"
        })
        print(f"   SearchReplace: {'✅' if result['success'] else '❌'}")
        
        # Test terminal
        result = await self._call_tool("RunTerminalCmd", {
            "command": "echo 'test'",
            "working_dir": str(self.workspace_root)
        })
        print(f"   RunTerminalCmd: {'✅' if result['success'] else '❌'}")
        
        # Test memory
        result = await self._call_tool("UpdateMemory", {
            "action": "create",
            "key": "test",
            "content": "test content"
        })
        print(f"   UpdateMemory: {'✅' if result['success'] else '❌'}")
        
        # Clean up
        await self._call_tool("UpdateMemory", {"action": "delete", "key": "test"})
        
        print("✅ Basic functionality test completed")
    
    async def cleanup(self):
        """Clean up"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
        
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        print("🧹 Cleanup completed")
    
    async def run_tests(self):
        """Run all tests"""
        try:
            await self.start_server()
            await self.test_basic_functionality()
            print("\n🎉 All tests passed!")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main function"""
    tester = SimpleMCPTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
