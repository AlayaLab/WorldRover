#!/usr/bin/env python
"""Check a WorldRover download against the delivery contract.

    python scripts/verify_dataset.py /data/WorldRover [--check-actions] [--jobs 8]

Per clip it verifies: required files present and non-empty, rgb/depth frame counts
agree, ``camera_trajectory.csv`` has exactly ``n_frames + 1`` rows, and rgb/depth
resolutions match. ``--check-actions`` additionally replays ``gamepad_format/`` and
reports how far the replay drifts from the recorded poses.

Exit code is 0 only if every clip passes.
"""
from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worldrover import Clip, find_clips              # noqa: E402
from worldrover import actions as _actions           # noqa: E402


def action_drift(clip: Clip):
    """Median / p95 position drift (cm) and yaw drift (deg) of the action replay."""
    snap = _actions.load_snapshot(clip.path)
    poses = clip.poses
    n = len(poses) - 1
    vals = _actions.load_axes(clip.path, n_frames=n)
    replay = _actions.integrate(vals, snap)
    ref = np.array([[p["location_x"], p["location_y"], p["rotation_yaw"]] for p in poses[:n]])
    d = np.hypot(replay[:, 0] - ref[:, 0], replay[:, 1] - ref[:, 1])
    dy = np.abs((replay[:, 3] - ref[:, 2] + 180.0) % 360.0 - 180.0)
    return float(np.median(d)), float(np.percentile(d, 95)), float(np.median(dy))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="dataset root (or any directory containing clips)")
    ap.add_argument("--check-actions", action="store_true")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()

    clips = find_clips(args.root)
    if not clips:
        print(f"no clips found under {args.root}")
        return 1
    print(f"{len(clips)} clip(s) under {args.root}")

    def one(clip: Clip):
        problems = clip.check()
        notes = []
        if not problems:
            try:
                declared = int(clip.description["camera"]["trajectory"]["num_frames"])
                actual = int(clip.depth_meta["n_frames"])
                if declared != actual:
                    notes.append(f"description num_frames {declared} vs {actual} rendered "
                                 "(keyframe count includes the closing keyframe)")
            except Exception:  # noqa: BLE001
                pass
        drift = None
        if args.check_actions and not problems:
            try:
                drift = action_drift(clip)
            except Exception as exc:                     # noqa: BLE001
                problems.append(f"action replay failed: {exc}")
        return clip, problems, drift, notes

    bad = 0
    drifts = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for clip, problems, drift, notes in pool.map(one, clips):
            rel = os.path.relpath(clip.path, args.root)
            if problems:
                bad += 1
                print(f"  FAIL {rel}: {'; '.join(problems)}")
            elif drift is not None:
                drifts.append(drift)
                print(f"  ok   {rel}  action replay: {drift[0]:.0f} cm median, "
                      f"{drift[2]:.2f} deg yaw")
            else:
                print(f"  ok   {rel}")
            for n in notes:
                print(f"       note: {n}")
    if drifts:
        a = np.array(drifts)
        print(f"\naction replay across {len(a)} clips: position {np.median(a[:, 0]):.0f} cm median "
              f"(p95 {np.percentile(a[:, 1], 95):.0f} cm), yaw {np.median(a[:, 2]):.2f} deg median")
    print(f"\n{len(clips) - bad}/{len(clips)} clips pass the contract")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
