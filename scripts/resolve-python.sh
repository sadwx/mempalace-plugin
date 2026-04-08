#!/bin/bash
# Resolve the best available Python command.
# Checks: uv run python, python3, python — in that order.
# Outputs the command string to stdout. Exits 1 if none found.

if command -v uv &>/dev/null && uv run python --version &>/dev/null 2>&1; then
  echo "uv run python"
elif command -v python3 &>/dev/null; then
  echo "python3"
elif command -v python &>/dev/null; then
  echo "python"
else
  echo "ERROR: No Python found. Install Python 3.9+ or uv." >&2
  exit 1
fi
