# Installation Guide: Gemini Code Assist + IntelliJ IDEA

This guide shows you how to integrate the **Claude Todo MCP Server** (now a comprehensive development toolkit with 19 tools) with **Gemini Code Assist** in **IntelliJ IDEA**.

## 🎯 What You'll Get

Your Gemini Code Assist will gain access to **19 powerful development tools**:

- **📋 Task Management**: Advanced todo tracking with visual indicators
- **💻 Terminal Operations**: Shell execution with background processes
- **🔍 Code Analysis**: Multi-language linting and semantic search
- **📝 File Operations**: Atomic editing, search/replace, file management
- **🌐 Web & GitHub**: Real-time search, PR fetching, patch application
- **🧠 Memory Management**: Persistent context across sessions

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
    "claude-todo-emulator": {
      "command": "uvx",
      "args": ["claude-todo-emulator"],
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
git clone https://github.com/your-username/claude-todo-emulator.git
cd claude-todo-emulator
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
    "claude-todo-emulator": {
      "command": "uvx",
      "args": ["."],
      "cwd": "/path/to/claude-todo-emulator",
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
    "claude-todo-emulator": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/claude-todo-emulator",
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
docker build -t claude-todo-emulator .
docker run -p 8000:8000 -v $(pwd):/workspace claude-todo-emulator
```

**Step 3: Configure MCP**
```json
{
  "mcpServers": {
    "claude-todo-emulator": {
      "command": "docker",
      "args": ["exec", "-i", "claude-todo-emulator", "python", "-m", "src.server"],
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
cd /path/to/claude-todo-emulator

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
    "claude-todo-emulator": {
      "command": "uvx",
      "args": ["claude-todo-emulator"],
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

### Test 1: Basic Todo Management
1. **Open a project** in IntelliJ IDEA
2. **Start a chat** with Gemini Code Assist
3. **Try this command**:
   ```
   Create a todo list for implementing user authentication with these tasks:
   - Set up JWT middleware
   - Create login/signup endpoints
   - Build user profile management
   - Add password reset flow
   - Implement role-based permissions
   ```

### Test 2: Code Analysis
```
Analyze the code quality of this project using the linting tools
```

### Test 3: File Operations
```
Search for all TODO comments in the codebase and create a summary
```

### Test 4: Web Search
```
Search for the latest best practices for Python async programming
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
    "claude-todo-emulator": {
      "command": "uvx",
      "args": ["claude-todo-emulator"],
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
uvx claude-todo-emulator

# Or locally
cd /path/to/claude-todo-emulator
python -m src.server
```

## 📚 Usage Examples

### Development Workflow

**1. Project Setup**
```
Analyze this codebase structure and create a development plan with todos
```

**2. Feature Development**
```
Implement user authentication. Break this down into manageable tasks and track progress.
```

**3. Code Quality**
```
Run linting on all Python files and fix any issues found
```

**4. Bug Investigation**
```
Search for error handling patterns in the codebase and identify potential issues
```

**5. Documentation**
```
Search the web for best practices on API documentation and update our docs accordingly
```

### Advanced Features

**Memory Management**
```
Store information about this project's architecture in memory for future reference
```

**GitHub Integration**
```
Fetch details for pull request #123 and analyze the changes
```

**Background Processes**
```
Start a long-running test suite in the background and monitor its progress
```

## 🚀 Performance Tips

### Optimization Settings

```json
{
  "mcpServers": {
    "claude-todo-emulator": {
      "command": "uvx",
      "args": ["claude-todo-emulator"],
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
uvx --upgrade claude-todo-emulator

# Or manually
pip install --upgrade claude-todo-emulator
```

### Checking Version

```bash
uvx claude-todo-emulator --version
```

### Uninstalling

```bash
# Remove from uvx cache
uvx --uninstall claude-todo-emulator

# Or remove pip package
pip uninstall claude-todo-emulator
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
uvx claude-todo-emulator --help

# Check IntelliJ IDEA logs
# Go to Help → Show Log in Explorer/Finder
```

## 🎉 You're All Set!

Once installed, your Gemini Code Assist will have access to all 19 powerful development tools. Try asking it to:

- **"Create a comprehensive development plan for this project"**
- **"Analyze the code quality and suggest improvements"**
- **"Search for security vulnerabilities in the codebase"**
- **"Help me implement a new feature step by step"**

The MCP server will automatically manage tasks, provide code analysis, and maintain context across your development sessions.

---

**Need help?** Check the [GitHub repository](https://github.com/your-username/claude-todo-emulator) for more documentation and examples.
