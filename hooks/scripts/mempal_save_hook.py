#!/usr/bin/env python3
"""Stop hook — delegates to upstream's `mempalace hook run --hook stop`.

Upstream (mempalace >=3.3.0) ships a first-class hook runner that reads
Claude Code's JSON hook payload from stdin, counts human messages since
the last save, and emits a ``{"decision": "block", ...}`` directive every
SAVE_INTERVAL messages prompting the model to persist context. It also
guards against infinite save loops via ``stop_hook_active`` and spawns
auto-ingest in the background when ``MEMPAL_DIR`` is set.

Silent no-op if the mempalace CLI cannot be located (neither on PATH nor
in the dedicated venv at ``~/.mempalace/.venv``). Never raises — hook
failures must not block Claude Code.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_IS_WIN = os.name == "nt"
_VENV_CMD = (
    Path.home() / ".mempalace" / ".venv"
    / ("Scripts" if _IS_WIN else "bin")
    / ("mempalace.exe" if _IS_WIN else "mempalace")
)


def _resolve_mempalace() -> str | None:
    path_cmd = shutil.which("mempalace")
    if path_cmd:
        return path_cmd
    if _VENV_CMD.exists():
        return str(_VENV_CMD)
    return None


def main() -> int:
    cmd = _resolve_mempalace()
    if not cmd:
        return 0
    try:
        return subprocess.run(
            [cmd, "hook", "run", "--hook", "stop", "--harness", "claude-code"],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=subprocess.DEVNULL,
            timeout=25,
        ).returncode
    except (subprocess.TimeoutExpired, OSError):
        return 0


if __name__ == "__main__":
    sys.exit(main())
