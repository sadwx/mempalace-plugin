---
name: mempalace
description: Initialize and set up mempalace — a local AI memory system — for the current project. Use this skill when the user mentions mempalace, wants persistent memory across Claude sessions, asks about remembering context between conversations, wants to set up project memory, or runs /mempalace. Also use when the user asks to mine conversations, search memories, or configure memory hooks. Even if they just say "set up memory" or "remember things between sessions", this skill applies.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
argument-hint: "[project-path]"
---

# MemPalace Setup

Fully automated setup of [mempalace](https://github.com/MemPalace/mempalace) — a local AI memory system (ChromaDB + SQLite). This skill runs end-to-end with zero user interaction. Execute every step, report what you did at the end.

The plugin already handles MCP server registration and hook scripts automatically. This skill handles project-specific initialization: palace init, wing config, identity, and initial mining.

## Pre-flight: resolve the `mempalace` command

This skill drives the `mempalace` CLI. Resolve ONE working invocation now and reuse
it — written as `<MP>` in every step below. No `bash` or shell-specific syntax is
needed; this works on Windows, macOS, and Linux. Try in order and stop at the first
that runs `--version` successfully:

1. **`uv` on `PATH`** (check `uv --version`) — preferred, zero-install:
   `<MP>` = `uv run --with mempalace mempalace`
2. **`mempalace` on `PATH`** (check `mempalace --version`):
   `<MP>` = `mempalace`
3. **The plugin's private venv.** When `uv` is absent, the plugin's MCP launcher
   auto-installs mempalace here — it is NOT on `PATH`, so check the file directly:
   - macOS / Linux: `<MP>` = `~/.mempalace/.venv/bin/mempalace`
   - Windows: `<MP>` = `%USERPROFILE%\.mempalace\.venv\Scripts\mempalace.exe`
4. **Not found anywhere** — install once, then use the result. **`uv` is the most
   reliable installer on every OS** — a single static binary with no Python
   prerequisites — so prefer it:
   - Install `uv` (https://docs.astral.sh/uv/), then use option 1.
   - If you genuinely cannot use `uv`, install into the plugin's venv. Note this
     needs `venv` + `ensurepip` in your Python (missing on some distros — e.g.
     Debian/Ubuntu need `sudo apt install python3-venv`; it also sidesteps PEP 668,
     which blocks a plain `pip install`):
     - macOS / Linux: `python3 -m venv ~/.mempalace/.venv && ~/.mempalace/.venv/bin/pip install mempalace`
     - Windows: `python -m venv %USERPROFILE%\.mempalace\.venv` then `%USERPROFILE%\.mempalace\.venv\Scripts\pip.exe install mempalace`
     - then `<MP>` = the venv `mempalace` from option 3.
   - If neither works, tell the user to install `uv` (recommended) or `mempalace`
     manually, then stop — do not guess further.

Confirm the resolved command runs before continuing (substitute your `<MP>`):

```
<MP> --version
```

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
<MP> init . --yes
```

`.` is the current directory (portable across Windows, macOS, and Linux); `--yes`
auto-accepts detected entities so setup stays non-interactive. If the palace
already exists, skip — verify with `<MP> status`.

### Step 3: Configure wings

Check where the wing config lives:
```
<MP> status
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
<MP> mine .
```

Idempotent — safe to run even if already mined.

### Step 6: Verify and report

```
<MP> status
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
- Hooks: SessionStart + Stop + PreCompact auto-configured by plugin (via `mempalace hook run`)
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
