#!/usr/bin/env python
"""End-to-end tour of one clip: metadata, a frame, depth, a point cloud, actions.

    python examples/quickstart.py /data/WorldRover/venice/fp/venice_000003
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from worldrover import Clip                              # noqa: E402
from worldrover import actions, camera, viz              # noqa: E402


def main(clip_dir: str) -> int:
    clip = Clip(clip_dir)
    desc = clip.description
    traj = desc["camera"]["trajectory"]
    print(f"{clip.clip_id}: {desc['environment']['scene_short_name']} "
          f"({'equirect' if clip.is_panoramic else 'pinhole'}), "
          f"{traj['num_frames']} frames / {traj['duration_s']:.1f} s, "
          f"path {traj['path_length_cm'] / 100:.0f} m")

    problems = clip.check()
    print("contract:", "; ".join(problems) if problems else "ok")

    mid = traj["num_frames"] // 2
    rgb = clip.rgb_frame(mid)
    depth_m = clip.depth_frame(mid)
    print(f"frame {mid}: rgb {rgb.shape}, depth {depth_m.shape}, "
          f"{np.nanpercentile(depth_m, 5):.1f}-{np.nanpercentile(depth_m, 95):.1f} m")

    # pose + intrinsics for that frame
    cam = clip.poses[mid]
    fx, fy, cx, cy = camera.intrinsics(cam, rgb.shape[1], rgb.shape[0])
    print(f"pose: ({cam['location_x']:.0f}, {cam['location_y']:.0f}, {cam['location_z']:.0f}) cm, "
          f"yaw {cam['rotation_yaw']:.1f} deg, fx {fx:.1f} px")

    # unproject -> world points, and check the round trip
    pts = clip.points_world(mid, stride=8)
    if not clip.is_panoramic:
        u, v, z = camera.project(pts, cam, rgb.shape[1], rgb.shape[0])
        print(f"round-trip: pixels recovered to {np.nanmax(np.abs(np.diff(u, axis=1)) - 8):.1e} px "
              f"of the 8-px stride")

    # actions
    snap = actions.load_snapshot(clip.path)
    vals = actions.load_axes(clip.path, n_frames=traj["num_frames"])
    phys = actions.to_physical(vals, snap)
    print(f"actions: forward {phys['forward_cmps'].min():.0f}..{phys['forward_cmps'].max():.0f} cm/s, "
          f"yaw rate {phys['yaw_rate_dps'].min():.1f}..{phys['yaw_rate_dps'].max():.1f} deg/s")

    import cv2
    cv2.imwrite("quickstart_rgb_depth.jpg", viz.rgb_depth_pair(rgb, depth_m))
    cv2.imwrite("quickstart_trajectory.png", viz.trajectory_topdown(clip.poses))
    n = viz.write_ply("quickstart_frame.ply", pts, rgb[::8, ::8])
    print(f"wrote quickstart_rgb_depth.jpg, quickstart_trajectory.png, "
          f"quickstart_frame.ply ({n} points)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    raise SystemExit(main(sys.argv[1]))
