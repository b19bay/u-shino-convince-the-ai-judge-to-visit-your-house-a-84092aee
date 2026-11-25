#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

Writes the invitation image to $MAKEFUN_OUTPUT_DIR/entry.png.
The image is a fixed asset shipped in this repository (assets/entry.png):
a storybook cottage at dusk above a letter inviting the judge to visit on
Sunday, composed in the authoring session. This program validates the asset
against the competition gate (whole PNG or JPEG, at most 1 MiB, at most
1024x1024 px) and writes it byte-identical to the output directory, so two
runs always produce the same file. Standard library only; no network, no
environment secrets, no wall clock, no randomness.
"""

import os
import struct
import sys
from pathlib import Path

MAX_BYTES = 1_048_576
MAX_DIM = 1024
ASSET = Path(__file__).resolve().parent / "assets" / "entry.png"


def png_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) from a PNG IHDR chunk; raise ValueError if malformed."""
    if len(data) < 33 or data[12:16] != b"IHDR":
        raise ValueError("not a PNG with an IHDR chunk")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) from the first JPEG SOF marker; raise ValueError if none."""
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            return width, height
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + length
    raise ValueError("no JPEG SOF marker found")


def main() -> int:
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        print("MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 1
    data = ASSET.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = png_dimensions(data)
    elif data[:2] == b"\xff\xd8":
        width, height = jpeg_dimensions(data)
    else:
        print("asset is neither PNG nor JPEG", file=sys.stderr)
        return 1
    if len(data) > MAX_BYTES:
        print(f"asset is {len(data)} bytes, over the 1 MiB gate", file=sys.stderr)
        return 1
    if width > MAX_DIM or height > MAX_DIM:
        print(f"asset is {width}x{height}, over the 1024x1024 gate", file=sys.stderr)
        return 1
    out_path = Path(out_dir) / "entry.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    print(f"wrote {out_path} ({len(data)} bytes, {width}x{height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
