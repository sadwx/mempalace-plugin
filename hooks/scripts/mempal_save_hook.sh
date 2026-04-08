#!/bin/bash
# Stop hook — mines current working directory for conversation context.
# Fires every ~15 messages to capture topics, decisions, and code changes.
# Silent no-op if mempalace is not installed.

MEMPALACE_CMD=""
if command -v mempalace &>/dev/null; then
  MEMPALACE_CMD="mempalace"
elif [ -x "$HOME/.mempalace/.venv/bin/mempalace" ]; then
  MEMPALACE_CMD="$HOME/.mempalace/.venv/bin/mempalace"
else
  exit 0
fi

$MEMPALACE_CMD mine --mode convos --extract general "$(pwd)" 2>/dev/null || true
