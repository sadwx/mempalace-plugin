# mempalace plugin for Claude Code

![version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fsadwx%2Fmempalace-plugin%2Fmaster%2F.claude-plugin%2Fplugin.json&query=%24.version&label=version)

Zero-effort setup and integration of [mempalace](https://github.com/milla-jovovich/mempalace) — a local AI memory system (ChromaDB + SQLite) — into Claude Code.

## What it does

**On install (automatic):**
- MCP server auto-registers, exposing 19 mempalace tools (search, add/delete drawers, knowledge graph, agent diary)
- Stop hook auto-saves conversation context every ~15 messages
- PreCompact hook emergency-saves before context window compression

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

- **Python 3.10+ on `PATH` as `python`** (not only `python3` or `py`).
  - **Windows:** install from [python.org](https://www.python.org/downloads/) or the Microsoft Store — both register `python` on `PATH` by default.
  - **macOS:** `brew install python` registers `python`.
  - **Debian / Ubuntu:** `sudo apt install python-is-python3` if `python` is missing.
- **Either `uv` (recommended) or the `mempalace` package** importable from that Python.
  - With `uv`: zero-install startup — the MCP launcher runs `uv run --with mempalace …` and uv handles provisioning.
  - Without `uv`: run `pip install mempalace` once; the launcher uses that install directly.
- **Claude Code.**

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
| `mempalace wake-up` | ~170 tokens of critical context for session start |
| `mempalace status` | Palace overview |

## Components

| Component | File | Purpose |
|-----------|------|---------|
| MCP | `.mcp.json` | Auto-registers mempalace MCP server |
| Skill | `skills/mempalace/SKILL.md` | `/mempalace` setup command |
| Hook | `hooks/scripts/mempal_save_hook.py` | Auto-save on Stop |
| Hook | `hooks/scripts/mempal_precompact_hook.py` | Emergency save on PreCompact |
| Script | `scripts/run-mcp-server.py` | Start MCP server (prefers `uv`, falls back to installed package) |

## License

MIT
