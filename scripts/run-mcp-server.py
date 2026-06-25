#!/usr/bin/env python3
"""Start the mempalace MCP server with broad environment compatibility.

Resolution order (first that works wins):
  1. ``uv run --with mempalace mempalace-mcp`` — zero-install, preferred when uv
     is on PATH. ``mempalace-mcp`` is upstream's canonical console entry point
     (== ``mempalace.mcp_server:main``); uv resolves it inside its managed env on
     Windows, macOS, and Linux alike.
  2. The current Python (``sys.executable``) if ``mempalace`` is importable.
  3. A pre-existing dedicated venv at ``~/.mempalace/.venv`` if it has mempalace.

The fallback paths (2-4) launch ``python -m mempalace.mcp_server`` rather than the
``mempalace-mcp`` script: ``python -m`` needs no PATH/Scripts lookup, so it is the
most portable form when uv is absent. It targets the same entry point.
  4. First-run install, tried in order until one succeeds:
       a. ``pip install --user mempalace`` against the current Python.
       b. Create ``~/.mempalace/.venv`` and ``pip install mempalace`` into it —
          this handles PEP 668 / externally-managed Pythons (e.g. Homebrew 3.12+).
  5. Loud stderr error with install instructions.

Network backends: when ``MEMPALACE_BACKEND`` is ``pgvector`` or ``qdrant``, the uv
path (1) widens ``--with`` to also pull the backend client (``mempalace[pgvector]``
or ``qdrant-client``). The non-uv paths (2-4) use whatever ``mempalace`` is already
installed, so that install must include the backend client itself.

Stdout is reserved for MCP JSON-RPC. All diagnostics go to stderr only.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

VENV_DIR = Path.home() / ".mempalace" / ".venv"
_IS_WIN = os.name == "nt"
_BIN = "Scripts" if _IS_WIN else "bin"
_EXE = ".exe" if _IS_WIN else ""


def _venv_python(venv: Path) -> Path:
    return venv / _BIN / f"python{_EXE}"


def _venv_pip(venv: Path) -> Path:
    return venv / _BIN / f"pip{_EXE}"


def _has_module(python: str, module: str) -> bool:
    try:
        return subprocess.run(
            [python, "-c", f"import {module}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
    except OSError:
        return False


def _venv_has_mempalace(venv: Path) -> bool:
    py = _venv_python(venv)
    return py.exists() and _has_module(str(py), "mempalace")


def _run(argv: list[str]) -> int:
    # subprocess passthrough (not os.execvp) — on Windows execvp is emulated as
    # spawn+exit and drops the MCP client's stdio pipes. Staying in-process as a
    # transparent middleman is reliable everywhere.
    return subprocess.run(
        argv,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    ).returncode


def _try_install() -> str | None:
    """Install mempalace and return a Python command that can run it."""
    # (a) pip --user on the current Python — cheap, works on non-managed envs.
    if _has_module(sys.executable, "pip"):
        rc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "mempalace"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        if rc == 0 and _has_module(sys.executable, "mempalace"):
            return sys.executable

    # (b) Dedicated venv — handles PEP 668 / externally-managed Pythons.
    try:
        VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        subprocess.run(
            [str(_venv_pip(VENV_DIR)), "install", "mempalace"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        if _venv_has_mempalace(VENV_DIR):
            return str(_venv_python(VENV_DIR))
    except (OSError, subprocess.CalledProcessError):
        pass

    return None


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
    backend is selected (via ``MEMPALACE_BACKEND`` or config.json). pgvector ships
    an extra; qdrant has none, so its client is added standalone.
    """
    backend = _select_backend()
    if backend == "pgvector":
        return ["--with", "mempalace[pgvector]"]
    if backend == "qdrant":
        return ["--with", "mempalace", "--with", "qdrant-client"]
    return ["--with", "mempalace"]


def main() -> int:
    forwarded = sys.argv[1:]

    if shutil.which("uv"):
        # Canonical upstream entry point; uv resolves the console script inside
        # its managed env on every platform. --with is widened for network
        # backends (MEMPALACE_BACKEND=pgvector|qdrant) so their client ships too.
        return _run(["uv", "run", *_uv_with_specs(), "mempalace-mcp", *forwarded])

    if _has_module(sys.executable, "mempalace"):
        return _run([sys.executable, "-m", "mempalace.mcp_server", *forwarded])

    if _venv_has_mempalace(VENV_DIR):
        return _run(
            [str(_venv_python(VENV_DIR)), "-m", "mempalace.mcp_server", *forwarded]
        )

    sys.stderr.write(
        "mempalace: first-run install (this may take a minute)...\n"
    )
    installed_python = _try_install()
    if installed_python:
        return _run([installed_python, "-m", "mempalace.mcp_server", *forwarded])

    sys.stderr.write(
        "ERROR: Could not start the mempalace MCP server.\n"
        "Fix: install uv (https://docs.astral.sh/uv/) — recommended — "
        "or run `pip install mempalace` manually.\n"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
