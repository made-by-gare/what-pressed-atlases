"""Generate the plain-outline community atlas.

White outlined keys on transparent background, white filled when pressed
with knocked-out text. Matches the style of the old built-in default atlas.
"""

import json
import os
import uuid
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S = 64  # standard key height

KEYS = [
    # (rdev_name, label, width)
    # Row 1: Escape + F-keys
    ("Escape", "ESC", 64),
    ("F1", "F1", 64),
    ("F2", "F2", 64),
    ("F3", "F3", 64),
    ("F4", "F4", 64),
    ("F5", "F5", 64),
    ("F6", "F6", 64),
    ("F7", "F7", 64),
    ("F8", "F8", 64),
    ("F9", "F9", 64),
    ("F10", "F10", 64),
    ("F11", "F11", 64),
    ("F12", "F12", 64),
    # Row 2: Number row
    ("BackQuote", "`", 64),
    ("Num1", "1", 64),
    ("Num2", "2", 64),
    ("Num3", "3", 64),
    ("Num4", "4", 64),
    ("Num5", "5", 64),
    ("Num6", "6", 64),
    ("Num7", "7", 64),
    ("Num8", "8", 64),
    ("Num9", "9", 64),
    ("Num0", "0", 64),
    ("Minus", "-", 64),
    ("Equal", "=", 64),
    ("Backspace", "BKSP", 128),
    # Row 3: QWERTY
    ("Tab", "TAB", 96),
    ("KeyQ", "Q", 64),
    ("KeyW", "W", 64),
    ("KeyE", "E", 64),
    ("KeyR", "R", 64),
    ("KeyT", "T", 64),
    ("KeyY", "Y", 64),
    ("KeyU", "U", 64),
    ("KeyI", "I", 64),
    ("KeyO", "O", 64),
    ("KeyP", "P", 64),
    ("LeftBracket", "[", 64),
    ("RightBracket", "]", 64),
    ("BackSlash", "\\", 64),
    # Row 4: Home row
    ("CapsLock", "CAPS", 112),
    ("KeyA", "A", 64),
    ("KeyS", "S", 64),
    ("KeyD", "D", 64),
    ("KeyF", "F", 64),
    ("KeyG", "G", 64),
    ("KeyH", "H", 64),
    ("KeyJ", "J", 64),
    ("KeyK", "K", 64),
    ("KeyL", "L", 64),
    ("SemiColon", ";", 64),
    ("Quote", "'", 64),
    ("Return", "ENTER", 128),
    # Row 5: Bottom row
    ("ShiftLeft", "SHIFT", 144),
    ("KeyZ", "Z", 64),
    ("KeyX", "X", 64),
    ("KeyC", "C", 64),
    ("KeyV", "V", 64),
    ("KeyB", "B", 64),
    ("KeyN", "N", 64),
    ("KeyM", "M", 64),
    ("Comma", ",", 64),
    ("Dot", ".", 64),
    ("Slash", "/", 64),
    ("ShiftRight", "SHIFT", 144),
    # Row 6: Bottom modifiers
    ("ControlLeft", "CTRL", 96),
    ("MetaLeft", "WIN", 64),
    ("Alt", "ALT", 64),
    ("Space", "SPACE", 320),
    ("AltGr", "ALTGR", 64),
    ("MetaRight", "WIN", 64),
    ("ControlRight", "CTRL", 96),
    # Navigation cluster
    ("PrintScreen", "PRTSC", 64),
    ("ScrollLock", "SCRLK", 64),
    ("Pause", "PAUSE", 64),
    ("Insert", "INS", 64),
    ("Home", "HOME", 64),
    ("PageUp", "PGUP", 64),
    ("Delete", "DEL", 64),
    ("End", "END", 64),
    ("PageDown", "PGDN", 64),
    # Arrow keys
    ("UpArrow", "UP", 64),
    ("DownArrow", "DOWN", 64),
    ("LeftArrow", "LEFT", 64),
    ("RightArrow", "RIGHT", 64),
    # Numpad
    ("NumLock", "NUMLK", 64),
    ("KpDivide", "N/", 64),
    ("KpMultiply", "N*", 64),
    ("KpMinus", "N-", 64),
    ("Kp7", "N7", 64),
    ("Kp8", "N8", 64),
    ("Kp9", "N9", 64),
    ("KpPlus", "N+", 64),
    ("Kp4", "N4", 64),
    ("Kp5", "N5", 64),
    ("Kp6", "N6", 64),
    ("Kp1", "N1", 64),
    ("Kp2", "N2", 64),
    ("Kp3", "N3", 64),
    ("KpReturn", "NENT", 64),
    ("Kp0", "N0", 128),
    ("KpDelete", "N.", 64),
    # Mouse buttons
    ("ButtonLeft", "LMB", 64),
    ("ButtonRight", "RMB", 64),
    ("ButtonMiddle", "MMB", 64),
]

