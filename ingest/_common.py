"""Shared utilities for ingest modules: hashing, snapshot manifests, path helpers."""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
SNAPSHOTS_DIR = ROOT / "data" / "snapshots"


def sha256_file(path: pathlib.Path, chunk_size: int = 1 << 20) -> str:
    """Return hex SHA-256 digest for a file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_manifest(
    source_path: pathlib.Path,
    dest_path: pathlib.Path,
    extra_meta: dict | None = None,
) -> dict:
    """
    Copy source_path to dest_path (raw store) and write a snapshot manifest.

    Returns the manifest dict (also written to data/snapshots/<stem>.json).
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source_path, dest_path)
    digest = sha256_file(dest_path)

    manifest = {
        "source": str(source_path),
        "dest": str(dest_path),
        "sha256": digest,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        **(extra_meta or {}),
    }

    manifest_path = SNAPSHOTS_DIR / f"{dest_path.stem}.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    return manifest


def load_raw_json(filename: str) -> list[dict]:
    """Load a JSON file from data/raw/ by filename."""
    path = RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Raw file not found: {path}\n"
            "Ensure the file has been ingested to data/raw/ before loading."
        )
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)
