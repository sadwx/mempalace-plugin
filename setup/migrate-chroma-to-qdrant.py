#!/usr/bin/env python3
"""Migrate an existing local Chroma palace into a shared Qdrant palace.

One-shot, idempotent copy (upsert by drawer id) of the drawer + closet
collections from a local Chroma palace into a Qdrant-backed palace, preserving
documents, metadata, AND the existing embeddings (no re-embedding). Run it on
each machine pointing at the same Qdrant + the same --qdrant-palace-id: their
memories MERGE into one shared palace (matching ids dedupe, new ids accumulate).

Run via uv so the qdrant client is present:

    uv run --with mempalace --with qdrant-client \
        python setup/migrate-chroma-to-qdrant.py \
        --qdrant-palace-id /mnt/d/mempalace-shared \
        --qdrant-url http://192.168.200.56:6333 \
        --qdrant-namespace shared

--qdrant-palace-id MUST be byte-identical to the `palace_path` in config.json on
every machine (it is the shared palace identity). Use --dry-run first to see
counts without writing.
"""
from __future__ import annotations

import argparse
import os
import sys

DEFAULT_COLLECTIONS = ["mempalace_drawers", "mempalace_closets"]


def _open(palace_path: str, name: str, backend: str, create: bool):
    from mempalace.palace import get_collection
    return get_collection(
        palace_path,
        collection_name=name,
        backend=backend,
        create=create,
        _skip_identity_check=True,
    )


def migrate_collection(src_path, dst_id, name, batch, dry_run):
    src = _open(src_path, name, "chroma", create=False)
    dst = None
    total, offset = 0, 0
    while True:
        res = src.get(
            limit=batch, offset=offset,
            include=["documents", "metadatas", "embeddings"],
        )
        ids = list(res.ids or [])
        if not ids:
            break
        docs = list(res.documents or [])
        metas = list(res.metadatas or []) or None
        embs = res.embeddings
        embs = list(embs) if embs is not None else None
        if not dry_run:
            if embs is None or len(embs) != len(ids):
                raise RuntimeError(
                    f"{name}: source returned no/short embeddings — refusing to "
                    f"write vectorless rows to qdrant"
                )
            if dst is None:
                dst = _open(dst_id, name, "qdrant", create=True)
            dst.upsert(documents=docs, ids=ids, metadatas=metas, embeddings=embs)
        total += len(ids)
        offset += len(ids)
        print(f"  {name}: {total} records "
              f"{'counted (dry-run)' if dry_run else 'migrated'}...", flush=True)
    return total


def _existing_chroma_collections(palace_path):
    """Names of collections that actually exist in the source chroma palace, or
    None if it can't be read (then we don't pre-filter)."""
    import sqlite3
    db = os.path.join(palace_path, "chroma.sqlite3")
    try:
        con = sqlite3.connect(db)
        try:
            return {r[0] for r in con.execute("SELECT name FROM collections")}
        finally:
            con.close()
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chroma-palace",
                    default=os.path.expanduser("~/.mempalace/palace"),
                    help="Source Chroma palace dir (default: ~/.mempalace/palace)")
    ap.add_argument("--qdrant-palace-id", required=True,
                    help="Shared identity string; MUST equal config.json palace_path on every machine")
    ap.add_argument("--qdrant-url",
                    default=os.environ.get("MEMPALACE_QDRANT_URL", "http://localhost:6333"))
    ap.add_argument("--qdrant-namespace", default="shared")
    ap.add_argument("--collections", default=",".join(DEFAULT_COLLECTIONS))
    ap.add_argument("--batch", type=int, default=1000)
    ap.add_argument("--dry-run", action="store_true",
                    help="Count source records only; write nothing")
    args = ap.parse_args()

    # Target backend config flows to the qdrant backend via env. Never set
    # MEMPALACE_PALACE_PATH (it would abspath the id and break cross-OS sharing);
    # the raw id is passed straight to get_collection instead.
    os.environ["MEMPALACE_QDRANT_URL"] = args.qdrant_url
    os.environ["MEMPALACE_QDRANT_NAMESPACE"] = args.qdrant_namespace
    os.environ.pop("MEMPALACE_PALACE_PATH", None)

    cols = [c.strip() for c in args.collections.split(",") if c.strip()]
    print(f"Source (chroma): {args.chroma_palace}")
    print(f"Target (qdrant): id={args.qdrant_palace_id!r} url={args.qdrant_url} ns={args.qdrant_namespace}")
    print(f"Collections: {cols} | mode: {'DRY-RUN' if args.dry_run else 'WRITE'}\n")

    if not os.path.isfile(os.path.join(args.chroma_palace, "chroma.sqlite3")):
        print(f"ERROR: no chroma.sqlite3 under {args.chroma_palace}", file=sys.stderr)
        return 2

    existing = _existing_chroma_collections(args.chroma_palace)
    if existing is not None:
        print(f"Source collections present: {sorted(existing)}\n")

    grand, errors = 0, 0
    for name in cols:
        if existing is not None and name not in existing:
            print(f"{name}: not present in source palace — skipping (nothing to migrate)\n")
            continue
        try:
            n = migrate_collection(args.chroma_palace, args.qdrant_palace_id,
                                   name, args.batch, args.dry_run)
            grand += n
            print(f"{name}: {n} total\n")
        except Exception as e:
            print(f"{name}: ERROR — {type(e).__name__}: {e}\n", file=sys.stderr)
            errors += 1

    verb = "counted" if args.dry_run else "migrated into qdrant"
    tail = f" ({errors} collection(s) errored.)" if errors else ""
    print(f"DONE. {grand} records {verb}.{tail}")
    if not args.dry_run and not errors:
        print("Re-running is safe (upsert by id). Run the same command on your other "
              "machine to merge its palace in too.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
