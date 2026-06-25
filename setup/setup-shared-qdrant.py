#!/usr/bin/env python3
"""Wire this machine to a shared Qdrant-backed MemPalace — one command, no env vars.

Writes ~/.mempalace/config.json so mempalace (and this plugin's MCP server + hooks)
use the shared Qdrant palace. Everything lives in config.json on purpose:

  * ``palace_path`` is the SHARED palace identity. config.json values are used
    verbatim (config.py:343), unlike MEMPALACE_PALACE_PATH which gets abspath'd
    per-OS — so an identical string here is what lets Windows + WSL share one
    palace. It MUST be byte-identical on every machine.
  * ``backend`` / ``qdrant_url`` / ``qdrant_namespace`` select Qdrant. The plugin
    launcher reads ``backend`` from here too, so it pulls qdrant-client.

Run once per OS (uv provides python):

    uv run python setup/setup-shared-qdrant.py \
        --palace-id /mnt/d/mempalace-shared \
        --qdrant-url http://192.168.200.56:6333     # WSL: Windows host IP
    uv run python setup/setup-shared-qdrant.py \
        --palace-id /mnt/d/mempalace-shared \
        --qdrant-url http://localhost:6333          # Windows

The existing config.json is backed up to config.json.bak and other keys are kept.
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--palace-id", default="/mnt/d/mempalace-shared",
                    help="Shared palace identity — MUST be identical on every machine")
    ap.add_argument("--qdrant-url", default="http://localhost:6333")
    ap.add_argument("--qdrant-namespace", default="shared")
    ap.add_argument("--config-dir", default=os.path.expanduser("~/.mempalace"))
    args = ap.parse_args()

    cfg_dir = args.config_dir
    cfg_path = os.path.join(cfg_dir, "config.json")
    os.makedirs(cfg_dir, exist_ok=True)

    data = {}
    if os.path.isfile(cfg_path):
        try:
            with open(cfg_path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        except (OSError, json.JSONDecodeError):
            data = {}
        # back up before overwriting (preserve the old chroma config for rollback)
        try:
            with open(cfg_path + ".bak", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    prev_palace = data.get("palace_path")
    data["palace_path"] = args.palace_id            # raw shared identity (no abspath)
    data["backend"] = "qdrant"
    data["qdrant_url"] = args.qdrant_url
    data["qdrant_namespace"] = args.qdrant_namespace

    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {cfg_path}")
    print(f"  palace_path      = {args.palace_id}   (identity — keep identical across machines)")
    print(f"  backend          = qdrant")
    print(f"  qdrant_url       = {args.qdrant_url}")
    print(f"  qdrant_namespace = {args.qdrant_namespace}")
    if prev_palace and prev_palace != args.palace_id:
        print(f"  (previous palace_path {prev_palace!r} backed up in config.json.bak)")

    # Guardrail: MEMPALACE_PALACE_PATH would override config.json AND get abspath'd
    # per-OS, silently breaking sharing.
    if os.environ.get("MEMPALACE_PALACE_PATH") or os.environ.get("MEMPAL_PALACE_PATH"):
        print("\n!! WARNING: MEMPALACE_PALACE_PATH is set in your environment. It overrides "
              "config.json and is abspath-normalized per-OS, which BREAKS cross-OS sharing. "
              "Unset it (and restart your shell) before using the shared palace.", file=sys.stderr)

    print("\nNext:")
    print("  1. Migrate your existing Chroma drawers in:  setup/migrate-chroma-to-qdrant.py "
          f"--qdrant-palace-id {args.palace_id} --qdrant-url {args.qdrant_url}")
    print("  2. Restart Claude Code so the MCP server + hooks pick up the new backend.")
    print("  3. Verify: uv run --with mempalace --with qdrant-client mempalace status")
    return 0


if __name__ == "__main__":
    sys.exit(main())
