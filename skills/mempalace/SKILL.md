---
name: mempalace
description: Initialize and set up mempalace — a local AI memory system — for the current project. Use this skill when the user mentions mempalace, wants persistent memory across Claude sessions, asks about remembering context between conversations, wants to set up project memory, or runs /mempalace. Also use when the user asks to mine conversations, search memories, or configure memory hooks. Even if they just say "set up memory" or "remember things between sessions", this skill applies.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
argument-hint: "[project-path]"
---

# MemPalace Setup

Fully automated setup of [mempalace](https://github.com/MemPalace/mempalace) — a local AI memory system (ChromaDB + SQLite). This skill runs end-to-end with zero user interaction. Execute every step, report what you did at the end.

The plugin already handles MCP server registration and hook scripts automatically. This skill handles project-specific initialization: palace init, wing config, identity, and initial mining.

## Pre-flight

This skill drives the `mempalace` CLI. Pick a portable invocation that works on
Windows, macOS, and Linux — no `bash` or shell-specific syntax required:

- **If `uv` is available** (check `uv --version`), prefix every `mempalace` command
  with `uv run --with mempalace`. uv provisions mempalace automatically on first
  use, so a fresh machine needs no manual install. The command blocks below use
  this form.
- **If `uv` is not available but `mempalace` is already on `PATH`** (check
  `mempalace --version`), drop the `uv run --with mempalace` prefix and call
  `mempalace …` directly.
- **If neither works**, install once with `uv tool install mempalace` (or
  `pip install mempalace`), then retry. If it still fails, tell the user and stop.

Confirm the CLI runs before continuing:

```
uv run --with mempalace mempalace --version
```

> The plugin's MCP server auto-installs mempalace on first launch, so this
> pre-flight usually just confirms the CLI is reachable for the steps below.

## Automated Setup

Run all steps sequentially. Skip any step whose check passes. Do NOT ask for confirmation — just do it.

### Step 1: Detect project context

Gather info automatically — no user input needed:

1. Get the current working directory name
2. Read CLAUDE.md, README.md, or package manifest if they exist — extract project name and purpose
3. Derive wing name: lowercase the project name, replace `-` and `.` with `_`, prefix with `wing_` (e.g., `psg-mcp` becomes `wing_psg_mcp`)
4. Scan top-level directories to identify 2-4 logical rooms (e.g., `src/`, `tests/`, `docs/`)
5. Derive keywords from: repo name, primary language/framework, key domain terms found in README/CLAUDE.md

### Step 2: Initialize palace

```
uv run --with mempalace mempalace init . --yes
```

`.` is the current directory (portable across Windows, macOS, and Linux); `--yes`
auto-accepts detected entities so setup stays non-interactive. If the palace
already exists, skip — verify with `mempalace status`.

### Step 3: Configure wings

Check where the wing config lives:
```
uv run --with mempalace mempalace status
```

Write/merge wing config (typically `~/.mempalace/wings.json` or inside the palace directory):

```json
{
  "default_wing": "wing_<project_name>",
  "wings": {
    "wing_<project_name>": {
      "type": "project",
      "keywords": ["<project_name>", "<derived_keywords>"]
    }
  }
}
```

If the config already exists with other wings, READ it first and merge — append the new wing, preserve existing wings. Only set `default_wing` if this is the first wing.

### Step 4: Identity file

If `~/.mempalace/identity.txt` does not exist, create it from git config and project context:

```bash
git config user.name
```

Write a ~50 token identity like:
```
<Name> — software engineer working on <project description>.
```

If identity.txt already exists, skip.

### Step 5: Initial mine

Seed the palace with current project context:

```
uv run --with mempalace mempalace mine .
```

Idempotent — safe to run even if already mined.

### Step 6: Verify and report

```
uv run --with mempalace mempalace status
```

Read the plugin version from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` (the `version` field).

Print a single summary:

```
Mempalace plugin v<version> — setup complete:
- Palace: initialized at <path>
- Wing: wing_<project_name> (keywords: ...)
- Identity: <first line>
- Mined: <project_path>
- MCP: auto-registered by plugin
- Hooks: Stop + PreCompact auto-configured by plugin
```

## Quick Reference

After setup, mempalace works automatically via MCP tools in Claude sessions. For manual use:

| Command | Purpose |
|---|---|
| `mempalace search "query"` | Semantic search across memories |
| `mempalace search "query" --wing name` | Search within a specific wing |
| `mempalace mine <path>` | Ingest code/docs |
| `mempalace mine <path> --mode convos` | Ingest conversation exports |
| `mempalace wake-up` | ~600–900 tokens of wake-up context (L0 + L1) for session start |
| `mempalace status` | Palace overview |

## Adding to another project

Run `/mempalace` in any project directory. The skill auto-detects the new project, creates a new wing, and wires everything up. Existing palace data and other wings are preserved.
