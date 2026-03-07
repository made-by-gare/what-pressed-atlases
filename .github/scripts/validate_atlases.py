#!/usr/bin/env python3
"""Validate atlas directory structure and atlas.json schema."""

import json
import os
import re
import sys

ATLASES_DIR = "atlases"
MAX_ATLAS_SIZE_MB = 20
MAX_IMAGE_SIZE_MB = 2
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$|^[a-z0-9]$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

errors: list[str] = []


def error(msg: str):
    errors.append(msg)
    print(f"::error::{msg}")


def validate_atlas(name: str):
    atlas_dir = os.path.join(ATLASES_DIR, name)

    # Name format
    if not NAME_PATTERN.match(name):
        error(
            f"{name}: Directory name must be lowercase alphanumeric with hyphens "
            f"(e.g. 'wasd-keys')"
        )

    # Required files
    atlas_json_path = os.path.join(atlas_dir, "atlas.json")
    if not os.path.isfile(atlas_json_path):
        error(f"{name}: Missing atlas.json")
        return

    thumbnail_path = os.path.join(atlas_dir, "thumbnail.png")
    if not os.path.isfile(thumbnail_path):
        error(f"{name}: Missing thumbnail.png")

    images_dir = os.path.join(atlas_dir, "images")
    if not os.path.isdir(images_dir):
        error(f"{name}: Missing images/ directory")

    # Parse atlas.json
    try:
        with open(atlas_json_path, "r", encoding="utf-8") as f:
            atlas = json.load(f)
    except json.JSONDecodeError as e:
        error(f"{name}: Invalid atlas.json - {e}")
        return

    # Required fields
    if not isinstance(atlas, dict):
        error(f"{name}: atlas.json must be a JSON object")
        return

    for field in ["name", "version", "entries"]:
        if field not in atlas:
            error(f"{name}: atlas.json missing required field '{field}'")

    # Name must match directory
    if atlas.get("name") != name:
        error(
            f"{name}: atlas.json 'name' field ('{atlas.get('name')}') "
            f"must match directory name ('{name}')"
        )

    # Version must be integer
    if "version" in atlas and not isinstance(atlas["version"], int):
        error(f"{name}: atlas.json 'version' must be an integer")

    # Semver format
    semver = atlas.get("semver", "")
    if semver and not SEMVER_PATTERN.match(semver):
        error(f"{name}: atlas.json 'semver' must be in format X.Y.Z (got '{semver}')")

    # Entries must be a list
    entries = atlas.get("entries", [])
    if not isinstance(entries, list):
        error(f"{name}: atlas.json 'entries' must be an array")
        entries = []

    # Validate entries reference existing images
    referenced_images = set()
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            error(f"{name}: entries[{i}] must be an object")
            continue
        for field in ["id", "input_id", "label", "pressed_image", "unpressed_image"]:
            if field not in entry:
                error(f"{name}: entries[{i}] missing field '{field}'")

        for img_field in ["pressed_image", "unpressed_image"]:
            img = entry.get(img_field, "")
            if img:
                referenced_images.add(img)
                # Path traversal check
                if ".." in img or img.startswith("/") or ":" in img:
                    error(
                        f"{name}: entries[{i}].{img_field} contains "
                        f"path traversal or absolute path: '{img}'"
                    )

    # Check referenced images exist
    if os.path.isdir(images_dir):
        existing_images = set(os.listdir(images_dir))
        for img in referenced_images:
            if img not in existing_images:
                error(f"{name}: Referenced image '{img}' not found in images/")

    # Total size check
    total_size = 0
    for root, _dirs, files in os.walk(atlas_dir):
        for f in files:
            fpath = os.path.join(root, f)
            size = os.path.getsize(fpath)
            total_size += size

            # Individual image size
            if root == images_dir and size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                error(
                    f"{name}: Image '{f}' is {size / 1024 / 1024:.1f} MB "
                    f"(max {MAX_IMAGE_SIZE_MB} MB)"
                )

    if total_size > MAX_ATLAS_SIZE_MB * 1024 * 1024:
        error(
            f"{name}: Total size {total_size / 1024 / 1024:.1f} MB "
            f"exceeds {MAX_ATLAS_SIZE_MB} MB limit"
        )

    # Check for unexpected file types in images/
    if os.path.isdir(images_dir):
        for f in os.listdir(images_dir):
            ext = os.path.splitext(f)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                error(
                    f"{name}: images/{f} has disallowed extension '{ext}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTS))}"
                )

    # Check for unexpected files at atlas root level
    allowed_root_files = {"atlas.json", "thumbnail.png"}
    allowed_root_dirs = {"images"}
    for item in os.listdir(atlas_dir):
        item_path = os.path.join(atlas_dir, item)
        if os.path.isfile(item_path) and item not in allowed_root_files:
            error(
                f"{name}: Unexpected file '{item}' at atlas root. "
                f"Allowed: {', '.join(sorted(allowed_root_files))}"
            )
        if os.path.isdir(item_path) and item not in allowed_root_dirs:
            error(
                f"{name}: Unexpected directory '{item}' at atlas root. "
                f"Only 'images/' is allowed."
            )


def main():
    if not os.path.isdir(ATLASES_DIR):
        print("No atlases/ directory found, nothing to validate")
        return

    count = 0
    for name in sorted(os.listdir(ATLASES_DIR)):
        if not os.path.isdir(os.path.join(ATLASES_DIR, name)):
            continue
        if name.startswith("."):
            continue
        print(f"Validating {name}...")
        validate_atlas(name)
        count += 1

    print(f"\nValidated {count} atlas(es)")
    if errors:
        print(f"\n{len(errors)} error(s) found:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("All checks passed!")


if __name__ == "__main__":
    main()
