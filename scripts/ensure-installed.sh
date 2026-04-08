#!/bin/bash
# Ensure mempalace is installed. Tries uv first, falls back to pip.
# Silent success if already installed.

if command -v mempalace &>/dev/null; then
  exit 0
fi

PYTHON_CMD=$(bash "$(dirname "$0")/resolve-python.sh" 2>/dev/null)
if [ -z "$PYTHON_CMD" ]; then
  exit 1
fi

# Check if importable even without CLI on PATH
if $PYTHON_CMD -c "import mempalace" &>/dev/null 2>&1; then
  exit 0
fi

# Install
if command -v uv &>/dev/null; then
  uv pip install mempalace 2>/dev/null && exit 0
fi

if command -v pip3 &>/dev/null; then
  pip3 install mempalace 2>/dev/null && exit 0
fi

if command -v pip &>/dev/null; then
  pip install mempalace 2>/dev/null && exit 0
fi

echo "ERROR: Could not install mempalace. Install manually: pip install mempalace" >&2
exit 1