MOUSE_BUTTONS = {"ButtonLeft", "ButtonRight", "ButtonMiddle"}


def find_font():
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    raise RuntimeError("No suitable font found")


def fit_font(font_path, label, w, h):
    max_h = int(h * 0.50)
    max_w = int(w * 0.75)
    size = max_h
    while size > 6:
        font = ImageFont.truetype(font_path, size)
        bbox = font.getbbox(label)
        tw = bbox[2] - bbox[0]
        if tw <= max_w:
            return font
        size -= 1
    return ImageFont.truetype(font_path, 8)


def render_unpressed(font_path, label, w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 2
    r = 6
    thickness = 3
    draw.rounded_rectangle(
        [margin, margin, w - margin - 1, h - margin - 1],
        radius=r,
        outline=(255, 255, 255, 255),
        width=thickness,
    )
    font = fit_font(font_path, label, w, h)
    bbox = font.getbbox(label)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (w - tw) / 2 - bbox[0]
    ty = (h - th) / 2 - bbox[1]
    draw.text((tx, ty), label, fill=(255, 255, 255, 255), font=font)
    return img


def render_pressed(font_path, label, w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 2
    r = 6
    draw.rounded_rectangle(
        [margin, margin, w - margin - 1, h - margin - 1],
        radius=r,
        fill=(255, 255, 255, 255),
    )
    # Knock out text by drawing it in transparent
    font = fit_font(font_path, label, w, h)
    bbox = font.getbbox(label)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (w - tw) / 2 - bbox[0]
    ty = (h - th) / 2 - bbox[1]
    draw.text((tx, ty), label, fill=(0, 0, 0, 0), font=font)
    return img


def make_thumbnail(font_path):
    """Generate a 256x256 thumbnail showing a few sample keys."""
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    # Draw a few keys arranged like a mini keyboard
    keys_preview = [
        ("Q", 10, 10, 56, 56),
        ("W", 70, 10, 56, 56),
        ("E", 130, 10, 56, 56),
        ("R", 190, 10, 56, 56),
        ("A", 20, 72, 56, 56),
        ("S", 80, 72, 56, 56),
        ("D", 140, 72, 56, 56),
        ("F", 200, 72, 56, 56),
        ("SHIFT", 10, 134, 100, 56),
        ("Z", 114, 134, 56, 56),
        ("X", 174, 134, 56, 56),
        ("SPACE", 30, 196, 196, 50),
    ]
    draw = ImageDraw.Draw(img)
    for label, x, y, w, h in keys_preview:
        draw.rounded_rectangle(
            [x, y, x + w - 1, y + h - 1],
            radius=5,
            outline=(255, 255, 255, 255),
            width=2,
        )
        font = fit_font(font_path, label, w, h)
        bbox = font.getbbox(label)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = x + (w - tw) / 2 - bbox[0]
        ty = y + (h - th) / 2 - bbox[1]
        draw.text((tx, ty), label, fill=(255, 255, 255, 255), font=font)
    return img


def main():
    atlas_dir = Path(__file__).parent.parent / "atlases" / "plain-outline"
    images_dir = atlas_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    font_path = find_font()
    entries = []

    for rdev_name, label, w in KEYS:
        h = S
        up_img = render_unpressed(font_path, label, w, h)
        dn_img = render_pressed(font_path, label, w, h)

        up_file = f"{rdev_name}_up.png"
        dn_file = f"{rdev_name}_dn.png"

        up_img.save(images_dir / up_file)
        dn_img.save(images_dir / dn_file)

        input_type = "MouseButton" if rdev_name in MOUSE_BUTTONS else "Key"

        entries.append({
            "id": str(uuid.uuid4()),
            "input_id": {"type": input_type, "value": rdev_name},
            "label": label,
            "pressed_image": dn_file,
            "unpressed_image": up_file,
            "width": w,
            "height": h,
        })

    atlas = {
        "name": "plain-outline",
        "version": 1,
        "semver": "1.0.0",
        "description": "Clean white outline keyboard with all standard keys. Unpressed shows an outline, pressed fills solid with knocked-out text.",
        "author": "madebygare",
        "entries": entries,
        "source_images": [],
    }

    with open(atlas_dir / "atlas.json", "w") as f:
        json.dump(atlas, f, indent=2)

    thumb = make_thumbnail(font_path)
    thumb.save(atlas_dir / "thumbnail.png")

    print(f"Generated {len(entries)} keys in {atlas_dir}")


if __name__ == "__main__":
    main()
