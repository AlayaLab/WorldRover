"""Equirectangular (panoramic) clips.

Panoramic ``rgb.mp4`` is a full 360x180 equirectangular projection, 4096x2048 by
default, rendered as six cube faces and stitched (feathered lanczos). Pixel
``(u, v)`` maps to a direction

    lon = (u + 0.5) / W * 2*pi - pi          # -pi .. pi, 0 = camera forward (+X)
    lat = pi/2 - (v + 0.5) / H * pi          # +pi/2 (up) .. -pi/2 (down)
    d_cam = (cos(lat)cos(lon), cos(lat)sin(lon), sin(lat))   # UE camera axes

so the image centre column looks along the camera's forward axis, columns run
towards +Y (right), and rows run from up (+Z) to down.

Panoramic depth is radial along each of those rays already — unlike the perspective
clips there is nothing to convert; multiply the direction by the distance.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

import numpy as np

from .camera import rotation_world_from_cam


def direction_map(width: int, height: int) -> np.ndarray:
    """Unit ray directions in camera space for every equirect pixel, ``(H, W, 3)``."""
    u = (np.arange(width) + 0.5) / width * 2.0 * math.pi - math.pi
    v = math.pi / 2.0 - (np.arange(height) + 0.5) / height * math.pi
    lon, lat = np.meshgrid(u, v)
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1)


def unproject(depth_radial_m: np.ndarray, cam: dict) -> np.ndarray:
    """Equirect radial depth (metres) -> world points in centimetres, ``(H, W, 3)``."""
    h, w = depth_radial_m.shape
    d = direction_map(w, h) * (depth_radial_m.astype(np.float64) * 100.0)[..., None]
    R = rotation_world_from_cam(cam["rotation_pitch"], cam["rotation_yaw"], cam["rotation_roll"])
    loc = np.array([cam["location_x"], cam["location_y"], cam["location_z"]])
    return d @ R.T + loc


def to_perspective(equirect: np.ndarray, hfov_deg: float = 90.0,
                   out_size: Tuple[int, int] = (960, 540),
                   yaw_deg: float = 0.0, pitch_deg: float = 0.0,
                   interpolation: Optional[int] = None) -> np.ndarray:
    """Cut a pinhole view out of an equirect frame.

    ``yaw_deg`` / ``pitch_deg`` rotate the virtual view relative to the panorama's
    own forward axis (so ``0, 0`` looks where the capture looked). Useful for
    turning a panoramic clip into perspective crops that match a target FOV.
    """
    import cv2
    if interpolation is None:
        interpolation = cv2.INTER_LINEAR
    out_w, out_h = out_size
    eh, ew = equirect.shape[:2]
    f = (out_w / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)
    xx, yy = np.meshgrid(np.arange(out_w), np.arange(out_h))
    # view-space rays: +X forward, +Y right, -Z up (same as the perspective camera)
    dirs = np.stack([np.full_like(xx, f, dtype=np.float64),
                     xx - (out_w - 1) / 2.0,
                     -(yy - (out_h - 1) / 2.0)], axis=-1)
    dirs /= np.linalg.norm(dirs, axis=-1, keepdims=True)
    # rotate the view into panorama space (yaw about Z, then pitch about Y)
    cy, sy = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    cp, sp = math.cos(math.radians(pitch_deg)), math.sin(math.radians(pitch_deg))
    Rz = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])
    Ry = np.array([[cp, 0.0, sp], [0.0, 1.0, 0.0], [-sp, 0.0, cp]])
    d = dirs @ (Rz @ Ry).T
    lon = np.arctan2(d[..., 1], d[..., 0])
    lat = np.arcsin(np.clip(d[..., 2], -1.0, 1.0))
    map_x = ((lon + math.pi) / (2.0 * math.pi) * ew - 0.5).astype(np.float32)
    map_y = ((math.pi / 2.0 - lat) / math.pi * eh - 0.5).astype(np.float32)
    return cv2.remap(equirect, map_x, map_y, interpolation, borderMode=cv2.BORDER_WRAP)
