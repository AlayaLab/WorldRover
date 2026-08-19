"""Small visualisation helpers (all return BGR uint8 images, ready for cv2.imwrite)."""
from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np

from . import camera as _camera
from . import depth as _depth


def rgb_depth_pair(rgb: np.ndarray, depth_m: np.ndarray, near: float = 0.1,
                   far: float = 60.0, width: int = 960) -> np.ndarray:
    """RGB next to a colourised depth map, both scaled to ``width`` each."""
    import cv2
    d = _depth.colorize(depth_m, near, far)
    h = int(round(rgb.shape[0] * width / rgb.shape[1]))
    left = cv2.resize(rgb[..., ::-1], (width, h))
    right = cv2.resize(d, (width, h))
    return np.hstack([left, right])


def contact_sheet(images: Sequence[np.ndarray], labels: Optional[Sequence[str]] = None,
                  cols: int = 6, cell: tuple = (512, 288)) -> np.ndarray:
    """Grid of thumbnails with optional captions — a quick way to eyeball a scene."""
    import cv2
    import math
    n = len(images)
    rows = math.ceil(n / cols)
    cw, ch = cell
    pad = 18 if labels else 0
    sheet = np.full((rows * (ch + pad), cols * cw, 3), 20, np.uint8)
    for i, img in enumerate(images):
        x, y = (i % cols) * cw, (i // cols) * (ch + pad)
        sheet[y:y + ch, x:x + cw] = cv2.resize(img, (cw, ch))
        if labels:
            cv2.putText(sheet, str(labels[i]), (x + 6, y + ch + 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (225, 225, 230), 1, cv2.LINE_AA)
    return sheet


def trajectory_topdown(poses: List[dict], size: int = 900, margin: int = 40,
                       colour_by_speed: bool = True, fps: float = 30.0) -> np.ndarray:
    """Top-down (X-Y) plot of a clip's path, optionally coloured by speed."""
    import cv2
    xy = np.array([[p["location_x"], p["location_y"]] for p in poses])
    lo, hi = xy.min(0), xy.max(0)
    span = max((hi - lo).max(), 1.0)
    px = ((xy - lo) / span * (size - 2 * margin) + margin).astype(int)
    img = np.full((size, size, 3), 24, np.uint8)
    for g in range(0, size, 100):
        cv2.line(img, (g, 0), (g, size), (40, 40, 44), 1)
        cv2.line(img, (0, g), (size, g), (40, 40, 44), 1)
    spd = _camera.speed_cmps(poses, fps)
    smax = max(np.percentile(spd, 95), 1.0)
    for i in range(1, len(px)):
        if colour_by_speed:
            t = float(np.clip(spd[i] / smax, 0, 1))
            col = tuple(int(c) for c in cv2.applyColorMap(
                np.uint8([[t * 255]]), cv2.COLORMAP_TURBO)[0, 0])
        else:
            col = (90, 200, 255)
        cv2.line(img, tuple(px[i - 1]), tuple(px[i]), col, 2, cv2.LINE_AA)
    cv2.circle(img, tuple(px[0]), 6, (120, 255, 120), -1, cv2.LINE_AA)
    cv2.circle(img, tuple(px[-1]), 6, (120, 120, 255), -1, cv2.LINE_AA)
    cv2.putText(img, f"{span / 100.0:.0f} m across, {len(poses) / fps:.0f} s",
                (margin, size - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 205), 1, cv2.LINE_AA)
    return img


def write_ply(path: str, points_cm: np.ndarray, colours: Optional[np.ndarray] = None) -> int:
    """Write an ASCII PLY in **metres**. ``points_cm`` is ``(..., 3)``; NaNs dropped."""
    pts = np.asarray(points_cm, dtype=np.float64).reshape(-1, 3)
    keep = np.isfinite(pts).all(1)
    cols = None
    if colours is not None:
        cols = np.asarray(colours).reshape(-1, 3)[keep]
    pts = pts[keep] / 100.0
    with open(path, "w") as f:
        f.write("ply\nformat ascii 1.0\nelement vertex %d\n" % len(pts))
        f.write("property float x\nproperty float y\nproperty float z\n")
        if cols is not None:
            f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("end_header\n")
        if cols is None:
            for p in pts:
                f.write("%.4f %.4f %.4f\n" % tuple(p))
        else:
            for p, c in zip(pts, cols):
                f.write("%.4f %.4f %.4f %d %d %d\n" % (p[0], p[1], p[2], c[0], c[1], c[2]))
    return len(pts)
