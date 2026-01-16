#!/usr/bin/env python3
"""
Stdio-to-HTTP proxy for WhatsApp MCP server.
Bridges Claude Code's stdio transport to the Streamable HTTP transport.

Environment variables:
    MCP_API_KEY: Your WhatsApp MCP API key (required)
    MCP_HOST: MCP server host (default: localhost)
    MCP_PORT: MCP server port (default: 8080)
    MCP_TIMEOUT: Request timeout in seconds (default: 30)
    MCP_DEBUG: Enable debug logging to /tmp/mcp-proxy.log (default: false)
"""

import os
import sys
import json
import requests
from datetime import datetime

# Configuration from environment
API_KEY = os.environ.get("MCP_API_KEY")
HOST = os.environ.get("MCP_HOST", "localhost")
PORT = os.environ.get("MCP_PORT", "8080")
TIMEOUT = int(os.environ.get("MCP_TIMEOUT", "30"))
DEBUG = os.environ.get("MCP_DEBUG", "").lower() in ("1", "true", "yes")

if not API_KEY:
    error = {
        "jsonrpc": "2.0",
        "id": None,
        "error": {
            "code": -32600,
            "message": "MCP_API_KEY environment variable is required"
        }
    }
    print(json.dumps(error), flush=True)
    sys.exit(1)

MCP_URL = f"http://{HOST}:{PORT}/mcp/{API_KEY}"
LOG_FILE = "/tmp/mcp-proxy.log"


def log(msg):
    """Write debug message to log file if debugging is enabled."""
    if DEBUG:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")


log("=== Proxy started ===")
log(f"URL: http://{HOST}:{PORT}/mcp/***")

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "Accept": "application/json"
})

mcp_session_id = None

while True:
    log("Waiting for input...")
    line = sys.stdin.readline()
    log(f"Got line: {len(line) if line else 0} chars")

    if not line:
        log("EOF received, exiting")
        break

    line = line.strip()
    if not line:
        log("Empty line, continuing")
        continue

    # Parse request to get the ID for error responses
    request_id = None
    try:
        req_json = json.loads(line)
        request_id = req_json.get("id")
    except json.JSONDecodeError:
        pass

    log(f"Request (id={request_id}): {line[:200]}...")

    headers = {}
    if mcp_session_id:
        headers["Mcp-Session-Id"] = mcp_session_id
        log(f"Using session: {mcp_session_id}")

    try:
        log("Sending HTTP request...")
        response = session.post(
            MCP_URL,
            data=line.encode('utf-8'),
            headers=headers,
            timeout=TIMEOUT
        )
        log(f"Got response: {response.status_code}")

        # Extract session ID from response headers
        if "Mcp-Session-Id" in response.headers:
            mcp_session_id = response.headers["Mcp-Session-Id"]
            log(f"New session ID: {mcp_session_id}")

        response_text = response.text
        log(f"Response ({len(response_text)} chars): {response_text[:200] if response_text else 'EMPTY'}...")

        # Handle error responses
        if response.status_code >= 400:
            log(f"HTTP ERROR {response.status_code}: {response_text}")
            error = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": f"HTTP {response.status_code}: {response_text}"
                }
            }
            print(json.dumps(error), flush=True)
            log("Error response written to stdout")
            continue

        # Skip empty responses (notifications return 202 with empty body)
        if not response_text:
            log("Skipped empty response (notification ack)")
            continue

        # Write successful response
        print(response_text, flush=True)
        log("Response written to stdout")

    except requests.exceptions.Timeout:
        log("Request timed out")
        error = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": "Request timed out"}
        }
        print(json.dumps(error), flush=True)
    except requests.exceptions.ConnectionError as e:
        log(f"Connection error: {e}")
        error = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": f"Connection error: Is the WhatsApp MCP server running?"}
        }
        print(json.dumps(error), flush=True)
    except Exception as e:
        log(f"Exception: {e}")
        error = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(e)}
        }
        print(json.dumps(error), flush=True)

log("=== Proxy exiting ===")
