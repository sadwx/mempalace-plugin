# mempalace plugin for Claude Code

![version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fsadwx%2Fmempalace-plugin%2Fmaster%2F.claude-plugin%2Fplugin.json&query=%24.version&label=version)

Zero-effort setup and integration of [mempalace](https://github.com/MemPalace/mempalace) — a local AI memory system (ChromaDB + SQLite) — into Claude Code.

## What it does

**On install (automatic):**
- MCP server auto-registers, exposing 35 mempalace tools (search, mining, drawers, knowledge graph, tunnels, agent diary, and more)
- SessionStart hook injects wake-up context and — once, in the background — imports your existing Claude Code transcripts before Claude Code's `cleanupPeriodDays` (default 30) deletes them ([discussion #1388](https://github.com/MemPalace/mempalace/discussions/1388))
- Stop hook auto-saves conversation context
- PreCompact hook emergency-saves before context window compression
- SessionEnd hook runs a final mine when the session ends
- All four run mempalace's first-class hook runner (`mempalace hook run --harness claude-code`)

**On `/mempalace` (per-project):**
- Installs mempalace package if needed (detects uv/python3/python)
- Initializes palace for the current project
- Auto-detects wing name, rooms, and keywords from project context
- Creates identity file from git config
- Mines the project to seed the palace
- Reports a single summary when done

## Installation

```bash
# Add this repo as a marketplace
claude plugin marketplace add https://github.com/sadwx/mempalace-plugin

# Install globally
claude plugin install mempalace@mempalace-plugin --scope user
```

Then restart Claude Code or run `/reload-plugins`.

## Requirements

> **Tested against mempalace 3.5.0** (35 MCP tools). The launcher installs the latest `mempalace` release from PyPI unpinned (`uv run --with mempalace …`), so newer versions are picked up automatically — 3.5.0 is just the release this plugin was last verified against.

- **`uv` (recommended)** — install from [docs.astral.sh/uv](https://docs.astral.sh/uv/). Zero-install startup: the launcher runs `uv run --with mempalace …` and uv provisions everything, identically on Windows, macOS, and Linux. Nothing else needed.
- **…or Python 3.10+ on `PATH`** with the `mempalace` package installed (`pip install mempalace`). The launcher detects `python3` first, then `python`, so either name works.
  - **Windows:** install Python from [python.org](https://www.python.org/downloads/) or the Microsoft Store — or just use `uv`.
  - **macOS:** `brew install uv` (or `brew install python`).
  - **Debian / Ubuntu:** `python3` is usually preinstalled; otherwise `sudo apt install python3` — or use `uv`.
- **Claude Code** (provides the `node` runtime the launcher uses to stay shell-agnostic).

> **No `bash` required.** The plugin no longer shells out through `bash`, so Windows users don't need Git Bash or WSL. This sidesteps a Windows `CreateProcess` issue where `C:\Windows\System32\bash.exe` (the WSL launcher) is resolved before Git Bash on `PATH` and fails on Windows-style script paths.

## Usage

```
/mempalace              # Set up mempalace for current project
```

Safe to re-run — skips completed steps. Run in any project directory to add a new wing.

### After setup

mempalace works automatically via MCP tools in Claude sessions. For manual use:

| Command | Purpose |
|---|---|
| `mempalace search "query"` | Semantic search across memories |
| `mempalace search "query" --wing name` | Search within a specific wing |
| `mempalace mine <path>` | Ingest code/docs |
| `mempalace mine <path> --mode convos` | Ingest conversation exports |
| `mempalace wake-up` | ~600–900 tokens of wake-up context (L0 + L1) for session start |
| `mempalace status` | Palace overview |

## Components

| Component | File | Purpose |
|-----------|------|---------|
| MCP | `.mcp.json` | Auto-registers mempalace MCP server |
| Skill | `skills/mempalace/SKILL.md` | `/mempalace` setup command |
| Hook | `hooks/scripts/mempal_hook.py` | Runs `mempalace hook run` for SessionStart / Stop / SessionEnd / PreCompact |
| Hook | `hooks/scripts/mempal_backlog_import.py` | One-time background import of existing transcripts ([#1388](https://github.com/MemPalace/mempalace/discussions/1388)) |
| Script | `scripts/run-mcp-server.py` | Start MCP server (prefers `uv`, falls back to installed package) |

## License

MIT
