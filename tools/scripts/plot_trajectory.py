#!/usr/bin/env python
"""Top-down trajectory plot for one clip or a whole scene.

    python scripts/plot_trajectory.py <clip_or_scene_dir> -o traj.png
"""
from __future__ import annotations

import argparse
import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worldrover import Clip, find_clips              # noqa: E402
from worldrover import viz                           # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("-o", "--out", default="trajectory.png")
    ap.add_argument("--cols", type=int, default=4)
    args = ap.parse_args()

    if os.path.exists(os.path.join(args.path, "rgb.mp4")):
        clips = [Clip(args.path)]
    else:
        clips = find_clips(args.path)
    if not clips:
        print(f"no clips under {args.path}")
        return 1
    imgs, labels = [], []
    for c in clips:
        imgs.append(viz.trajectory_topdown(c.poses))
        labels.append(c.clip_id)
    out = imgs[0] if len(imgs) == 1 else viz.contact_sheet(imgs, labels, cols=args.cols,
                                                          cell=(450, 450))
    cv2.imwrite(args.out, out)
    print(f"{len(clips)} clip(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
