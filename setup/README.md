# Shared Qdrant backend (Windows + WSL)

Run one MemPalace palace shared across machines (e.g. Windows PowerShell + WSL) by
backing it with a single Qdrant server instead of each machine's local Chroma file.

Everything is driven by `~/.mempalace/config.json` — **no persistent env vars** — so
the plugin's MCP server and hooks pick it up automatically.

## Why a config file (not `MEMPALACE_PALACE_PATH`)

A palace's identity is its `palace_path`, hashed into the Qdrant collection name. The
**env var** `MEMPALACE_PALACE_PATH` is `abspath`-normalized per-OS (`/...` vs `C:\...`),
so two OSes could never produce the same identity. The **config.json** `palace_path` is
used *verbatim*, so an identical string there is what makes sharing work. Keep
`MEMPALACE_PALACE_PATH` **unset**.

## Scripts

| Script | Run on | Purpose |
|--------|--------|---------|
| `run-qdrant.ps1` | Windows | Start Qdrant in podman, data bind-mounted at `D:\qdrant-data` |
| `setup-shared-qdrant.py` | each OS | Write `config.json` (shared `palace_path` + qdrant backend) |
| `migrate-chroma-to-qdrant.py` | each OS | Copy existing Chroma drawers into the shared Qdrant (idempotent) |

## One-time setup

1. **Start Qdrant (Windows):**
   ```powershell
   pwsh -ExecutionPolicy Bypass -File setup\run-qdrant.ps1
   ```
   Data persists in `D:\qdrant-data`. Verify: `curl http://localhost:6333/readyz`.

2. **Reach it from WSL.** Qdrant listens on the Windows host. With WSL *mirrored
   networking* (`.wslconfig` → `[wsl2]` / `networkingMode=mirrored`), reach it at the
   Windows host's IP (e.g. `http://192.168.200.56:6333`). `localhost` from WSL may not
   bridge to podman's listener — find the host IP with `ip -br addr | grep eth` and test
   `curl http://<ip>:6333/readyz`.

3. **Pick ONE shared identity string** (must be byte-identical on every machine), e.g.
   `/mnt/d/mempalace-shared`.

4. **Wire each OS** (`uv` provides python):
   ```bash
   # WSL — use the Windows host IP
   uv run python setup/setup-shared-qdrant.py \
     --palace-id /mnt/d/mempalace-shared --qdrant-url http://192.168.200.56:6333
   ```
   ```powershell
   # Windows — localhost works here
   uv run python setup\setup-shared-qdrant.py `
     --palace-id /mnt/d/mempalace-shared --qdrant-url http://localhost:6333
   ```

5. **Migrate existing memory** into the shared store (run on each OS that has a Chroma
   palace — they merge):
   ```bash
   uv run --with mempalace --with qdrant-client python setup/migrate-chroma-to-qdrant.py \
     --qdrant-palace-id /mnt/d/mempalace-shared --qdrant-url http://192.168.200.56:6333
   ```
   (`--dry-run` first to preview counts.)

6. **Restart Claude Code** on each machine. Verify:
   ```bash
   uv run --with mempalace --with qdrant-client mempalace status
   ```

## Constraints & caveats

- `--palace-id` / `palace_path` must be **byte-identical** on every machine.
- Leave `MEMPALACE_EMBEDDING_MODEL` **unset** on all machines (same default → comparable
  vectors). Mixing models in one collection corrupts search.
- Only the **vector drawers + closets** are shared. `tunnels.json` / `hallways.json`
  (the graph layer) are local files per machine.
- `qdrant_url` differs per OS (WSL = host IP, Windows = `localhost`); both reach the same
  server, so they share.
- This leans on an internal behavior (config-file `palace_path` used raw). An upstream
  path-independent palace-id would be the robust long-term fix.

## Rollback

`setup-shared-qdrant.py` backs up your previous config to `config.json.bak`. To return to
the local Chroma palace, restore it (or remove the `backend`/`qdrant_*` keys and set
`palace_path` back) and restart Claude Code. Your Chroma palace is left untouched.
