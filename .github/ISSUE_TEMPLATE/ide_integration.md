---
name: IDE Integration Support
about: Request support for a new IDE or improve existing integration
title: '[IDE] '
labels: ide-integration
assignees: ''

---

**IDE Information**
- **IDE Name**: [e.g. IntelliJ IDEA, Cursor, VS Code, Windsurf]
- **Version**: [e.g. 2024.1, 1.0.0]
- **AI Assistant**: [e.g. Gemini Code Assist, Claude, ChatGPT]
- **MCP Support**: [e.g. Native, Extension, Plugin]

**Current Status**
- [ ] IDE has native MCP support
- [ ] IDE has MCP extension/plugin available
- [ ] IDE needs custom integration
- [ ] Integration exists but needs improvement

**Integration Details**
Describe how the IDE currently handles MCP or what integration is needed.

**Configuration Example**
```json
{
  "mcpServers": {
    "cursor-emulator": {
      "command": "uvx",
      "args": ["cursor-emulator"]
    }
  }
}
```

**Testing Results**
- [ ] Installation successful
- [ ] MCP server connects
- [ ] Tools are accessible
- [ ] Commands work as expected
- [ ] Error handling works

**Issues Encountered**
Describe any problems or limitations you've encountered.

**Additional Context**
Add any other context about the IDE integration here.

**Documentation Needs**
- [ ] Installation guide needed
- [ ] Configuration examples needed
- [ ] Troubleshooting guide needed
- [ ] Usage examples needed
