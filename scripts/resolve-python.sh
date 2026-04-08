#!/bin/bash
# Resolve the best available system Python command.
# Outputs the command string to stdout. Exits 1 if none found.
# Note: uv is handled directly by run-mcp-server.sh, not here.

if command -v python3 &>/dev/null; then
  echo "python3"
elif command -v python &>/dev/null; then
  echo "python"
else
  echo "ERROR: No Python found. Install Python 3.9+ or uv." >&2
  exit 1
fi
