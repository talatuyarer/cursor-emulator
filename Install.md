# Installation Guide: Cursor Emulator - Universal AI Code Assistant

This guide shows you how to integrate **Cursor Emulator** (a comprehensive MCP server with 19 advanced tools) with **Gemini Code Assist** in **IntelliJ IDEA** to transform your AI assistant into a powerful code assistant.

## 🎯 What You'll Get

Your Gemini Code Assist will gain access to **19 powerful development tools** that replicate all the capabilities of Claude Code:

- **📋 Advanced Task Management**: Visual indicators, merge capabilities, and business rules
- **💻 Terminal & Process Management**: Shell execution with background processes and monitoring
- **🔍 Code Analysis & Quality**: Multi-language linting, semantic search, and pattern matching
- **📝 File Operations**: Atomic editing, search/replace, and safe file management
- **🌐 Web & GitHub Integration**: Real-time search, PR fetching, and patch application
- **🧠 Memory & Context Management**: Persistent knowledge storage across sessions
- **⚡ Performance**: Sub-millisecond operations with parallel execution support

## 📋 Prerequisites

### Required Software
- **IntelliJ IDEA** (2024.1 or later)
- **Gemini Code Assist** extension installed and configured
- **Python 3.11+** installed on your system
- **uv** package manager (recommended) or **pip**

### System Requirements
- **macOS**: 10.15+ (Catalina or later)
- **Windows**: Windows 10 version 1903 or later
- **Linux**: Ubuntu 18.04+ or equivalent

### What This Enables
With Cursor Emulator, your Gemini Code Assist will be able to:
- Execute terminal commands and manage background processes
- Perform multi-language code analysis and linting
- Edit files atomically with search/replace operations
- Access web search and GitHub integration
- Maintain persistent memory across development sessions
- Work with multiple tools in parallel for maximum efficiency

## 🚀 Installation Methods

### Method 1: Quick Install (Recommended)

**Step 1: Install uv (if not already installed)**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

**Step 2: Configure MCP in IntelliJ IDEA**

1. **Open IntelliJ IDEA**
2. **Go to Settings** → **Tools** → **Gemini Code Assist**
3. **Find MCP Configuration** section
4. **Add this configuration**:

```json
{
  "mcpServers": {
    "cursor-emulator": {
      "command": "uvx",
      "args": ["cursor-emulator"],
      "env": {
        "WORKSPACE_FOLDER_PATHS": "${workspaceRoot}"
      }
    }
  }
}
```

**Step 3: Restart IntelliJ IDEA**

The system will automatically download and set up the MCP server on first use!

### Method 2: Local Development Install

**Step 1: Clone the Repository**
```bash
git clone https://github.com/your-username/cursor-emulator.git
cd cursor-emulator
```

**Step 2: Install Dependencies**
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

**Step 3: Configure MCP in IntelliJ IDEA**

**Option A: Using uvx (Recommended)**
```json
{
  "mcpServers": {
    "cursor-emulator": {
      "command": "uvx",
      "args": ["."],
      "cwd": "/path/to/cursor-emulator",
      "env": {
        "WORKSPACE_FOLDER_PATHS": "${workspaceRoot}"
      }
    }
  }
}
```

**Option B: Direct Python Execution**
```json
{
  "mcpServers": {
    "cursor-emulator": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/cursor-emulator",
      "env": {
        "WORKSPACE_FOLDER_PATHS": "${workspaceRoot}"
      }
    }
  }
}
```

### Method 3: Docker Install

**Step 1: Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install uv && uv sync

