#!/usr/bin/env python3
"""PreCompact hook — delegates to upstream's `mempalace hook run --hook precompact`.

Upstream (mempalace >=3.3.0) ships a first-class hook runner that reads
Claude Code's JSON hook payload from stdin and mines the current
session's transcript synchronously so data lands before compaction
proceeds. Per the 3.3.1 changelog, the upstream runner is explicitly
non-blocking on failure/timeout — it will not wedge compaction.

Silent no-op if the mempalace CLI cannot be located (neither on PATH nor
in the dedicated venv at ``~/.mempalace-plugin/.venv``, or its legacy
location at ``~/.mempalace/.venv`` from plugin <1.0.8). Never raises —
hook failures must not block Claude Code.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_IS_WIN = os.name == "nt"
_BIN = "Scripts" if _IS_WIN else "bin"
_EXE = "mempalace.exe" if _IS_WIN else "mempalace"
_VENV_CMD = Path.home() / ".mempalace-plugin" / ".venv" / _BIN / _EXE
_LEGACY_VENV_CMD = Path.home() / ".mempalace" / ".venv" / _BIN / _EXE


def _resolve_mempalace() -> str | None:
    path_cmd = shutil.which("mempalace")
    if path_cmd:
        return path_cmd
    for candidate in (_VENV_CMD, _LEGACY_VENV_CMD):
        if candidate.exists():
            return str(candidate)
    return None


def main() -> int:
    cmd = _resolve_mempalace()
    if not cmd:
        return 0
    try:
        return subprocess.run(
            [cmd, "hook", "run", "--hook", "precompact", "--harness", "claude-code"],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=subprocess.DEVNULL,
            timeout=85,
        ).returncode
    except (subprocess.TimeoutExpired, OSError):
        return 0


if __name__ == "__main__":
    sys.exit(main())
