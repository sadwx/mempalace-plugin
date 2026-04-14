#!/usr/bin/env python3
"""Stop hook — mines cwd for conversation context every ~15 messages.

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
        subprocess.run(
            [cmd, "mine", "--mode", "convos", "--extract", "general", os.getcwd()],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=25,
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
