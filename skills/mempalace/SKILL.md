---
name: mempalace
description: Initialize and set up mempalace — a local AI memory system — for the current project. Use this skill when the user mentions mempalace, wants persistent memory across Claude sessions, asks about remembering context between conversations, wants to set up project memory, or runs /mempalace. Also use when the user asks to mine conversations, search memories, or configure memory hooks. Even if they just say "set up memory" or "remember things between sessions", this skill applies.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
argument-hint: "[project-path]"
---

# MemPalace Setup

Fully automated setup of [mempalace](https://github.com/milla-jovovich/mempalace) — a local AI memory system (ChromaDB + SQLite). This skill runs end-to-end with zero user interaction. Execute every step, report what you did at the end.

The plugin already handles MCP server registration and hook scripts automatically. This skill handles project-specific initialization: palace init, wing config, identity, and initial mining.

## Pre-flight

Verify the mempalace CLI is on `PATH`:

```bash
mempalace --version
```

If it's missing, install it once and re-check:

```bash
uv pip install mempalace || pip install --user mempalace
mempalace --version
```

If both installs fail, stop and tell the user to install manually.

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

```bash
mempalace init "$(pwd)"
```

If palace already exists, skip — verify with `mempalace status`.

### Step 3: Configure wings

Check where the wing config lives:
```bash
mempalace status
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

```bash
mempalace mine "$(pwd)"
```

Idempotent — safe to run even if already mined.

### Step 6: Verify and report

```bash
mempalace status
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
| `mempalace sweep <path>` | Idempotent safety-net miner — catches anything `mine` missed (mempalace ≥3.3.2) |
| `mempalace wake-up` | ~170 tokens of critical context for session start |
| `mempalace status` | Palace overview |

## Adding to another project

Run `/mempalace` in any project directory. The skill auto-detects the new project, creates a new wing, and wires everything up. Existing palace data and other wings are preserved.
