# Claude Code Integration

This folder contains files for integrating WhatsApp MCP with [Claude Code](https://claude.ai/code) (Anthropic's CLI tool).

## Why a Proxy?

Claude Code uses **stdio transport** for MCP servers, while WhatsApp MCP uses **Streamable HTTP**. The proxy bridges this gap.

## Files

- `mcp-stdio-proxy.py` - Python proxy that bridges stdio ↔ HTTP
- `.mcp.json.example` - Example configuration for Claude Code

## Setup

1. **Copy the example config to your project root:**
   ```bash
   cp claude-code/.mcp.json.example .mcp.json
   ```

2. **Edit `.mcp.json`** with your API key (from `.env`)

3. **Install dependency:**
   ```bash
   pip install requests
   ```

4. **Start Claude Code** in the project directory

## Configuration

Environment variables for the proxy:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_API_KEY` | (required) | Your WhatsApp MCP API key from `.env` |
| `MCP_HOST` | `localhost` | MCP server hostname |
| `MCP_PORT` | `8080` | MCP server port |
| `MCP_TIMEOUT` | `30` | Request timeout in seconds |
| `MCP_DEBUG` | `false` | Enable debug logging to `/tmp/mcp-proxy.log` |

## Alternative Implementations

The proxy is written in Python for simplicity. A Go implementation could be added if preferred - contributions welcome!
