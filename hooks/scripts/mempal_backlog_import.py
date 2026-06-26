#!/usr/bin/env python3
"""One-time backlog import of existing Claude Code transcripts.

GitHub discussion #1388: Claude Code deletes JSONL transcripts under
``~/.claude/projects/`` after ``cleanupPeriodDays`` (default 30). Conversations
that predate this plugin's auto-save hooks are lost unless they are mined before
that cleanup runs. This SessionStart hook does that once, in the background.

Behaviour:
  * Skip immediately if the sentinel ``~/.mempalace/.claude_imports_done`` exists.
  * Skip WITHOUT writing the sentinel if ``~/.claude/projects`` doesn't exist yet
    — a later session retries.
  * Otherwise spawn a DETACHED background process running
    ``mempalace mine ~/.claude/projects --mode convos --wing claude_imports``
    (the command from discussion #1388), logged to
    ``~/.mempalace/claude_imports.log``, then write the sentinel so it never runs
    again. The hook returns immediately — it never blocks session start.

Silent no-op if the mempalace CLI cannot be located. Never raises.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_IS_WIN = os.name == "nt"
_MEMPAL_DIR = Path.home() / ".mempalace"
_VENV_CMD = (
    _MEMPAL_DIR / ".venv"
    / ("Scripts" if _IS_WIN else "bin")
    / ("mempalace.exe" if _IS_WIN else "mempalace")
)
_SENTINEL = _MEMPAL_DIR / ".claude_imports_done"
_PROJECTS = Path.home() / ".claude" / "projects"
_LOG = _MEMPAL_DIR / "claude_imports.log"


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
    # For a network backend (qdrant/pgvector) prefer ``uv run`` FIRST: it pulls the
    # required client into the run env. A bare PATH/venv ``mempalace`` may lack it,
    # in which case ``mine`` silently writes to a LOCAL chroma palace instead of the
    # shared backend. (mempal_hook.py / run-mcp-server.py are uv-first for this.)
    if _select_backend() in ("qdrant", "pgvector") and shutil.which("uv"):
        return ["uv", "run", *_uv_with_specs(), "mempalace"]
    path_cmd = shutil.which("mempalace")
    if path_cmd:
        return [path_cmd]
    if _VENV_CMD.exists():
        return [str(_VENV_CMD)]
    if shutil.which("uv"):
        return ["uv", "run", *_uv_with_specs(), "mempalace"]
    return None


def main() -> int:
    if _SENTINEL.exists():
        return 0
    if not _PROJECTS.is_dir():
        return 0  # nothing to import yet; a later session will retry
    argv = _resolve_mempalace_argv()
    if not argv:
        return 0
    argv += ["mine", str(_PROJECTS), "--mode", "convos", "--wing", "claude_imports"]

    # Detach so the (potentially long) mine outlives this short-lived hook and
    # never blocks session start.
    if _IS_WIN:
        detach = {
            "creationflags": subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
        }
    else:
        detach = {"start_new_session": True}

    try:
        _MEMPAL_DIR.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "ab") as log:
            subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                **detach,
            )
        _SENTINEL.write_text("done\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
