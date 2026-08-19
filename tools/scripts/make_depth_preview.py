#!/usr/bin/env python
"""Render an RGB-next-to-depth preview video for one clip.

    python scripts/make_depth_preview.py <clip_dir> out.mp4 [--far 60] [--width 960]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worldrover import Clip                          # noqa: E402
from worldrover import viz                           # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("clip_dir")
    ap.add_argument("out_mp4")
    ap.add_argument("--far", type=float, default=60.0, help="depth colour scale ceiling (m)")
    ap.add_argument("--width", type=int, default=960, help="width of each half")
    ap.add_argument("--limit", type=int, default=0, help="stop after N frames (0 = all)")
    args = ap.parse_args()

    clip = Clip(args.clip_dir)
    meta = clip.depth_meta
    fps = float(meta.get("fps", 30))
    cap = cv2.VideoCapture(os.path.join(clip.path, "rgb.mp4"))
    proc = None
    n = 0
    for depth_m in clip.iter_depth():
        ok, bgr = cap.read()
        if not ok:
            break
        frame = viz.rgb_depth_pair(bgr[..., ::-1], depth_m, float(meta["near_m"]),
                                   args.far, args.width)
        if proc is None:
            h, w = frame.shape[:2]
            proc = subprocess.Popen(
                ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                 "-s", f"{w}x{h}", "-r", str(fps), "-i", "-", "-c:v", "libx264",
                 "-crf", "18", "-pix_fmt", "yuv420p", args.out_mp4],
                stdin=subprocess.PIPE)
        proc.stdin.write(np.ascontiguousarray(frame).tobytes())
        n += 1
        if args.limit and n >= args.limit:
            break
    cap.release()
    if proc is not None:
        proc.stdin.close()
        proc.wait()
    print(f"{n} frames -> {args.out_mp4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
