#!/usr/bin/env python3
"""Validate that image files are actually valid images, not disguised binaries."""

import os
import struct
import sys

ATLASES_DIR = "atlases"

# Magic bytes for allowed image formats
MAGIC_SIGNATURES = {
    "PNG": (b"\x89PNG\r\n\x1a\n",),
    "JPEG": (b"\xff\xd8\xff",),
    "WebP": (b"RIFF",),  # RIFF header, then check for WEBP
}

errors: list[str] = []


def error(msg: str):
    errors.append(msg)
    print(f"::error::{msg}")


def identify_image(filepath: str) -> str | None:
    """Return format name if valid image, None otherwise."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(16)
    except IOError:
        return None

    if len(header) < 4:
        return None

    # PNG
    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG"

    # JPEG
    if header[:3] == b"\xff\xd8\xff":
        return "JPEG"

    # WebP (RIFF....WEBP)
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "WebP"

    return None


def check_png_dimensions(filepath: str) -> tuple[int, int] | None:
    """Read PNG dimensions from IHDR chunk."""
    try:
        with open(filepath, "rb") as f:
            f.read(8)  # skip signature
            f.read(4)  # chunk length
            chunk_type = f.read(4)
            if chunk_type != b"IHDR":
                return None
            width = struct.unpack(">I", f.read(4))[0]
            height = struct.unpack(">I", f.read(4))[0]
            return (width, height)
    except (IOError, struct.error):
        return None


def validate_image(filepath: str, name: str, filename: str):
    ext = os.path.splitext(filename)[1].lower()
    fmt = identify_image(filepath)

    if fmt is None:
        error(
            f"{name}: {filename} is not a valid image file "
            f"(unrecognized magic bytes)"
        )
        return

    # Check extension matches actual format
    expected_exts = {
        "PNG": {".png"},
        "JPEG": {".jpg", ".jpeg"},
        "WebP": {".webp"},
    }
    if ext not in expected_exts.get(fmt, set()):
        error(
            f"{name}: {filename} has extension '{ext}' but is actually "
            f"{fmt} format. Please use the correct extension."
        )

    # For PNGs, check for absurd dimensions (decompression bomb)
    if fmt == "PNG":
        dims = check_png_dimensions(filepath)
        if dims:
            w, h = dims
            # 8192x8192 is more than generous for key images
            if w > 8192 or h > 8192:
                error(
                    f"{name}: {filename} has dimensions {w}x{h} which is "
                    f"excessively large. Max 8192x8192."
                )
            # Total pixel count check (potential decompression bomb)
            if w * h > 67_108_864:  # 8192*8192
                error(
                    f"{name}: {filename} has {w * h:,} pixels - "
                    f"possible decompression bomb"
                )


def main():
    if not os.path.isdir(ATLASES_DIR):
        print("No atlases/ directory")
        return

    count = 0
    for atlas_name in sorted(os.listdir(ATLASES_DIR)):
        atlas_dir = os.path.join(ATLASES_DIR, atlas_name)
        if not os.path.isdir(atlas_dir):
            continue
        if atlas_name.startswith("."):
            continue

        # Check thumbnail
        thumb = os.path.join(atlas_dir, "thumbnail.png")
        if os.path.isfile(thumb):
            validate_image(thumb, atlas_name, "thumbnail.png")
            count += 1

        # Check all images
        images_dir = os.path.join(atlas_dir, "images")
        if not os.path.isdir(images_dir):
            continue

        for filename in sorted(os.listdir(images_dir)):
            filepath = os.path.join(images_dir, filename)
            if not os.path.isfile(filepath):
                continue
            validate_image(filepath, atlas_name, f"images/{filename}")
            count += 1

    print(f"Validated {count} image(s)")
    if errors:
        print(f"\n{len(errors)} error(s) found:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("All images valid!")


if __name__ == "__main__":
    main()
