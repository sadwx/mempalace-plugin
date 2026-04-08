#!/bin/bash
# PreCompact hook — emergency save before context window compression.
# Captures everything possible before memories are lost to compaction.
# Silent no-op if mempalace is not installed.

command -v mempalace &>/dev/null || exit 0

mempalace mine --mode convos --extract general "$(pwd)" 2>/dev/null || true
