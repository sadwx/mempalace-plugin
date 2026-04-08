#!/bin/bash
# Ensure mempalace is importable by system Python.
# Only called as fallback when uv is NOT available
# (run-mcp-server.sh handles the uv path directly).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$HOME/.mempalace/.venv"

PYTHON_CMD=$(bash "$SCRIPT_DIR/resolve-python.sh" 2>/dev/null)
if [ -z "$PYTHON_CMD" ]; then
  exit 1
fi

# Already importable — nothing to do
if $PYTHON_CMD -c "import mempalace" &>/dev/null 2>&1; then
  exit 0
fi

# Try pipx first (isolated, preferred)
if command -v pipx &>/dev/null; then
  pipx install mempalace 2>/dev/null && exit 0
fi

# Try pip --user (works on non-externally-managed Pythons)
if command -v pip3 &>/dev/null; then
  pip3 install --user mempalace 2>/dev/null && exit 0
fi
if command -v pip &>/dev/null; then
  pip install --user mempalace 2>/dev/null && exit 0
fi

# Fallback: create a dedicated venv (handles PEP 668 / externally-managed)
if $PYTHON_CMD -c "import venv" &>/dev/null 2>&1; then
  mkdir -p "$(dirname "$VENV_DIR")"
  $PYTHON_CMD -m venv "$VENV_DIR" 2>/dev/null
  "$VENV_DIR/bin/pip" install mempalace 2>/dev/null && exit 0
fi

echo "ERROR: Could not install mempalace. Install manually: pip install mempalace" >&2
exit 1
