"""Camera model for WorldRover clips.

Conventions (inherited from the renderer, Unreal Engine):

* World is **left-handed**, units **centimetres**: X = forward, Y = right, Z = up.
* A camera pose is an Unreal rotator ``(pitch, yaw, roll)`` in degrees: pitch about
  Y, yaw about Z, roll about X.
* The camera looks down its own **+X**; image right is **+Y**, image up is **-Z**
  (so pixel row ``v`` grows downward, as usual).
* Perspective clips are rendered with a physical camera: ``focal_length_mm`` on a
  ``sensor_width_mm x sensor_height_mm`` filmback. ``hfov_deg`` is provided as a
  convenience and agrees with the focal length.

Panoramic clips are equirectangular (see :mod:`worldrover.equirect`); their rows in
``camera_trajectory.csv`` carry ``hfov_deg = 360`` and no meaningful focal length.
"""
from __future__ import annotations

import csv
import math
from typing import Dict, List

import numpy as np

CM_PER_M = 100.0


def load_camera_csv(path: str) -> List[dict]:
    """Read ``camera_trajectory.csv`` into a list of per-frame dicts (floats parsed).

    The file has one row per rendered frame **plus one tail row** (the renderer's
    closing keyframe), so ``len(rows) == n_video_frames + 1``. Index the list by
    frame number; row ``i`` is the pose the video's frame ``i`` was rendered with.
    """
    rows: List[dict] = []
    with open(path, newline="") as f:
        for raw in csv.DictReader(f):
            row = {}
            for k, v in raw.items():
                try:
                    row[k] = float(v)
                except (TypeError, ValueError):
                    row[k] = v
            rows.append(row)
    return rows


def intrinsics(cam: dict, width: int, height: int):
    """Return ``(fx, fy, cx, cy)`` in pixels for a perspective frame.

    Prefers the physical filmback (focal length / sensor size) and falls back to
    ``hfov_deg``. The principal point is the image centre.
    """
    sw = float(cam.get("sensor_width_mm") or cam.get("sensor_width") or 0.0)
    sh = float(cam.get("sensor_height_mm") or cam.get("sensor_height") or 0.0)
    fmm = float(cam.get("focal_length_mm") or 0.0)
    if fmm > 0.0 and sw > 0.0:
        fx = fmm / sw * width
        fy = fmm / sh * height if sh > 0.0 else fx
    else:
        hfov = math.radians(float(cam["hfov_deg"]))
        fx = fy = (width / 2.0) / math.tan(hfov / 2.0)
    return fx, fy, width / 2.0, height / 2.0


def rotation_world_from_cam(pitch_deg: float, yaw_deg: float, roll_deg: float) -> np.ndarray:
    """Unreal rotator -> 3x3 matrix whose **columns** are the camera's world axes
    (forward, right, up). Equivalent to ``FRotationMatrix(FRotator(p, y, r))``."""
    p, y, r = map(math.radians, (pitch_deg, yaw_deg, roll_deg))
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    cr, sr = math.cos(r), math.sin(r)
    fwd = np.array([cp * cy, cp * sy, sp])
    right = np.array([sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp])
    up = np.array([-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp])
    return np.stack([fwd, right, up], axis=1)


def pose_matrix(cam: dict) -> np.ndarray:
    """4x4 camera-to-world matrix in centimetres."""
    T = np.eye(4)
    T[:3, :3] = rotation_world_from_cam(cam["rotation_pitch"], cam["rotation_yaw"],
                                        cam["rotation_roll"])
    T[:3, 3] = [cam["location_x"], cam["location_y"], cam["location_z"]]
    return T


def ray_directions(cam: dict, width: int, height: int) -> np.ndarray:
    """Unit ray directions in **camera** space for every pixel, shape ``(H, W, 3)``."""
    fx, fy, cx, cy = intrinsics(cam, width, height)
    uu, vv = np.meshgrid(np.arange(width), np.arange(height))
    d = np.stack([np.ones_like(uu, dtype=np.float64),
                  (uu - cx) / fx,
                  -(vv - cy) / fy], axis=-1)
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


def unproject(depth_planar_m: np.ndarray, cam: dict) -> np.ndarray:
    """Planar depth (metres) -> world points in centimetres, shape ``(H, W, 3)``.

    ``depth_planar_m`` must be **planar** depth (distance along the camera's
    forward axis). The depth stored in the dataset is radial; convert it first with
    :func:`worldrover.depth.radial_to_planar`.
    """
    height, width = depth_planar_m.shape
    fx, fy, cx, cy = intrinsics(cam, width, height)
    uu, vv = np.meshgrid(np.arange(width), np.arange(height))
    dir_cam = np.stack([np.ones_like(uu, dtype=np.float64),
                        (uu - cx) / fx,
                        -(vv - cy) / fy], axis=-1)
    pts_cam = dir_cam * (depth_planar_m.astype(np.float64) * CM_PER_M)[..., None]
    R = rotation_world_from_cam(cam["rotation_pitch"], cam["rotation_yaw"], cam["rotation_roll"])
    loc = np.array([cam["location_x"], cam["location_y"], cam["location_z"]])
    return pts_cam @ R.T + loc


def project(pts_world_cm: np.ndarray, cam: dict, width: int, height: int):
    """World points (cm) -> ``(u, v, planar_depth_m)``. Inverse of :func:`unproject`."""
    fx, fy, cx, cy = intrinsics(cam, width, height)
    R = rotation_world_from_cam(cam["rotation_pitch"], cam["rotation_yaw"], cam["rotation_roll"])
    loc = np.array([cam["location_x"], cam["location_y"], cam["location_z"]])
    pc = (np.asarray(pts_world_cm, dtype=np.float64) - loc) @ R
    z = pc[..., 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        u = pc[..., 1] / z * fx + cx
        v = -pc[..., 2] / z * fy + cy
    return u, v, z / CM_PER_M


def speed_cmps(rows: List[dict], fps: float = 30.0) -> np.ndarray:
    """Per-frame planar speed in cm/s from consecutive poses (central difference)."""
    xy = np.array([[r["location_x"], r["location_y"]] for r in rows])
    n = len(xy)
    out = np.zeros(n)
    for i in range(n):
        lo, hi = max(0, i - 1), min(n - 1, i + 1)
        out[i] = np.hypot(*(xy[hi] - xy[lo])) / max(1, hi - lo) * fps
    return out
