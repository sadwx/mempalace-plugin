# mempalace plugin for Claude Code

![version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fsadwx%2Fmempalace-plugin%2Fmaster%2F.claude-plugin%2Fplugin.json&query=%24.version&label=version)

Zero-effort setup and integration of [mempalace](https://github.com/MemPalace/mempalace) — a local AI memory system (ChromaDB + SQLite) — into Claude Code.

## What it does

**On install (automatic):**
- MCP server auto-registers, exposing the mempalace MCP toolset (search, add/delete drawers, knowledge graph, agent diary)
- SessionStart hook injects `mempalace wake-up` as session context so the model begins each session with palace memory
- Stop hook auto-saves conversation context every ~15 messages (delegates to upstream's first-class `mempalace hook run` so infinite-loop guards and throttling stay in sync with the library)
- PreCompact hook synchronously mines the session transcript before context compression so nothing is lost

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

- **Python 3.9+ on `PATH` as `python`** (not only `python3` or `py`). 3.9 is the floor inherited from upstream `mempalace`'s `requires-python`.
  - **Windows:** install from [python.org](https://www.python.org/downloads/) or the Microsoft Store — both register `python` on `PATH` by default.
  - **macOS:** `brew install python` registers `python`.
  - **Debian / Ubuntu:** `sudo apt install python-is-python3` if `python` is missing.
- **Either `uv` (recommended) or the `mempalace` package** importable from that Python.
  - With `uv`: zero-install startup — the MCP launcher runs `uv run --with mempalace …` and uv handles provisioning.
  - Without `uv`: run `pip install mempalace` once; the launcher uses that install directly.
  - **Supported `mempalace` version: `>=3.3.3`** ([CHANGELOG](https://github.com/MemPalace/mempalace/blob/main/CHANGELOG.md)). The Stop / PreCompact / SessionStart hooks delegate to upstream's `mempalace hook run` runner, first introduced in 3.3.0 and fixed for cross-platform plugin-dir layouts in 3.3.3 ([#942](https://github.com/MemPalace/mempalace/pull/942)). On older versions the hooks become silent no-ops.
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
| `mempalace sweep <path>` | Idempotent safety-net miner — catches anything `mine` missed (mempalace ≥3.3.2) |
| `mempalace wake-up` | ~170 tokens of critical context for session start |
| `mempalace status` | Palace overview |

## Components

| Component | File | Purpose |
|-----------|------|---------|
| MCP | `.mcp.json` | Auto-registers mempalace MCP server |
| Skill | `skills/mempalace/SKILL.md` | `/mempalace` setup command |
| Hook | `hooks/scripts/mempal_session_start_hook.py` | Inject `mempalace wake-up` as SessionStart context |
| Hook | `hooks/scripts/mempal_save_hook.py` | Auto-save on Stop (delegates to `mempalace hook run --hook stop`) |
| Hook | `hooks/scripts/mempal_precompact_hook.py` | Sync-mine transcript on PreCompact (delegates to `mempalace hook run --hook precompact`) |
| Script | `scripts/run-mcp-server.py` | Start MCP server (prefers `uv`, falls back to installed package) |

### SessionStart wake-up scoping

By default the SessionStart hook runs `mempalace wake-up` (general context). Set `MEMPALACE_WAKE_UP_WING=<wing>` to scope wake-up to a specific project wing.

## License

MIT
