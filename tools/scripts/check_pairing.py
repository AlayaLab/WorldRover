#!/usr/bin/env python
"""Verify that a scene's first-person and panoramic clips are frame-for-frame paired.

    python scripts/check_pairing.py /data/WorldRover/venice

The two views of a clip id were rendered from the *same* per-frame camera
trajectory, so pose row *k* must agree exactly. This prints the worst per-frame
deviation per pair; anything above a few 0.001 cm means the pair is not aligned.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worldrover import paired_clips                  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scene_dir", help="<root>/<scene> containing pano/ and fp/")
    ap.add_argument("--tol-cm", type=float, default=0.01)
    args = ap.parse_args()

    pairs = paired_clips(args.scene_dir)
    if not pairs:
        print(f"no pano/fp pairs under {args.scene_dir}")
        return 1
    worst = 0.0
    bad = 0
    for pano, fp in pairs:
        a, b = pano.poses, fp.poses
        n = min(len(a), len(b))
        A = np.array([[p["location_x"], p["location_y"], p["location_z"], p["rotation_yaw"]] for p in a[:n]])
        B = np.array([[p["location_x"], p["location_y"], p["location_z"], p["rotation_yaw"]] for p in b[:n]])
        dxyz = np.abs(A[:, :3] - B[:, :3]).max()
        dyaw = np.abs((A[:, 3] - B[:, 3] + 180.0) % 360.0 - 180.0).max()
        worst = max(worst, dxyz)
        flag = "ok  "
        if dxyz > args.tol_cm or dyaw > args.tol_cm or len(a) != len(b):
            flag = "FAIL"
            bad += 1
        print(f"  {flag} {os.path.basename(pano.path)}: {n} frames, "
              f"max |dpos| {dxyz:.6f} cm, max |dyaw| {dyaw:.6f} deg"
              + ("" if len(a) == len(b) else f"  (length {len(a)} vs {len(b)})"))
    print(f"\n{len(pairs) - bad}/{len(pairs)} pairs frame-exact (worst deviation {worst:.6f} cm)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