EXPOSE 8000
CMD ["python", "-m", "src.server"]
```

**Step 2: Build and Run**
```bash
docker build -t cursor-emulator .
docker run -p 8000:8000 -v $(pwd):/workspace cursor-emulator
```

**Step 3: Configure MCP**
```json
{
  "mcpServers": {
    "cursor-emulator": {
      "command": "docker",
      "args": ["exec", "-i", "cursor-emulator", "python", "-m", "src.server"],
      "env": {
        "WORKSPACE_FOLDER_PATHS": "${workspaceRoot}"
      }
    }
  }
}
```

## 🔧 Using uvx with Local Repositories

**Yes, `uvx` can install and run MCP servers from local repositories!** This is perfect for development and testing.

### How uvx Works with Local Repos

When you run `uvx .` in a local repository:

1. **Automatic Detection**: `uvx` detects the `pyproject.toml` file
2. **Dependency Resolution**: Downloads and installs all required dependencies
3. **Package Building**: Builds the package from source
4. **Execution**: Runs the package using the entry point defined in `pyproject.toml`

### Benefits of Using uvx Locally

✅ **No Installation Required**: Runs directly from source code  
✅ **Automatic Dependencies**: Handles all dependency management  
✅ **Isolated Environment**: Creates clean virtual environment  
✅ **Development Friendly**: Perfect for testing changes  
✅ **Cross-Platform**: Works on macOS, Linux, and Windows  

### Testing Your Local Setup

```bash
# Navigate to your local repository
cd /path/to/cursor-emulator

# Test with uvx
uvx . --help

# The server should start and show the FastMCP banner
```

### Troubleshooting Local uvx Issues

**Issue**: "Command not found: uvx"
```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Issue**: Import errors or missing functions
```bash
# Clear uv cache to force rebuild
uv cache clean
uvx . --help
```

**Issue**: Dependencies not found
```bash
# Ensure pyproject.toml is properly configured
# Check that all dependencies are listed in [project.dependencies]
```

## ⚙️ Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WORKSPACE_FOLDER_PATHS` | Workspace directory path | Current working directory |
| `MCP_LOG_LEVEL` | Logging level (DEBUG, INFO, WARN, ERROR) | INFO |
| `MCP_TIMEOUT` | Tool execution timeout (seconds) | 30 |

### Advanced Configuration

```json
{
  "mcpServers": {
    "cursor-emulator": {
      "command": "uvx",
      "args": ["cursor-emulator"],
      "env": {
        "WORKSPACE_FOLDER_PATHS": "${workspaceRoot}",
        "MCP_LOG_LEVEL": "DEBUG",
        "MCP_TIMEOUT": "60"
      },
      "timeout": 30000,
      "retries": 3
    }
  }
}
```

## 🧪 Testing Your Installation

### Test 1: Advanced Task Management
1. **Open a project** in IntelliJ IDEA
2. **Start a chat** with Gemini Code Assist
3. **Try this command**:
   ```
   Create a comprehensive development plan for implementing user authentication with these tasks:
   - Set up JWT middleware
   - Create login/signup endpoints
   - Build user profile management
   - Add password reset flow
   - Implement role-based permissions
   ```

### Test 2: Terminal & Process Management
```
Run a background process to compile the project and monitor its status
```

### Test 3: Code Analysis & Quality
```
Analyze the code quality of this project using multi-language linting tools and provide a detailed report
```

### Test 4: File Operations & Search
```
Search for all TODO comments in the codebase, analyze patterns, and create a prioritized summary
```

### Test 5: Web Search & GitHub Integration
```
Search for the latest best practices for Python async programming and find relevant GitHub repositories
```

### Test 6: Memory Management
```
Store information about this project's architecture in persistent memory for future reference
```

## 🔧 Troubleshooting

### Common Issues

**Issue**: "Command not found: uvx"
```bash
# Solution: Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh
# Then restart IntelliJ IDEA
```

**Issue**: "Module not found: fastmcp"
```bash
# Solution: Install dependencies
uv sync
# Or
pip install fastmcp aiohttp beautifulsoup4 lxml
```

**Issue**: "Permission denied" errors
```bash
# Solution: Check file permissions
chmod +x /path/to/your/workspace
# Ensure IntelliJ has proper permissions
```

**Issue**: MCP server not responding
```bash
# Solution: Check logs
# Look in IntelliJ IDEA logs for MCP-related errors
# Try increasing timeout in configuration
```

### Debug Mode

Enable debug logging to troubleshoot issues:

```json
{
  "mcpServers": {
    "cursor-emulator": {
      "command": "uvx",
      "args": ["cursor-emulator"],
      "env": {
        "MCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Manual Server Test

Test the MCP server directly:

```bash
# Using uvx
uvx cursor-emulator

