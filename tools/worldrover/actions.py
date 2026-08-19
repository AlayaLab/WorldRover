"""Action labels (``gamepad_format/``).

Every clip ships a gamepad-style action stream derived from the camera motion, so a
policy can be trained on (frame, action) pairs without touching the renderer:

    gamepad_format/
      keybinds_snapshot.json   fps, hfov, start pose, axis normalization, bindings
      gamepad_axis_0.txt       "<timestamp>: axis_<n>,d,<value>"  (~1 line per axis per frame)
      gamepad_button_0.txt     button events (empty for synthetic capture)
      key_0.txt                keyboard events (empty)
      mouse_move_0.txt         mouse deltas (empty)
      timeline.txt             render start/end markers

Axes are normalized to [-1, 1]; ``axis_normalization`` in the snapshot gives the
physical value at 1.0. With the default profile:

    axis_0  strafe right   100 cm/s at 1.0
    axis_1  forward/back   210 cm/s at 1.0   (forward is NEGATIVE, per `bindings`)
    axis_2  yaw right       30 deg/s at 1.0
    axis_3  vertical        100 cm/s at 1.0
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional, Tuple

import numpy as np

_LINE = re.compile(r"^(?P<ts>[\d\-: .]+):\s*axis_(?P<axis>\d+),\w+,(?P<val>-?[\d.eE+]+)")


def load_snapshot(clip_dir: str) -> dict:
    with open(os.path.join(clip_dir, "gamepad_format", "keybinds_snapshot.json")) as f:
        return json.load(f)


def load_events(clip_dir: str) -> List[Tuple[float, int, float]]:
    """Parse ``gamepad_axis_0.txt`` into ``(t_seconds_from_first_event, axis, value)``.

    The stream is **event driven**: a line appears when an axis changes, at wall-clock
    timestamps, not once per frame. Sample it at frame boundaries (see
    :func:`sample_per_frame`) rather than treating one line as one frame.
    """
    import datetime
    path = os.path.join(clip_dir, "gamepad_format", "gamepad_axis_0.txt")
    events: List[Tuple[float, int, float]] = []
    t0 = None
    with open(path) as f:
        for line in f:
            m = _LINE.match(line.strip())
            if not m:
                continue
            ts = datetime.datetime.strptime(m.group("ts").strip(), "%Y-%m-%d %H:%M:%S.%f")
            if t0 is None:
                t0 = ts
            events.append(((ts - t0).total_seconds(), int(m.group("axis")), float(m.group("val"))))
    return events


def sample_per_frame(events, n_frames: int, fps: float = 30.0, n_axes: int = 4) -> np.ndarray:
    """Axis state held at each frame boundary, shape ``(n_frames, n_axes)``."""
    state = np.zeros(n_axes)
    out = np.zeros((n_frames, n_axes))
    k = 0
    for frame in range(n_frames):
        t = frame / fps
        while k < len(events) and events[k][0] <= t:
            _, axis, val = events[k]
            if 0 <= axis < n_axes:
                state[axis] = val
            k += 1
        out[frame] = state
    return out


def load_axes(clip_dir: str, n_frames: Optional[int] = None, fps: Optional[float] = None,
              n_axes: int = 4) -> np.ndarray:
    """Per-frame axis values for a clip, shape ``(n_frames, n_axes)``.

    ``n_frames``/``fps`` default to the clip's own snapshot and event span.
    """
    snap = load_snapshot(clip_dir)
    fps = float(fps or snap.get("fps", 30))
    events = load_events(clip_dir)
    if n_frames is None:
        n_frames = int(round(events[-1][0] * fps)) + 1 if events else 0
    return sample_per_frame(events, n_frames, fps, n_axes)


def to_physical(values: np.ndarray, snapshot: dict) -> Dict[str, np.ndarray]:
    """Normalized axes -> physical rates, using the clip's own normalization block.

    ``axis_1`` is negated: the binding block maps *forward* to ``AXIS_1_NEG``.
    """
    n = snapshot.get("axis_normalization", {})
    return {
        "strafe_cmps": values[:, 0] * float(n.get("axis_0_cmps_at_one", 100.0)),
        "forward_cmps": -values[:, 1] * float(n.get("axis_1_cmps_at_one", 210.0)),
        "yaw_rate_dps": values[:, 2] * float(n.get("axis_2_dps_at_one", 30.0)),
        "vertical_cmps": values[:, 3] * float(n.get("axis_3_cmps_at_one", 100.0)),
    }


def integrate(values: np.ndarray, snapshot: dict) -> np.ndarray:
    """Replay per-frame actions into poses ``(T, 4) = (x, y, z, yaw_deg)``.

    Mirrors the renderer's own inverse (``tools/gamepad_to_keyframes.py``): position
    advances with the *current* yaw, then yaw integrates. Starts from
    ``snapshot["start_pose"]``. Use it to check the labels against
    ``camera_trajectory.csv``.
    """
    import math
    p = snapshot["start_pose"]
    fps = float(snapshot.get("fps", 30))
    dt = 1.0 / fps
    phys = to_physical(values, snapshot)
    x, y, z, yaw = float(p["x"]), float(p["y"]), float(p["z"]), float(p["yaw"])
    out = np.zeros((len(values), 4))
    for i in range(len(values)):
        out[i] = (x, y, z, yaw)
        r = math.radians(yaw)
        fwd = (math.cos(r), math.sin(r))
        right = (-math.sin(r), math.cos(r))
        x += (phys["forward_cmps"][i] * fwd[0] + phys["strafe_cmps"][i] * right[0]) * dt
        y += (phys["forward_cmps"][i] * fwd[1] + phys["strafe_cmps"][i] * right[1]) * dt
        z += phys["vertical_cmps"][i] * dt
        yaw += phys["yaw_rate_dps"][i] * dt
    return out
