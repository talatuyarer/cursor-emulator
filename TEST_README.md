# MCP Server Integration Test Suite

This comprehensive test suite validates that your MCP server tools match the functionality and performance of built-in AI assistant tools.

## 🎯 Test Coverage

### **Core Functionality Tests**
- ✅ **Server Startup**: Validates MCP server initialization and tool discovery
- ✅ **Tool Functionality**: Tests all 19 tools with realistic scenarios
- ✅ **Built-in Comparison**: Compares responses with expected built-in tool behavior
- ✅ **Performance Benchmarking**: Measures execution times and identifies bottlenecks
- ✅ **Error Handling**: Validates proper error responses and edge cases

### **Tool Categories Tested**

**📋 Task Management**
- `TodoRead` / `TodoWrite` - Advanced task management with visual indicators

**💻 Terminal Operations**
- `RunTerminalCmd` - Shell execution with environment variables

**🔍 Code Analysis**
- `ReadLints` - Multi-language linting
- `CodebaseSearch` - Semantic code understanding
- `Grep` - Pattern search

**📝 File Operations**
- `SearchReplace` / `SearchReplaceMultiple` - Exact string replacements
- `MultiEdit` / `MultiEditValidate` - Atomic multi-edit operations
- `DeleteFile` - Safe file deletion
- `GlobFileSearch` - File discovery

**🌐 Web & GitHub**
- `WebSearch` - Real-time web search
- `FetchPullRequest` - GitHub PR data
- `ApplyPatch` - Patch application

**🧠 Memory Management**
- `UpdateMemory` - Persistent memory operations

## 🚀 Quick Start

### **Simple Test (Recommended for Development)**
```bash
python test_runner.py
```

### **Full Integration Test Suite**
```bash
python run_integration_tests.py
```

### **Verbose Output**
```bash
python run_integration_tests.py --verbose
```

### **Quick Test (Skip Performance)**
```bash
python run_integration_tests.py --quick
```

## 📊 Test Results

The test suite provides detailed reporting:

```
🎯 INTEGRATION TEST SUMMARY
============================================================
Server Startup              ✅ PASSED
Tool Functionality          ✅ PASSED
Builtin Comparison          ✅ PASSED
Performance                 ✅ PASSED
Error Handling              ✅ PASSED
------------------------------------------------------------
Total Tests: 5
Passed: 5
Failed: 0
Success Rate: 100.0%

🎉 ALL INTEGRATION TESTS PASSED!
Your MCP server is ready for production use!
```

## 🔧 Test Architecture

### **Test Files Structure**

```
test_integration.py          # Main integration test framework
test_builtin_comparison.py   # Built-in tool comparison tests
test_performance.py          # Performance benchmarking
run_integration_tests.py     # Complete test runner
test_runner.py              # Simple test runner
```

### **Test Components**

**1. MCPIntegrationTest Class**
- Manages MCP server lifecycle
- Handles test environment setup
- Provides tool calling interface

**2. BuiltinComparisonTest Class**
- Compares MCP responses with built-in expectations
- Validates response format consistency
- Tests error handling patterns

**3. PerformanceBenchmark Class**
- Measures execution times
- Tests concurrent operations
- Compares with performance thresholds

## 📈 Performance Expectations

### **Target Performance Thresholds**

| Tool | Expected Time | Description |
|------|---------------|-------------|
| `GlobFileSearch` | < 0.1s | File search operations |
| `SearchReplace` | < 0.01s | Simple text replacement |
| `MultiEdit` | < 0.02s | Multiple edits |
| `ReadLints` | < 0.5s | Code linting |
| `CodebaseSearch` | < 0.2s | Semantic search |
| `Grep` | < 0.05s | Pattern matching |
| `RunTerminalCmd` | < 0.1s | Command execution |
| `UpdateMemory_*` | < 0.01s | Memory operations |
| `TodoWrite/Read` | < 0.01s | Todo operations |

### **Concurrent Performance**
- **5x GlobFileSearch**: Should complete in < 0.5s total
- **10x UpdateMemory**: Should complete in < 0.1s total
- **Speedup Factor**: Concurrent operations should show 2-3x speedup

