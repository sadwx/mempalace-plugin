#!/bin/bash
# Ensure mempalace is importable by system Python.
# Only called as fallback when uv is NOT available
# (run-mcp-server.sh handles the uv path directly).

PYTHON_CMD=$(bash "$(dirname "$0")/resolve-python.sh" 2>/dev/null)
if [ -z "$PYTHON_CMD" ]; then
  exit 1
fi

# Already importable — nothing to do
if $PYTHON_CMD -c "import mempalace" &>/dev/null 2>&1; then
  exit 0
fi

# Install into user site-packages (works on externally-managed Pythons)
if command -v pipx &>/dev/null; then
  pipx install mempalace 2>/dev/null && exit 0
fi

if command -v pip3 &>/dev/null; then
  pip3 install --user mempalace 2>/dev/null && exit 0
fi

if command -v pip &>/dev/null; then
  pip install --user mempalace 2>/dev/null && exit 0
fi

echo "ERROR: Could not install mempalace. Install manually: pip install mempalace" >&2
exit 1
