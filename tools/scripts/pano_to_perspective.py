#!/usr/bin/env python
"""Cut a pinhole view out of a panoramic clip.

    python scripts/pano_to_perspective.py <pano_clip_dir> out.mp4 --hfov 90 --yaw 0

``--yaw``/``--pitch`` are relative to the panorama's own forward axis, so 0/0 looks
where the capture looked (and matches the paired first-person clip's heading).
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
from worldrover import equirect                      # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("clip_dir")
    ap.add_argument("out_mp4")
    ap.add_argument("--hfov", type=float, default=90.0)
    ap.add_argument("--yaw", type=float, default=0.0)
    ap.add_argument("--pitch", type=float, default=0.0)
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    w, h = (int(x) for x in args.size.lower().split("x"))
    clip = Clip(args.clip_dir)
    if not clip.is_panoramic:
        print(f"{clip.clip_id} is not a panoramic clip")
        return 1
    fps = float(clip.depth_meta.get("fps", 30))
    cap = cv2.VideoCapture(os.path.join(clip.path, "rgb.mp4"))
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", f"{w}x{h}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "18",
         "-pix_fmt", "yuv420p", args.out_mp4], stdin=subprocess.PIPE)
    n = 0
    while True:
        ok, frame = cap.read()
        if not ok or (args.limit and n >= args.limit):
            break
        view = equirect.to_perspective(frame, args.hfov, (w, h), args.yaw, args.pitch)
        proc.stdin.write(np.ascontiguousarray(view).tobytes())
        n += 1
    cap.release()
    proc.stdin.close()
    proc.wait()
    print(f"{n} frames -> {args.out_mp4}  (hfov {args.hfov} deg, yaw {args.yaw}, pitch {args.pitch})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
