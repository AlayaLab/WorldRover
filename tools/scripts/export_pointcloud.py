#!/usr/bin/env python
"""Export one frame of a clip as a coloured point cloud (PLY, metres).

    python scripts/export_pointcloud.py <clip_dir> --frame 100 --stride 2 -o frame100.ply

Works for both perspective and panoramic clips: the depth is unprojected with the
matching camera model and the clip's own pose, so several frames (or the two views of
a pair) land in one consistent world frame.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worldrover import Clip                          # noqa: E402
from worldrover import viz                           # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("clip_dir")
    ap.add_argument("--frame", type=int, default=0)
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--max-depth", type=float, default=60.0, help="drop points beyond this (m)")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()

    clip = Clip(args.clip_dir)
    pts = clip.points_world(args.frame, stride=args.stride)
    rgb = clip.rgb_frame(args.frame)[::args.stride, ::args.stride]
    depth = clip.depth_frame(args.frame, planar=not clip.is_panoramic)[::args.stride, ::args.stride]
    keep = np.isfinite(depth) & (depth < args.max_depth)
    out = args.out or f"{clip.clip_id}_f{args.frame:06d}.ply"
    n = viz.write_ply(out, pts[keep], rgb[keep])
    print(f"{n} points -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
