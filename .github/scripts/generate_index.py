#!/usr/bin/env python3
"""Regenerate index.json from all atlases/ directories."""

import json
import os
from datetime import datetime, timezone

ATLASES_DIR = "atlases"
INDEX_FILE = "index.json"


def process_atlas(name: str) -> dict | None:
    atlas_dir = os.path.join(ATLASES_DIR, name)
    atlas_json_path = os.path.join(atlas_dir, "atlas.json")

    if not os.path.isfile(atlas_json_path):
        print(f"  SKIP {name}: no atlas.json")
        return None

    with open(atlas_json_path, "r", encoding="utf-8") as f:
        atlas = json.load(f)

    # Derive display_name from name if not obvious
    display_name = atlas.get("description", name.replace("-", " ").title())
    # Use first 80 chars of description
    description = atlas.get("description", "")[:200]

    thumbnail_path = os.path.join(atlas_dir, "thumbnail.png")
    has_thumbnail = os.path.isfile(thumbnail_path)

    entry = {
        "name": name,
        "display_name": atlas.get("name", name).replace("-", " ").title(),
        "description": description,
        "author": atlas.get("author", "unknown"),
        "version": atlas.get("semver", "0.0.0"),
        "thumbnail_url": f"atlases/{name}/thumbnail.png" if has_thumbnail else "",
        "entry_count": len(atlas.get("entries", [])),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    origin = atlas.get("origin")
    if origin:
        entry["origin"] = origin

    return entry


def main():
    if not os.path.isdir(ATLASES_DIR):
        print("No atlases/ directory found")
        return

    entries = []
    for name in sorted(os.listdir(ATLASES_DIR)):
        if not os.path.isdir(os.path.join(ATLASES_DIR, name)):
            continue
        if name.startswith("."):
            continue
        print(f"Processing {name}...")
        entry = process_atlas(name)
        if entry:
            entries.append(entry)

    index = {"version": 1, "atlases": entries}

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
        f.write("\n")

    print(f"Generated {INDEX_FILE} with {len(entries)} atlas(es)")


if __name__ == "__main__":
    main()
