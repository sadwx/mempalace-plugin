#!/usr/bin/env python3
"""SessionStart hook — runs upstream state-init, then injects wake-up as context.

Two phases:

1. Delegate to ``mempalace hook run --hook session-start --harness claude-code``
   with stdin/stdout discarded. Upstream's session-start is currently a
   state-init no-op (creates ``~/.mempalace/hook_state/`` and logs a
   SESSION START marker) that emits ``{}`` to stdout. We discard its
   stdout so the empty JSON response doesn't get picked up by Claude
   Code's hook parser and suppress the ``additionalContext`` path. If
   upstream ever expands session-start, we inherit that behavior
   automatically via this delegate.

2. Run ``mempalace wake-up`` and write its output to our stdout.
   Claude Code treats non-JSON SessionStart stdout as
   ``additionalContext``, so the model starts each session with L0
   identity + L1 essential story (~170-900 tokens) loaded.

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


def _run_upstream_session_start(cmd: str) -> None:
    """Fire-and-forget upstream state-init. Stdout discarded on purpose."""
    try:
        subprocess.run(
            [cmd, "hook", "run", "--hook", "session-start", "--harness", "claude-code"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass


def _emit_wake_up(cmd: str) -> None:
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
        return
    if proc.returncode != 0:
        return
    text = proc.stdout.decode("utf-8", errors="replace").strip()
    if text:
        sys.stdout.write(text)
        sys.stdout.write("\n")


def main() -> int:
    cmd = _resolve_mempalace()
    if not cmd:
        return 0
    _run_upstream_session_start(cmd)
    _emit_wake_up(cmd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
