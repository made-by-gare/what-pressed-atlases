#!/usr/bin/env python3
"""Security scan: detect zip bombs, path traversal, suspicious files, symlinks."""

import os
import sys

ATLASES_DIR = "atlases"

# Files that should never appear in a submission
DANGEROUS_EXTENSIONS = {
    ".exe", ".dll", ".bat", ".cmd", ".ps1", ".sh", ".bash",
    ".msi", ".scr", ".com", ".vbs", ".vbe", ".js", ".jse",
    ".wsf", ".wsh", ".reg", ".inf", ".hta", ".cpl", ".pif",
    ".zip", ".gz", ".tar", ".rar", ".7z", ".bz2", ".xz",
    ".jar", ".war", ".ear", ".apk", ".deb", ".rpm",
    ".iso", ".img", ".dmg",
    ".py", ".rb", ".pl", ".php", ".lua",
    ".html", ".htm", ".svg",  # SVG can contain scripts
}

# Any single file over 2 MB is rejected (matches validate_atlases.py limit).
# This ensures nothing exceeds ClamAV's --max-filesize.
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024

errors: list[str] = []


def error(msg: str):
    errors.append(msg)
    print(f"::error::{msg}")


def scan_path_traversal(atlas_dir: str, name: str):
    """Check for path traversal in filenames and symlinks."""
    for root, dirs, files in os.walk(atlas_dir):
        # Check for symlinks (could point outside repo)
        for d in dirs:
            full = os.path.join(root, d)
            if os.path.islink(full):
                error(f"{name}: Symlink directory found: {os.path.relpath(full, ATLASES_DIR)}")

        for f in files:
            full = os.path.join(root, f)

            # Symlink check
            if os.path.islink(full):
                target = os.readlink(full)
                error(
                    f"{name}: Symlink found: {os.path.relpath(full, ATLASES_DIR)} "
                    f"-> {target}"
                )
                continue

            # Path traversal in filename
            if ".." in f or f.startswith("/") or ":" in f:
                error(
                    f"{name}: Suspicious filename: "
                    f"{os.path.relpath(full, ATLASES_DIR)}"
                )

            # Check the file resolves inside the atlas dir
            real_path = os.path.realpath(full)
            real_atlas = os.path.realpath(atlas_dir)
            if not real_path.startswith(real_atlas):
                error(
                    f"{name}: File resolves outside atlas directory: "
                    f"{os.path.relpath(full, ATLASES_DIR)} -> {real_path}"
                )


def scan_dangerous_files(atlas_dir: str, name: str):
    """Check for files with dangerous extensions."""
    for root, _dirs, files in os.walk(atlas_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in DANGEROUS_EXTENSIONS:
                rel = os.path.relpath(os.path.join(root, f), ATLASES_DIR)
                error(f"{name}: Dangerous file type '{ext}': {rel}")


def scan_file_sizes(atlas_dir: str, name: str):
    """Reject any file over the size limit. Prevents ClamAV silent skips."""
    for root, _dirs, files in os.walk(atlas_dir):
        for f in files:
            full = os.path.join(root, f)
            if not os.path.isfile(full):
                continue
            size = os.path.getsize(full)
            if size > MAX_FILE_SIZE_BYTES:
                rel = os.path.relpath(full, ATLASES_DIR)
                error(
                    f"{name}: {rel} is {size / 1024 / 1024:.1f} MB "
                    f"(max {MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f} MB)"
                )


def scan_hidden_files(atlas_dir: str, name: str):
    """Flag hidden files/directories."""
    for root, dirs, files in os.walk(atlas_dir):
        for d in dirs:
            if d.startswith("."):
                rel = os.path.relpath(os.path.join(root, d), ATLASES_DIR)
                error(f"{name}: Hidden directory: {rel}")
        for f in files:
            if f.startswith("."):
                rel = os.path.relpath(os.path.join(root, f), ATLASES_DIR)
                error(f"{name}: Hidden file: {rel}")


def scan_file_count(atlas_dir: str, name: str):
    """Flag atlases with an unusually high number of files (potential abuse)."""
    count = 0
    for _root, _dirs, files in os.walk(atlas_dir):
        count += len(files)
    if count > 500:
        error(
            f"{name}: Contains {count} files. "
            f"Maximum 500 files per atlas to prevent abuse."
        )


def main():
    if not os.path.isdir(ATLASES_DIR):
        print("No atlases/ directory found")
        return

    # Also scan for unexpected top-level items in atlases/
    for item in os.listdir(ATLASES_DIR):
        full = os.path.join(ATLASES_DIR, item)
        if not os.path.isdir(full):
            error(f"Unexpected file at atlases/ root: {item} (only directories allowed)")
        if os.path.islink(full):
            error(f"Symlink at atlases/ root: {item}")

    for name in sorted(os.listdir(ATLASES_DIR)):
        atlas_dir = os.path.join(ATLASES_DIR, name)
        if not os.path.isdir(atlas_dir):
            continue
        if name.startswith("."):
            continue

        print(f"Security scanning {name}...")
        scan_path_traversal(atlas_dir, name)
        scan_dangerous_files(atlas_dir, name)
        scan_file_sizes(atlas_dir, name)
        scan_hidden_files(atlas_dir, name)
        scan_file_count(atlas_dir, name)

    if errors:
        print(f"\n{len(errors)} security issue(s) found:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Security scan passed!")


if __name__ == "__main__":
    main()
