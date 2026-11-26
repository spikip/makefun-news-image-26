#!/usr/bin/env python3
"""Entry program for the make.fun bounty news-image-20261126.

The image itself — a dense one-page digest of Thursday 26 November 2026's
world news — is drawn ahead of time by render.py in this same directory and
stored as entry.png. This program only has to hand those exact bytes to the
grader: it reads entry.png, checks it against the contest's limits (a whole
PNG, at most 1 MiB, at most 1024 x 1024 pixels), and copies it to the output
directory the harness provides ($MAKEFUN_OUTPUT_DIR, default /output).

Standard library only, no network, no clock, no randomness — every run
writes the same bytes.
"""
import os
import shutil
import struct
import sys

BYTE_LIMIT = 1_048_576
PIXEL_LIMIT = 1024
PNG_HEAD = b"\x89PNG\r\n\x1a\n"
PNG_TAIL = b"IEND\xaeB`\x82"


def read_checked_png(path):
    """Read a PNG and return (width, height, bytes), raising on any problem."""
    with open(path, "rb") as handle:
        blob = handle.read()
    if len(blob) > BYTE_LIMIT:
        raise ValueError(f"entry.png is {len(blob)} bytes, over the 1 MiB cap")
    if not blob.startswith(PNG_HEAD):
        raise ValueError("entry.png does not start with the PNG signature")
    if not blob.endswith(PNG_TAIL):
        raise ValueError("entry.png is truncated: the IEND chunk is missing")
    width, height = struct.unpack(">II", blob[16:24])
    if width > PIXEL_LIMIT or height > PIXEL_LIMIT:
        raise ValueError(f"entry.png is {width}x{height}, over the 1024 px cap")
    return width, height, blob


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    width, height, blob = read_checked_png(source)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "entry.png")
    shutil.copyfile(source, dest)
    # Verify the copy landed byte-for-byte: a short write must never pass
    # silently, since the grader runs this program twice and compares bytes.
    with open(dest, "rb") as handle:
        copied = handle.read()
    if copied != blob:
        raise ValueError("copied entry.png does not match the source bytes")
    print(f"entry.png delivered: {width}x{height}, {len(blob)} bytes -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
