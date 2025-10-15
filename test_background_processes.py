#!/usr/bin/env python3
"""
Test Background Process Management

This test verifies that the background process management functionality
matches the built-in run_terminal_cmd tool capabilities.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the tool functions directly
from src.tools.run_terminal_cmd import (
    run_background_command, 
    get_background_process_status, 
    kill_background_process, 
    list_background_processes
)


async def test_background_process_management():
    """Test background process management functionality"""
    print("🧪 Testing background process management...")
    
    # Test 1: Start a background process
    print("   Starting background process...")
    result = await run_background_command("sleep 10")
    
    if not result["success"]:
        print(f"   ❌ Failed to start background process: {result.get('error')}")
        return False
    
    process_id = result["process_id"]
    print(f"   ✅ Background process started with ID: {process_id}")
    
    # Test 2: Check process status (should be running)
    print("   Checking process status...")
    status_result = await get_background_process_status(process_id)
    
    if not status_result["success"]:
        print(f"   ❌ Failed to get process status: {status_result.get('error')}")
        return False
    
    if status_result["status"] != "running":
        print(f"   ❌ Expected status 'running', got: {status_result['status']}")
        return False
    
    print(f"   ✅ Process status: {status_result['status']}")
    print(f"   ✅ Runtime: {status_result['runtime']:.2f}s")
    
    # Test 3: List all background processes
    print("   Listing all background processes...")
    list_result = await list_background_processes()
    
    if not list_result["success"]:
        print(f"   ❌ Failed to list processes: {list_result.get('error')}")
        return False
    
    if list_result["running_processes"] < 1:
        print(f"   ❌ Expected at least 1 running process, got: {list_result['running_processes']}")
        return False
    
    print(f"   ✅ Found {list_result['total_processes']} total processes")
    print(f"   ✅ {list_result['running_processes']} running, {list_result['completed_processes']} completed")
    
    # Test 4: Kill the background process
    print("   Killing background process...")
    kill_result = await kill_background_process(process_id)
    
    if not kill_result["success"]:
        print(f"   ❌ Failed to kill process: {kill_result.get('error')}")
        return False
    
    if kill_result["status"] != "killed":
        print(f"   ❌ Expected status 'killed', got: {kill_result['status']}")
        return False
    
    print(f"   ✅ Process killed successfully")
    print(f"   ✅ Final runtime: {kill_result['runtime']:.2f}s")
    
    # Test 5: Check status after killing (should be killed)
    print("   Checking status after killing...")
    final_status = await get_background_process_status(process_id)
    
    if not final_status["success"]:
        print(f"   ❌ Failed to get final status: {final_status.get('error')}")
        return False
    
    if final_status["status"] != "killed":
        print(f"   ❌ Expected final status 'killed', got: {final_status['status']}")
        return False
    
    print(f"   ✅ Final status: {final_status['status']}")
    
    # Test 6: Test error handling - invalid process ID
    print("   Testing error handling...")
    try:
        error_result = await get_background_process_status("invalid-id")
        if error_result["success"]:
            print("   ❌ Expected error for invalid process ID")
            return False
        print("   ✅ Error handling works correctly")
    except Exception as e:
        print(f"   ✅ Error handling works correctly: {e}")
    
    return True


async def test_quick_background_process():
    """Test a quick background process that completes naturally"""
    print("🧪 Testing quick background process...")
    
    # Start a quick process
    result = await run_background_command("echo 'Hello from background'")
    
    if not result["success"]:
        print(f"   ❌ Failed to start quick process: {result.get('error')}")
        return False
    
    process_id = result["process_id"]
    print(f"   ✅ Quick process started: {process_id}")
    
    # Wait a bit for it to complete
    await asyncio.sleep(1)
    
    # Check status
    status_result = await get_background_process_status(process_id)
    
    if not status_result["success"]:
        print(f"   ❌ Failed to get status: {status_result.get('error')}")
        return False
    
    print(f"   ✅ Process status: {status_result['status']}")
    
    if status_result["status"] == "completed":
        print(f"   ✅ Process completed naturally")
        print(f"   ✅ Output: {status_result.get('stdout', '').strip()}")
        print(f"   ✅ Return code: {status_result.get('return_code')}")
    else:
        print(f"   ⚠️  Process still running after 1 second")
    
    return True


async def main():
    """Run all background process tests"""
    print("🚀 Starting Background Process Management Tests")
    print("=" * 50)
    
    try:
        success1 = await test_background_process_management()
        success2 = await test_quick_background_process()
        
        print("=" * 50)
        if success1 and success2:
            print("🎉 All background process tests passed!")
            print("✅ Background process management matches built-in tool capabilities!")
        else:
            print("❌ Some background process tests failed!")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

