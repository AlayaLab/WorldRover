"""Depth decoding for WorldRover clips.

Each clip stores depth as ``depth/depth.mkv`` (FFV1, lossless, 16-bit) plus
``depth/depth.meta.json``::

    {"near_m": 0.1, "far_m": 200.0, "n_frames": 1184, "width": 1280, "height": 720,
     "fps": 30, "format": "FFV1 / gray16le; R = log-quantized depth",
     "decode_formula": {"depth_m": "exp(R / 65535.0 * (log(200.0) - log(0.1)) + log(0.1))"}}

Two things matter when using it:

1. **The 16-bit codes are log-quantized between ``near_m`` and ``far_m``.** Treating
   them as linear depth crushes the near field (the log curve is there to spend
   codes where they matter). Use :func:`codes_to_metres`.
2. **The stored value is radial distance** to the camera centre, not planar depth
   along the forward axis. The two agree on the optical axis and differ by
   ``1/cos(theta)`` off-axis — 13% in the corner of a 1280x720 frame at
   hfov 65.5 deg. Convert with :func:`radial_to_planar` before unprojecting.

Older clips were written as 3-channel ``gbrp16le`` with the payload in R and
G = B = 0; newer ones are single-channel ``gray16le``. Both are handled here.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
from typing import Iterator, Optional, Tuple

import numpy as np

_RAY_CACHE: dict = {}


def load_meta(clip_dir: str) -> dict:
    with open(os.path.join(clip_dir, "depth", "depth.meta.json")) as f:
        return json.load(f)


def _pix_fmt(meta: dict) -> Tuple[str, int]:
    """ffmpeg output pixel format and channel count for this clip's depth video."""
    fmt = str(meta.get("format", "")).lower()
    if "gbrp" in fmt or "rgb" in fmt:
        return "rgb48le", 3
    return "gray16le", 1


def codes_to_metres(codes: np.ndarray, meta: dict) -> np.ndarray:
    """uint16 codes -> radial distance in metres (inverts the log quantization)."""
    near = float(meta["near_m"])
    far = float(meta["far_m"])
    ln, lf = math.log(near), math.log(far)
    return np.exp(ln + codes.astype(np.float64) / 65535.0 * (lf - ln))


def iter_depth(clip_dir: str, meta: Optional[dict] = None,
               start: int = 0, stop: Optional[int] = None) -> Iterator[np.ndarray]:
    """Yield radial depth in metres, frame by frame, decoding the mkv in one pass.

    Streaming keeps memory flat: a 4096x2048 panoramic depth frame is 16 MB, and
    clips run to thousands of frames.
    """
    meta = meta or load_meta(clip_dir)
    pix, nch = _pix_fmt(meta)
    w, h = int(meta["width"]), int(meta["height"])
    nbytes = w * h * nch * 2
    path = os.path.join(clip_dir, "depth", "depth.mkv")
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", pix, "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        i = 0
        while True:
            buf = proc.stdout.read(nbytes)
            if len(buf) != nbytes:
                break
            if stop is not None and i >= stop:
                break
            if i >= start:
                codes = np.frombuffer(buf, np.uint16).reshape(h, w, nch)[..., 0]
                yield codes_to_metres(codes, meta)
            i += 1
    finally:
        proc.stdout.close()
        proc.wait()


def read_depth_frame(clip_dir: str, frame: int, meta: Optional[dict] = None) -> np.ndarray:
    """Radial depth in metres for a single frame (seeks, then decodes one frame)."""
    meta = meta or load_meta(clip_dir)
    pix, nch = _pix_fmt(meta)
    w, h = int(meta["width"]), int(meta["height"])
    path = os.path.join(clip_dir, "depth", "depth.mkv")
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-vf", f"select=eq(n\\,{int(frame)})",
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", pix, "-"],
        capture_output=True).stdout
    if len(out) < w * h * nch * 2:
        raise IndexError(f"frame {frame} not decodable from {path}")
    codes = np.frombuffer(out[: w * h * nch * 2], np.uint16).reshape(h, w, nch)[..., 0]
    return codes_to_metres(codes, meta)


def radial_to_planar(depth_radial: np.ndarray, fx: float, fy: float,
                     cx: Optional[float] = None, cy: Optional[float] = None) -> np.ndarray:
    """Radial distance -> planar depth along the camera forward axis.

    ``planar = radial / sqrt(1 + ((u-cx)/fx)^2 + ((v-cy)/fy)^2)``
    """
    h, w = depth_radial.shape
    cx = w / 2.0 if cx is None else cx
    cy = h / 2.0 if cy is None else cy
    key = (w, h, round(fx, 6), round(fy, 6), round(cx, 3), round(cy, 3))
    r = _RAY_CACHE.get(key)
    if r is None:
        uu, vv = np.meshgrid(np.arange(w), np.arange(h))
        r = np.sqrt(1.0 + ((uu - cx) / fx) ** 2 + ((vv - cy) / fy) ** 2)
        _RAY_CACHE[key] = r
    return depth_radial / r


def colorize(depth_m: np.ndarray, near: float = 0.1, far: float = 60.0) -> np.ndarray:
    """Depth (metres) -> BGR uint8 preview, sqrt-compressed then turbo.

    The sqrt matters: clips are clamped at ``far_m = 200`` but most content sits
    within 2-30 m, so a linear ramp puts nearly everything in one colour band.
    """
    import cv2
    d = np.clip(np.nan_to_num(depth_m, nan=far, posinf=far), near, far)
    t = np.sqrt((d - near) / max(far - near, 1e-9))
    return cv2.applyColorMap((t * 255).astype(np.uint8), cv2.COLORMAP_TURBO)
