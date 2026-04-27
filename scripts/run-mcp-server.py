#!/usr/bin/env python3
"""Start the mempalace MCP server with broad environment compatibility.

Resolution order (first that works wins):
  1. ``uv run --with mempalace`` — zero-install, preferred when uv is on PATH.
  2. The current Python (``sys.executable``) if ``mempalace`` is importable.
  3. A pre-existing dedicated venv at ``~/.mempalace-plugin/.venv`` (or the
     legacy ``~/.mempalace/.venv`` path used by plugin <1.0.8) if it has
     mempalace.
  4. First-run install, tried in order until one succeeds:
       a. ``pip install --user mempalace`` against the current Python.
       b. Create ``~/.mempalace-plugin/.venv`` and ``pip install mempalace``
          into it — this handles PEP 668 / externally-managed Pythons
          (e.g. Homebrew 3.12+). Note: kept under our own
          ``~/.mempalace-plugin/`` dir, NOT ``~/.mempalace/``, to avoid
          mingling plugin internals with upstream's user data
          (``config.json``, ``identity.txt``, ``hook_state/`` etc.).
  5. Loud stderr error with install instructions.

Stdout is reserved for MCP JSON-RPC. All diagnostics go to stderr only.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

VENV_DIR = Path.home() / ".mempalace-plugin" / ".venv"
# Legacy path used by plugin <1.0.8. Read-only fallback for already-installed
# users so we don't force a re-install on upgrade.
LEGACY_VENV_DIR = Path.home() / ".mempalace" / ".venv"
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


def main() -> int:
    forwarded = sys.argv[1:]

    if shutil.which("uv"):
        return _run(
            ["uv", "run", "--with", "mempalace",
             "python", "-m", "mempalace.mcp_server", *forwarded]
        )

    if _has_module(sys.executable, "mempalace"):
        return _run([sys.executable, "-m", "mempalace.mcp_server", *forwarded])

    for venv in (VENV_DIR, LEGACY_VENV_DIR):
        if _venv_has_mempalace(venv):
            return _run(
                [str(_venv_python(venv)), "-m", "mempalace.mcp_server", *forwarded]
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
