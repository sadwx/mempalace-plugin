#!/bin/bash
# Start the mempalace MCP server using the best available Python.
# Called by .mcp.json — runs as a long-lived process.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure mempalace is installed
bash "$SCRIPT_DIR/ensure-installed.sh" 2>/dev/null

PYTHON_CMD=$(bash "$SCRIPT_DIR/resolve-python.sh" 2>/dev/null)
if [ -z "$PYTHON_CMD" ]; then
  echo "ERROR: No Python found. Cannot start mempalace MCP server." >&2
  exit 1
fi

exec $PYTHON_CMD -m mempalace.mcp_server "$@"
