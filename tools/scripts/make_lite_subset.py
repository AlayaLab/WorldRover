#!/usr/bin/env python
"""Build the RGB + pose + action subset of a release (everything except depth).

    python scripts/make_lite_subset.py /data/WorldRover /data/WorldRover-lite [--link]

Depth is ~87% of the bytes, so the lite variant is ~103 GB against ~800 GB — a much
friendlier default download for anyone who only needs video and poses. ``--link`` hard
links instead of copying (same filesystem only).
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worldrover import find_clips                    # noqa: E402

KEEP_FILES = ("rgb.mp4", "camera_trajectory.csv", "description.json", "trajectory.png")
KEEP_DIRS = ("gamepad_format",)
KEEP_DEPTH_META = os.path.join("depth", "depth.meta.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--link", action="store_true", help="hard link instead of copy")
    args = ap.parse_args()

    put = os.link if args.link else shutil.copy2
    n_clips = n_bytes = 0
    for clip in find_clips(args.src):
        rel = os.path.relpath(clip.path, args.src)
        out = os.path.join(args.dst, rel)
        os.makedirs(os.path.join(out, "depth"), exist_ok=True)
        for name in KEEP_FILES + (KEEP_DEPTH_META,):
            s = os.path.join(clip.path, name)
            if os.path.exists(s):
                d = os.path.join(out, name)
                os.makedirs(os.path.dirname(d), exist_ok=True)
                if not os.path.exists(d):
                    put(s, d)
                n_bytes += os.path.getsize(s)
        for sub in KEEP_DIRS:
            s = os.path.join(clip.path, sub)
            if os.path.isdir(s):
                d = os.path.join(out, sub)
                os.makedirs(d, exist_ok=True)
                for f in os.listdir(s):
                    if not os.path.exists(os.path.join(d, f)):
                        put(os.path.join(s, f), os.path.join(d, f))
                    n_bytes += os.path.getsize(os.path.join(s, f))
        n_clips += 1
    print(f"{n_clips} clips -> {args.dst}  ({n_bytes / 1e9:.1f} GB, depth excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