## 🧪 Test Scenarios

### **File Operations**
- ✅ Create, edit, and delete files
- ✅ Search and replace operations
- ✅ Multi-edit atomic operations
- ✅ Glob pattern file discovery
- ✅ Error handling for invalid paths

### **Code Analysis**
- ✅ Multi-language linting (Python, JavaScript, etc.)
- ✅ Semantic code search
- ✅ Pattern matching with grep
- ✅ TODO/FIXME comment detection

### **Terminal Operations**
- ✅ Command execution
- ✅ Environment variable handling
- ✅ Working directory management
- ✅ Output capture and parsing

### **Memory Management**
- ✅ Create, read, update, delete memories
- ✅ Tag-based organization
- ✅ Search functionality
- ✅ Expiration handling

### **Web & GitHub Integration**
- ✅ Web search with multiple engines
- ✅ GitHub PR data fetching
- ✅ Patch application
- ✅ Error handling for network issues

## 🔍 Built-in Tool Comparison

The test suite ensures your MCP tools match built-in tool behavior:

### **Response Format Consistency**
```json
{
  "success": true,
  "result": {...},
  "message": "Operation completed successfully"
}
```

### **Error Handling Consistency**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid parameters provided"
  }
}
```

### **Tool-Specific Expectations**
- **TodoWrite**: Returns `count` and `message`
- **SearchReplace**: Returns `replacements_made`
- **GlobFileSearch**: Returns `files` array and `total_found`
- **UpdateMemory**: Returns `action`, `key`, and `memory`

## 🚨 Troubleshooting

### **Common Issues**

**Server Won't Start**
```bash
# Check Python path
which python
python --version

# Check dependencies
pip install fastmcp aiohttp beautifulsoup4 lxml

# Check server directly
python -m src.server
```

**Import Errors**
```bash
# Install missing dependencies
pip install pytest pytest-asyncio

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Performance Issues**
```bash
# Run with verbose output to see timing
python run_integration_tests.py --verbose

# Check system resources
top
df -h
```

### **Test Environment**

The test suite creates isolated environments:
- **Temporary directories** for each test run
- **Mock network calls** to avoid external dependencies
- **Automatic cleanup** after test completion
- **Isolated MCP server** instances

## 📝 Adding New Tests

### **Adding a New Tool Test**

1. **Add to test_integration.py**:
```python
async def test_new_tool(self):
    """Test new tool functionality"""
    result = await self._call_tool("NewTool", {"param": "value"})
    assert result["success"] is True
    # Add specific assertions
```

2. **Add to test_builtin_comparison.py**:
```python
async def compare_new_tool(self):
    """Compare new tool with built-in expectations"""
    result = await self.mcp_client._call_tool("NewTool", {"param": "value"})
    # Validate response format matches built-in behavior
```

3. **Add to test_performance.py**:
```python
async def benchmark_new_tool(self):
    """Benchmark new tool performance"""
    result = await self.benchmark_tool("NewTool", {"param": "value"})
    # Add performance expectations
```

### **Test Data Management**

- **Use temporary directories** for file operations
- **Create realistic test data** that matches real-world usage
- **Clean up resources** in finally blocks
- **Mock external dependencies** (network, APIs)

## 🎉 Success Criteria

Your MCP server passes integration tests when:

✅ **All 19 tools** respond correctly to valid inputs  
✅ **Response formats** match built-in tool expectations  
✅ **Performance** meets or exceeds target thresholds  
✅ **Error handling** provides meaningful error messages  
✅ **Concurrent operations** show expected speedup  
✅ **Memory management** persists data correctly  
✅ **File operations** are atomic and safe  

## 📞 Support

If tests fail:

1. **Check the verbose output** for detailed error messages
2. **Review the test logs** for specific failure points
3. **Compare with built-in tool behavior** to identify discrepancies
4. **Check performance metrics** against expected thresholds
5. **Verify error handling** provides appropriate responses

The test suite is designed to help you build a production-ready MCP server that provides the same high-quality experience as built-in AI assistant tools! 🚀
