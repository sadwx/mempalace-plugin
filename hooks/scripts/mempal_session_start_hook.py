#!/usr/bin/env python3
"""SessionStart hook — injects `mempalace wake-up` output as session context.

Claude Code treats any non-JSON text printed by a SessionStart hook as
``additionalContext`` that is injected into the session. We run
``mempalace wake-up`` (which prints L0 identity + L1 essential story,
~170-900 tokens) so the model starts each session with the palace's
wake-up context.

We do *not* delegate to ``mempalace hook run --hook session-start``:
upstream's session-start is a state-init no-op (a mkdir) that emits
``{}``, which would be mistaken for a hook response and suppress the
plain-text context. The state dir upstream needs is created lazily by
the Stop and PreCompact runners anyway.

Silent no-op if the mempalace CLI cannot be located (neither on PATH nor
in the dedicated venv at ``~/.mempalace/.venv``) or if ``wake-up`` fails
(e.g. no palace initialized yet). Never raises — hook failures must not
block Claude Code.

Optional env: ``MEMPALACE_WAKE_UP_WING`` — scope wake-up to a specific
wing (equivalent to ``mempalace wake-up --wing <name>``).
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
    argv = [cmd, "wake-up"]
    wing = os.environ.get("MEMPALACE_WAKE_UP_WING", "").strip()
    if wing:
        argv += ["--wing", wing]
    try:
        proc = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return 0
    if proc.returncode != 0:
        return 0
    text = proc.stdout.decode("utf-8", errors="replace").strip()
    if text:
        sys.stdout.write(text)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
