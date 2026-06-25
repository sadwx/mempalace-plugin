#!/usr/bin/env python3
"""PreCompact hook — emergency save before context window compression.

Claude Code stores per-project transcripts under
``~/.claude/projects/<encoded-cwd>/`` where the encoding replaces path
separators with ``-``. That directory — not the project source tree —
is what ``mempalace mine --mode convos`` expects.

Silent no-op if the mempalace CLI cannot be located (neither on PATH nor
in the dedicated venv at ``~/.mempalace/.venv``), or if no transcripts
exist for the current project yet. Never raises — hook failures must
not block Claude Code.
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


def _session_transcripts_dir(cwd: str) -> Path | None:
    base = Path.home() / ".claude" / "projects"
    if not base.is_dir():
        return None
    encoded = cwd.replace("/", "-").replace("\\", "-").replace(":", "")
    candidate = base / encoded
    return candidate if candidate.is_dir() else None


def main() -> int:
    cmd = _resolve_mempalace()
    if not cmd:
        return 0
    transcripts = _session_transcripts_dir(os.getcwd())
    if transcripts is None:
        return 0
    try:
        subprocess.run(
            [cmd, "mine", str(transcripts), "--mode", "convos", "--extract", "general"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=25,
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