# Or locally
cd /path/to/cursor-emulator
python -m src.server
```

## 📚 Usage Examples

### Development Workflow

**1. Project Analysis & Planning**
```
Analyze this codebase structure, identify patterns, and create a comprehensive development plan with prioritized tasks
```

**2. Feature Development**
```
Implement user authentication. Break this down into manageable tasks, track progress, and manage the implementation workflow.
```

**3. Code Quality & Analysis**
```
Run multi-language linting on all files, perform semantic code analysis, and provide detailed quality reports
```

**4. Bug Investigation & Debugging**
```
Search for error handling patterns, analyze code quality issues, and identify potential problems using advanced search capabilities
```

**5. Research & Documentation**
```
Search the web for best practices, fetch relevant GitHub repositories, and update documentation with current standards
```

### Advanced Features

**Memory & Context Management**
```
Store project architecture, coding patterns, and domain knowledge in persistent memory for cross-session reference
```

**GitHub Integration & Collaboration**
```
Fetch pull request details, analyze code changes, apply patches, and manage collaborative development workflows
```

**Terminal & Process Management**
```
Execute build scripts, run test suites in background, monitor long-running processes, and manage development environments
```

**File Operations & Atomic Editing**
```
Perform complex file operations, atomic multi-file edits, and safe file management with rollback capabilities
```

## 🚀 Performance Tips

### Optimization Settings

```json
{
  "mcpServers": {
    "cursor-emulator": {
      "command": "uvx",
      "args": ["cursor-emulator"],
      "env": {
        "MCP_TIMEOUT": "60",
        "MCP_MAX_WORKERS": "4"
      }
    }
  }
}
```

### Best Practices

1. **Use parallel operations** when possible
2. **Set appropriate limits** for large result sets
3. **Monitor execution times** and optimize tool selection
4. **Use memory management** for frequently accessed information
5. **Leverage background processes** for long-running tasks

## 🔄 Updates and Maintenance

### Updating the MCP Server

```bash
# Using uvx (automatic updates)
uvx --upgrade cursor-emulator

# Or manually
pip install --upgrade cursor-emulator
```

### Checking Version

```bash
uvx cursor-emulator --version
```

### Uninstalling

```bash
# Remove from uvx cache
uvx --uninstall cursor-emulator

# Or remove pip package
pip uninstall cursor-emulator
```

## 📞 Support

### Getting Help

1. **Check the logs** in IntelliJ IDEA for error messages
2. **Review this guide** for common solutions
3. **Test manually** using the command line
4. **Check GitHub issues** for known problems
5. **Create a new issue** if the problem persists

### Useful Commands

```bash
# Check if uv is installed
uv --version

# Check if Python is available
python --version

# Test MCP server directly
uvx cursor-emulator --help

# Check IntelliJ IDEA logs
# Go to Help → Show Log in Explorer/Finder
```

## 🎉 You're All Set!

Once installed, your Gemini Code Assist will be transformed into a powerful code assistant with access to all 19 advanced development tools. Try asking it to:

- **"Analyze this codebase structure and create a comprehensive development plan"**
- **"Run multi-language linting and provide detailed code quality reports"**
- **"Search for security vulnerabilities and performance issues in the codebase"**
- **"Help me implement a new feature with step-by-step task management"**
- **"Execute build scripts and monitor background processes"**
- **"Search the web for best practices and fetch relevant GitHub repositories"**
- **"Store project knowledge in persistent memory for future reference"**

Cursor Emulator will automatically provide:
- **Advanced task management** with visual progress tracking
- **Terminal operations** with background process monitoring
- **Code analysis** with multi-language linting and semantic search
- **File operations** with atomic editing and safe management
- **Web & GitHub integration** for research and collaboration
- **Memory management** for persistent context across sessions

---

**Need help?** Check the [GitHub repository](https://github.com/your-username/cursor-emulator) for more documentation and examples.

**Transform your AI assistant into a powerful code assistant today!** 🚀
