#!/usr/bin/env python3
"""
Performance Benchmarking Test Suite

This test suite benchmarks MCP server tool performance and compares with expected
built-in tool performance characteristics.
"""

import asyncio
import time
import statistics
from pathlib import Path
from typing import Any, Dict, List, Tuple
import tempfile


class PerformanceBenchmark:
    """Performance benchmarking for MCP server tools"""
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.test_dir = Path(tempfile.mkdtemp(prefix="perf_test_"))
        self.workspace_root = self.test_dir / "workspace"
        self.workspace_root.mkdir()
        self.benchmark_results: Dict[str, List[float]] = {}
        
    def setup_performance_data(self):
        """Set up test data for performance testing"""
        # Create large test files for performance testing
        large_python_file = self.workspace_root / "large_file.py"
        large_content = ""
        for i in range(1000):
            large_content += f"""
def function_{i}():
    '''Function {i} for performance testing'''
    # TODO: Add implementation for function {i}
    # FIXME: Optimize function {i}
    return {i}

class Class{i}:
    def __init__(self):
        self.value = {i}
    
    def method_{i}(self):
        return self.value * {i}
"""
        large_python_file.write_text(large_content)
        
        # Create multiple small files
        for i in range(100):
            small_file = self.workspace_root / f"small_file_{i}.py"
            small_file.write_text(f"# Small file {i}\ndef func_{i}(): return {i}")
        
        # Create nested directory structure
        nested_dir = self.workspace_root / "nested" / "deep" / "structure"
        nested_dir.mkdir(parents=True)
        for i in range(50):
            nested_file = nested_dir / f"nested_file_{i}.py"
            nested_file.write_text(f"# Nested file {i}\nclass Nested{i}: pass")
    
    async def benchmark_tool(self, tool_name: str, args: Dict[str, Any], iterations: int = 5) -> Dict[str, float]:
        """Benchmark a specific tool"""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            try:
                result = await self.mcp_client._call_tool(tool_name, args)
                end_time = time.time()
                
                if result.get("success", False):
                    times.append(end_time - start_time)
                else:
                    print(f"Warning: Tool {tool_name} failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"Error benchmarking {tool_name}: {e}")
        
        if not times:
            return {"error": "No successful runs"}
        
        return {
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "iterations": len(times)
        }
    
    async def benchmark_file_operations(self):
        """Benchmark file operation tools"""
        print("Benchmarking file operations...")
        
        # Benchmark GlobFileSearch
        result = await self.benchmark_tool("GlobFileSearch", {
            "glob_pattern": "**/*.py",
            "target_directory": str(self.workspace_root)
        })
        self.benchmark_results["GlobFileSearch"] = result
        print(f"  GlobFileSearch: {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
        
        # Benchmark SearchReplace
        test_file = self.workspace_root / "test_replace.py"
        test_file.write_text("def test_function():\n    return 'test'\n")
        
        result = await self.benchmark_tool("SearchReplace", {
            "file_path": str(test_file),
            "old_string": "test",
            "new_string": "benchmark"
        })
        self.benchmark_results["SearchReplace"] = result
        print(f"  SearchReplace: {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
        
        # Benchmark MultiEdit
        result = await self.benchmark_tool("MultiEdit", {
            "file_path": str(test_file),
            "edits": [
                {"old_string": "benchmark", "new_string": "performance"},
                {"old_string": "function", "new_string": "method"}
            ]
        })
        self.benchmark_results["MultiEdit"] = result
        print(f"  MultiEdit: {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
    
    async def benchmark_code_analysis(self):
        """Benchmark code analysis tools"""
        print("Benchmarking code analysis...")
        
        # Benchmark ReadLints
        result = await self.benchmark_tool("ReadLints", {
            "paths": [str(self.workspace_root)]
        })
        self.benchmark_results["ReadLints"] = result
        print(f"  ReadLints: {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
        
        # Benchmark CodebaseSearch
        result = await self.benchmark_tool("CodebaseSearch", {
            "query": "function definition",
            "target_directories": [str(self.workspace_root)]
        })
        self.benchmark_results["CodebaseSearch"] = result
        print(f"  CodebaseSearch: {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
        
        # Benchmark Grep
        result = await self.benchmark_tool("Grep", {
            "pattern": "def ",
            "path": str(self.workspace_root)
        })
        self.benchmark_results["Grep"] = result
        print(f"  Grep: {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
    
    async def benchmark_terminal_operations(self):
        """Benchmark terminal operation tools"""
        print("Benchmarking terminal operations...")
        
        # Benchmark RunTerminalCmd
        result = await self.benchmark_tool("RunTerminalCmd", {
            "command": "echo 'Hello World'",
            "working_dir": str(self.workspace_root)
        })
        self.benchmark_results["RunTerminalCmd"] = result
        print(f"  RunTerminalCmd: {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
        
        # Benchmark with environment variables
        result = await self.benchmark_tool("RunTerminalCmd", {
            "command": "echo $TEST_VAR",
            "working_dir": str(self.workspace_root),
            "env_vars": {"TEST_VAR": "test_value"}
        })
        self.benchmark_results["RunTerminalCmd_Env"] = result
        print(f"  RunTerminalCmd (with env): {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
    
    async def benchmark_memory_operations(self):
        """Benchmark memory management tools"""
        print("Benchmarking memory operations...")
        
        # Benchmark UpdateMemory - Create
        result = await self.benchmark_tool("UpdateMemory", {
            "action": "create",
            "key": "perf_test",
            "content": "Performance test memory"
        })
        self.benchmark_results["UpdateMemory_Create"] = result
        print(f"  UpdateMemory (create): {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
        
        # Benchmark UpdateMemory - Get
        result = await self.benchmark_tool("UpdateMemory", {
            "action": "get",
            "key": "perf_test"
        })
        self.benchmark_results["UpdateMemory_Get"] = result
        print(f"  UpdateMemory (get): {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
        
        # Benchmark UpdateMemory - List
        result = await self.benchmark_tool("UpdateMemory", {
            "action": "list"
        })
        self.benchmark_results["UpdateMemory_List"] = result
        print(f"  UpdateMemory (list): {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
        
        # Clean up
        await self.mcp_client._call_tool("UpdateMemory", {
            "action": "delete",
            "key": "perf_test"
        })
    
    async def benchmark_todo_operations(self):
        """Benchmark todo management tools"""
        print("Benchmarking todo operations...")
        
        # Create test todos
        test_todos = [
            {
                "id": f"perf_test_{i}",
                "content": f"Performance test todo {i}",
                "status": "pending",
                "priority": "medium"
            }
            for i in range(10)
        ]
        
        # Benchmark TodoWrite
        result = await self.benchmark_tool("TodoWrite", {"todos": test_todos})
        self.benchmark_results["TodoWrite"] = result
        print(f"  TodoWrite: {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
        
        # Benchmark TodoRead
        result = await self.benchmark_tool("TodoRead", {})
        self.benchmark_results["TodoRead"] = result
        print(f"  TodoRead: {result['mean']:.3f}s ± {result['std_dev']:.3f}s")
    
    async def benchmark_concurrent_operations(self):
        """Benchmark concurrent tool execution"""
        print("Benchmarking concurrent operations...")
        
        # Test concurrent file searches
        start_time = time.time()
        tasks = []
        for i in range(5):
            task = self.mcp_client._call_tool("GlobFileSearch", {
                "glob_pattern": f"*{i}*.py",
                "target_directory": str(self.workspace_root)
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        concurrent_time = end_time - start_time
        self.benchmark_results["Concurrent_GlobFileSearch"] = {
            "total_time": concurrent_time,
            "operations": 5,
            "avg_per_operation": concurrent_time / 5
        }
        
        print(f"  Concurrent GlobFileSearch (5 ops): {concurrent_time:.3f}s total, {concurrent_time/5:.3f}s avg")
        
        # Test concurrent memory operations
        start_time = time.time()
        tasks = []
        for i in range(10):
            task = self.mcp_client._call_tool("UpdateMemory", {
                "action": "create",
                "key": f"concurrent_test_{i}",
                "content": f"Concurrent test {i}"
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        concurrent_time = end_time - start_time
        self.benchmark_results["Concurrent_UpdateMemory"] = {
            "total_time": concurrent_time,
            "operations": 10,
            "avg_per_operation": concurrent_time / 10
        }
        
        print(f"  Concurrent UpdateMemory (10 ops): {concurrent_time:.3f}s total, {concurrent_time/10:.3f}s avg")
        
        # Clean up concurrent test memories
        cleanup_tasks = []
        for i in range(10):
            task = self.mcp_client._call_tool("UpdateMemory", {
                "action": "delete",
                "key": f"concurrent_test_{i}"
            })
            cleanup_tasks.append(task)
        await asyncio.gather(*cleanup_tasks)
    
    def analyze_performance(self):
        """Analyze performance results and compare with expectations"""
        print("\n📊 Performance Analysis")
        print("=" * 50)
        
        # Expected performance thresholds (in seconds)
        expected_thresholds = {
            "GlobFileSearch": 0.1,      # File search should be fast
            "SearchReplace": 0.01,      # Simple text replacement
            "MultiEdit": 0.02,          # Multiple edits
            "ReadLints": 0.5,           # Linting can take time
            "CodebaseSearch": 0.2,      # Semantic search
            "Grep": 0.05,               # Pattern matching
            "RunTerminalCmd": 0.1,      # Command execution
            "UpdateMemory_Create": 0.01, # Memory operations should be fast
            "UpdateMemory_Get": 0.005,   # Memory retrieval
            "UpdateMemory_List": 0.01,   # Memory listing
            "TodoWrite": 0.01,          # Todo operations
            "TodoRead": 0.005,          # Todo reading
        }
        
        performance_issues = []
        
        for tool_name, result in self.benchmark_results.items():
            if "error" in result:
                print(f"❌ {tool_name}: Failed to benchmark")
                continue
            
            mean_time = result["mean"]
            threshold = expected_thresholds.get(tool_name, 1.0)  # Default 1s threshold
            
            if mean_time > threshold:
                performance_issues.append(f"{tool_name}: {mean_time:.3f}s (expected < {threshold}s)")
                print(f"⚠️  {tool_name}: {mean_time:.3f}s ± {result['std_dev']:.3f}s (SLOW)")
            else:
                print(f"✅ {tool_name}: {mean_time:.3f}s ± {result['std_dev']:.3f}s (GOOD)")
        
        # Concurrent performance analysis
        if "Concurrent_GlobFileSearch" in self.benchmark_results:
            concurrent_result = self.benchmark_results["Concurrent_GlobFileSearch"]
            avg_time = concurrent_result["avg_per_operation"]
            single_time = self.benchmark_results.get("GlobFileSearch", {}).get("mean", 0)
            
            if single_time > 0:
                speedup = single_time / avg_time
                print(f"🔄 Concurrent GlobFileSearch speedup: {speedup:.2f}x")
        
        if performance_issues:
            print(f"\n⚠️  Performance Issues Found:")
            for issue in performance_issues:
                print(f"   - {issue}")
        else:
            print(f"\n🎉 All tools meet performance expectations!")
        
        return len(performance_issues) == 0
    
    async def run_all_benchmarks(self):
        """Run all performance benchmarks"""
        print("⚡ Starting Performance Benchmarks")
        print("=" * 50)
        
        try:
            self.setup_performance_data()
            
            await self.benchmark_file_operations()
            await self.benchmark_code_analysis()
            await self.benchmark_terminal_operations()
            await self.benchmark_memory_operations()
            await self.benchmark_todo_operations()
            await self.benchmark_concurrent_operations()
            
            performance_ok = self.analyze_performance()
            
            if performance_ok:
                print("\n🎉 All performance benchmarks passed!")
            else:
                print("\n⚠️  Some performance benchmarks failed!")
            
            return performance_ok
            
        except Exception as e:
            print(f"❌ Performance benchmark failed: {e}")
            raise
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)


async def run_performance_benchmarks(mcp_client):
    """Run performance benchmarks with MCP client"""
    benchmark = PerformanceBenchmark(mcp_client)
    return await benchmark.run_all_benchmarks()


if __name__ == "__main__":
    print("Performance benchmark module loaded")
