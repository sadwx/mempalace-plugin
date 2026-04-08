#!/bin/bash
# Stop hook — mines current working directory for conversation context.
# Fires every ~15 messages to capture topics, decisions, and code changes.
# Silent no-op if mempalace is not installed.

command -v mempalace &>/dev/null || exit 0

mempalace mine --mode convos --extract general "$(pwd)" 2>/dev/null || true
