#!/usr/bin/env python
"""Contact sheet of the first frame of every clip under a directory.

    python scripts/first_frame_grid.py /data/WorldRover/venice/pano -o venice.jpg
"""
from __future__ import annotations

import argparse
import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worldrover import find_clips                    # noqa: E402
from worldrover import viz                           # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("-o", "--out", default="grid.jpg")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--frame", type=int, default=0)
    args = ap.parse_args()

    clips = find_clips(args.root)
    if not clips:
        print(f"no clips under {args.root}")
        return 1
    imgs, labels = [], []
    for c in clips:
        try:
            imgs.append(c.rgb_frame(args.frame)[..., ::-1])
            labels.append(c.clip_id)
        except Exception as exc:                       # noqa: BLE001
            print(f"  skip {c.clip_id}: {exc}")
    cv2.imwrite(args.out, viz.contact_sheet(imgs, labels, cols=args.cols))
    print(f"{len(imgs)} clip(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
