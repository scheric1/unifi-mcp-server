# Release Notes: UniFi MCP Server v0.2.5

**Release Date:** May 1, 2026  
**Status:** Stable Release  
**Tests:** 1,232 unit tests passing ✅

---

## 🎯 Overview

**v0.2.5** introduces groundbreaking improvements to the MCP server infrastructure with the addition of **SSE/HTTP transport mode support**, alongside critical API compatibility fixes and enhanced stability for UniFi Cloud EA API integration.

---

## ⭐ Major Highlights

### 1. **SSE/HTTP Transport Mode Support** (NEW) 🚀

The MCP server now supports **Server-Sent Events (SSE) over HTTP**, in addition to the default STDIO transport. This enables:

- **MCP Gateway Integration**: Direct HTTP connectivity for gateway-based AI deployments
- **Long-lived Connections**: SSE allows persistent bidirectional communication channels
- **Cloud-native Architecture**: Deploy as a network service accessible to multiple clients
- **Enhanced Deployment Flexibility**: Run alongside STDIO for multi-client scenarios

**Configuration:**
```bash
UNIFI_TRANSPORT_MODE=sse      # Enable SSE/HTTP mode
UNIFI_HTTP_HOST=0.0.0.0       # Bind address (default: localhost)
UNIFI_HTTP_PORT=8000          # Port binding (default: 8000)
```

See [TRANSPORT.md](docs/TRANSPORT.md) for detailed configuration guide.

---

## 🔧 Technical Improvements

### API Compatibility & Bug Fixes

- **Local API Bug Fixes** (#57): Resolved 7 critical issues affecting UniFi Network 9.x compatibility
  - Fixed firewall policy zone resolution
  - Corrected WLAN band parameter handling
  - Normalized single-object response parsing
  
- **Cloud EA API Hardening**: Enhanced Site Manager endpoint resilience
  - Graceful fallback for unavailable endpoints
  - Improved error handling for edge cases
  - Better compatibility with UniFi Network early-access features

- **Formatting & Code Quality**: Automated formatting pass across entire codebase
  - Consistent code style (Black 26.3.1)
  - Clean import ordering (isort)
  - All linting checks passing (Ruff)

### Dependency Updates

- **Security Updates**: Bumped critical dependencies in the `uv` group
  - fastmcp → latest
  - MCP framework → 1.26.0+
  - cryptography → 46.0.5+
  - httpx → 0.28.1+

---

## 📊 Test Coverage

- **Unit Tests**: 1,232 passing
- **Python Support**: 3.10, 3.11, 3.12, 3.13
- **Coverage**: Maintained high code quality standards
- **Integration Tests**: 14 skipped (require configured environment)

---

## 📝 What's Changed Since v0.2.4

### New Features
- ✨ SSE/HTTP transport mode support for MCP gateway integration
- 🔌 HTTP server bootstrap for alternative deployment architectures

### Bug Fixes
- 🐛 Local API compatibility fixes for UniFi Network 9.x
- 🐛 Cloud EA API endpoint hardening
- 🐛 Firewall policy zone resolution corrections
- 🐛 WLAN band parameter parity improvements

### Quality & Maintenance
- 📋 Automated code formatting pass (Black)
- 🔧 Dependency security updates
- 📚 Documentation improvements
- 🧪 Maintained 1,232 passing tests

---

## 🚀 Installation

### Via pip
```bash
pip install unifi-mcp-server==0.2.5
```

### Via uv (Recommended)
```bash
uv pip install unifi-mcp-server==0.2.5
```

### Via Docker
```bash
docker pull ghcr.io/enuno/unifi-mcp-server:v0.2.5

# Using Docker Compose
services:
  unifi-mcp:
    image: ghcr.io/enuno/unifi-mcp-server:v0.2.5
    ports:
      - "8000:8000"
    environment:
      - UNIFI_API_TYPE=local
      - UNIFI_LOCAL_HOST=192.168.2.1
      - UNIFI_USERNAME=admin
      - UNIFI_PASSWORD=your-password
      - UNIFI_TRANSPORT_MODE=sse  # New: Enable SSE/HTTP mode
```

---

## 🔄 Migration Guide

### From v0.2.4

**No breaking changes.** The v0.2.5 release is fully backward-compatible:

- ✅ Existing STDIO configurations work unchanged
- ✅ All existing tools maintain the same API
- ✅ New SSE mode is optional and disabled by default

To enable the new SSE transport:

```bash
# Start server with SSE/HTTP mode
UNIFI_TRANSPORT_MODE=sse UNIFI_HTTP_PORT=8000 python -m unifi_mcp_server

# Or in your Claude Desktop config:
{
  "mcpServers": {
    "unifi": {
      "command": "python",
      "args": ["-m", "unifi_mcp_server"],
      "env": {
        "UNIFI_TRANSPORT_MODE": "sse",
        "UNIFI_HTTP_PORT": "8000"
      }
    }
  }
}
```

---

## 🐛 Known Issues

None reported. Please [open an issue](https://github.com/enuno/unifi-mcp-server/issues) if you encounter any problems.

---

## 📚 Documentation

- **[README.md](README.md)** - Project overview and quick start
- **[API.md](API.md)** - Complete MCP tool reference (90+ tools)
- **[CLAUDE.md](CLAUDE.md)** - AI agent guidelines and integration
- **[AGENTS.md](AGENTS.md)** - Detailed agent instructions
- **[DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)** - Roadmap and priorities

---

## 🔗 Links

- **Repository**: https://github.com/enuno/unifi-mcp-server
- **PyPI Package**: https://pypi.org/project/unifi-mcp-server
- **Issue Tracker**: https://github.com/enuno/unifi-mcp-server/issues
- **Docker Image**: ghcr.io/enuno/unifi-mcp-server:v0.2.5

---

## ✨ Contributors

Thanks to the community for reporting issues and providing feedback that drove these improvements.

---

**Next Release**: v0.2.6 (Focus: Additional cloud API features and performance optimizations)
