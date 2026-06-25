#!/usr/bin/env python3
"""Unified Claude Code hook launcher backed by mempalace's first-class runner.

Wires a Claude Code hook event to ``mempalace hook run --hook <name>
--harness claude-code``. The hook name is the sole CLI argument — one of
``session-start``, ``stop``, ``session-end``, ``precompact``.

The hook JSON arrives on stdin and is forwarded untouched to the runner; the
runner's stdout (harness JSON — e.g. a SessionStart wake-up context payload, or
a Stop decision) is forwarded back to Claude Code. Silent no-op if the mempalace
CLI cannot be located. Never raises — hook failures must not block Claude Code.

CLI resolution order: ``mempalace`` on PATH, then the dedicated venv at
``~/.mempalace/.venv``, then ``uv run --with mempalace`` if uv is available.
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
_VALID_HOOKS = {"session-start", "stop", "session-end", "precompact"}


def _select_backend() -> str:
    """Backend name from ``MEMPALACE_BACKEND``, else the ``backend`` key in
    ~/.mempalace/config.json — so a config-file-only setup (no env vars) still
    provisions the right client. Empty string if unset/unreadable.
    """
    backend = os.environ.get("MEMPALACE_BACKEND", "").strip().lower()
    if backend:
        return backend
    try:
        import json
        cfg = Path.home() / ".mempalace" / "config.json"
        if cfg.is_file():
            return str(json.loads(cfg.read_text(encoding="utf-8")).get("backend", "")).strip().lower()
    except Exception:
        pass
    return ""


def _uv_with_specs() -> list[str]:
    """uv ``--with`` args, widened to pull a network backend's client when a
    backend is selected (via ``MEMPALACE_BACKEND`` or config.json; pgvector ships
    an extra; qdrant does not).
    """
    backend = _select_backend()
    if backend == "pgvector":
        return ["--with", "mempalace[pgvector]"]
    if backend == "qdrant":
        return ["--with", "mempalace", "--with", "qdrant-client"]
    return ["--with", "mempalace"]


def _resolve_mempalace_argv() -> list[str] | None:
    path_cmd = shutil.which("mempalace")
    if path_cmd:
        return [path_cmd]
    if _VENV_CMD.exists():
        return [str(_VENV_CMD)]
    if shutil.which("uv"):
        return ["uv", "run", *_uv_with_specs(), "mempalace"]
    return None


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in _VALID_HOOKS:
        return 0
    hook = sys.argv[1]
    argv = _resolve_mempalace_argv()
    if not argv:
        return 0
    argv += ["hook", "run", "--hook", hook, "--harness", "claude-code"]
    try:
        # Pass stdin (the hook JSON) and stdout (harness response) straight
        # through; keep stderr quiet so it never clutters the transcript.
        subprocess.run(
            argv,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=subprocess.DEVNULL,
            timeout=25,
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
