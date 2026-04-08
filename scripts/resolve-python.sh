#!/bin/bash
# Resolve the best available Python command.
# Outputs the command string to stdout. Exits 1 if none found.
# Note: uv is handled directly by run-mcp-server.sh, not here.

VENV_DIR="$HOME/.mempalace/.venv"

# Prefer the dedicated venv if it exists and has mempalace
if [ -x "$VENV_DIR/bin/python" ] && "$VENV_DIR/bin/python" -c "import mempalace" &>/dev/null 2>&1; then
  echo "$VENV_DIR/bin/python"
elif command -v python3 &>/dev/null; then
  echo "python3"
elif command -v python &>/dev/null; then
  echo "python"
else
  echo "ERROR: No Python found. Install Python 3.9+ or uv." >&2
  exit 1
fi
