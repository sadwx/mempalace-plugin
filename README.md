# mempalace plugin for Claude Code

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

## Prerequisites

- Python 3.9+ (via `python3`, `python`, or `uv`)
- Claude Code

mempalace itself is installed automatically on first use.

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
| Hook | `hooks/scripts/mempal_save_hook.sh` | Auto-save on Stop |
| Hook | `hooks/scripts/mempal_precompact_hook.sh` | Emergency save on PreCompact |
| Script | `scripts/resolve-python.sh` | Find best Python runtime |
| Script | `scripts/ensure-installed.sh` | Install mempalace if missing |
| Script | `scripts/run-mcp-server.sh` | Start MCP server with resolved Python |

## License

MIT
