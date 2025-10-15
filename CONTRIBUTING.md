# Contributing to Cursor Emulator

Thank you for your interest in contributing to Cursor Emulator! This document provides guidelines and information for contributors.

## 🎯 Project Vision

Cursor Emulator is a universal AI code assistant that transforms any AI assistant into a powerful code assistant using a local MCP server with 19 advanced tools.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- `uv` package manager (recommended) or `pip`
- Git

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/cursor-emulator.git
   cd cursor-emulator
   ```

2. **Install dependencies**
   ```bash
   uv sync
   # or
   pip install -e .
   ```

3. **Run the server**
   ```bash
   uv run python -m src.server
   # or
   python -m src.server
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run integration tests
python3 run_integration_tests.py

# Run direct tool tests
python3 simple_test.py

# Run performance tests
python3 test_performance.py
```

### Test Coverage

We aim for high test coverage. Run tests with coverage:

```bash
uv run pytest tests/ --cov=src --cov-report=html
```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all functions and classes
- Use modern Python features (3.11+)
- Write comprehensive docstrings

### Tool Development

When creating new MCP tools:

1. **Place in `/src/tools/`** directory
2. **Follow existing patterns** - thin wrappers around state management functions
3. **Use centralized store** - all state operations through `/src/state/store.py`
4. **Include comprehensive error handling** with `ValidationError`
5. **Support parallel execution** for optimal performance
6. **Add to server.py** with proper `@mcp.tool` decorator

### State Management

- Use the singleton pattern established by `store` instance
- All state operations should go through the centralized store
- Follow business rules enforcement in validation

### Type Annotations

Use Python 3.11+ modern type hints:
- `list[T]` instead of `List[T]`
- `dict[K, V]` instead of `Dict[K, V]`
- `str | None` instead of `Optional[str]`

## 🛠️ Tool Categories

### Task Management Tools
- `TodoRead` / `TodoWrite` - Advanced task management with visual indicators

### Terminal & Process Management
- `RunTerminalCmd` - Shell command execution with background processes
- `GetBackgroundProcessStatus` / `KillBackgroundProcess` / `ListBackgroundProcesses` - Process management

### Code Analysis & Quality
- `ReadLints` - Multi-language linting
- `CodebaseSearch` - Semantic code understanding
- `Grep` - Pattern search using Linux grep

### File Operations
- `SearchReplace` / `MultiEdit` - Exact string replacements and atomic multi-edit
- `DeleteFile` - Safe file deletion
- `GlobFileSearch` - File discovery using glob patterns

### Web & GitHub Integration
- `WebSearch` - Real-time web search
- `FetchPullRequest` - GitHub pull request data retrieval
- `ApplyPatch` - Unified diff patch application

### Memory & Context Management
- `UpdateMemory` - Persistent memory management

## 📋 Pull Request Process

### Before Submitting

1. **Run tests** - Ensure all tests pass
2. **Check linting** - Run `uv run ruff check .` and `uv run ruff format .`
3. **Update documentation** - Update relevant documentation
4. **Add tests** - Include tests for new functionality
5. **Update version** - Update version in `pyproject.toml` if needed

### PR Template

Use the provided PR template and include:

- **Description** of changes
- **Type of change** (bug fix, feature, etc.)
- **Tool category** affected
- **Testing** performed
- **Performance impact** assessment
- **Breaking changes** documentation

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Testing** verification
4. **Documentation** review
5. **Approval** from maintainers

## 🐛 Bug Reports

### Before Reporting

1. **Check existing issues** - Search for similar problems
2. **Test latest version** - Ensure you're using the latest release
3. **Gather information** - Collect environment details and error logs

### Bug Report Template

Include:
- **Environment details** (OS, IDE, Python version)
- **MCP configuration**
- **Error logs** and console output
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Tool that failed** (if applicable)

## 🚀 Feature Requests

### Before Requesting

1. **Check existing issues** - Search for similar requests
2. **Consider use cases** - Think about real-world scenarios
3. **Evaluate complexity** - Consider implementation effort

### Feature Request Template

Include:
- **Problem description** - What problem does this solve?
- **Proposed solution** - How should it work?
- **Use cases** - Specific scenarios where this would help
- **Tool category** - Which category does this belong to?
- **Implementation ideas** - Any thoughts on how to implement?

## 🏷️ Issue Labels

We use the following labels:

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements or additions to documentation
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention is needed
- `ide-integration` - IDE-specific integration issues
- `performance` - Performance improvements
- `security` - Security-related issues
- `testing` - Testing improvements
- `tool-category` - Specific tool category labels

## 📚 Documentation

### Documentation Types

- **README.md** - Project overview and quick start
- **Install.md** - Detailed installation guide
- **CURSOR_EMULATOR.md** - Comprehensive vision and capabilities
- **AGENTS.md** - Technical documentation and development guidelines
- **CONTRIBUTING.md** - This file

### Documentation Guidelines

- **Keep it current** - Update documentation with code changes
- **Be comprehensive** - Include all necessary information
- **Use examples** - Provide practical examples
- **Test instructions** - Verify all instructions work

## 🔧 Development Commands

```bash
# Setup development environment
make setup

# Run linting
make lint

# Format code
make format

# Run tests
make test

# Clean cache files
make clean

# Run server directly
uv run python -m src.server
```

## 📞 Getting Help

### Community Support

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Community discussions and Q&A
- **GitHub Wiki** - Additional documentation and guides

### Development Support

- **Code review** - Get feedback on your contributions
- **Pair programming** - Work with maintainers on complex features
- **Mentorship** - Get guidance on contributing

## 🎉 Recognition

Contributors are recognized in:

- **README.md** - Contributor list
- **Release notes** - Feature and fix acknowledgments
- **GitHub contributors** - Automatic contributor recognition

## 📄 License

By contributing to Cursor Emulator, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Cursor Emulator!** 🚀

Together, we're building the future of AI-assisted development.

