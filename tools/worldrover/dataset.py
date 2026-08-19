"""Clip and scene handles: locate files, read frames, check the delivery contract."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Iterator, List, Optional

import numpy as np

from . import camera as _camera
from . import depth as _depth

REQUIRED_FILES = (
    "rgb.mp4",
    "camera_trajectory.csv",
    "description.json",
    "depth/depth.mkv",
    "depth/depth.meta.json",
    "gamepad_format/keybinds_snapshot.json",
    "gamepad_format/gamepad_axis_0.txt",
)


def video_info(path: str) -> dict:
    """``{width, height, n_frames, fps}`` via ffprobe (counts packets when the
    container has no frame count)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
         "-show_entries", "stream=width,height,nb_read_packets,r_frame_rate",
         "-of", "json", path], capture_output=True, text=True).stdout
    st = json.loads(out)["streams"][0]
    num, den = (st.get("r_frame_rate") or "30/1").split("/")
    return {"width": int(st["width"]), "height": int(st["height"]),
            "n_frames": int(st.get("nb_read_packets", 0)),
            "fps": float(num) / float(den or 1)}


@dataclass
class Clip:
    """One clip directory (``.../<scene>/<view>/<clip_id>/``)."""

    path: str

    # ---- metadata -------------------------------------------------------
    @property
    def clip_id(self) -> str:
        return os.path.basename(os.path.normpath(self.path))

    @property
    def description(self) -> dict:
        with open(os.path.join(self.path, "description.json")) as f:
            return json.load(f)

    @property
    def is_panoramic(self) -> bool:
        return self.description.get("camera", {}).get("projection") == "equirectangular"

    @property
    def depth_meta(self) -> dict:
        return _depth.load_meta(self.path)

    @property
    def poses(self) -> List[dict]:
        """Per-frame camera poses; ``len == n_frames + 1`` (trailing keyframe)."""
        return _camera.load_camera_csv(os.path.join(self.path, "camera_trajectory.csv"))

    # ---- pixels ---------------------------------------------------------
    def rgb_frame(self, frame: int) -> np.ndarray:
        """One RGB frame as uint8 ``(H, W, 3)``, already tone-mapped (sRGB)."""
        import cv2
        cap = cv2.VideoCapture(os.path.join(self.path, "rgb.mp4"))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame))
        ok, img = cap.read()
        cap.release()
        if not ok:
            raise IndexError(f"frame {frame} not readable from {self.path}/rgb.mp4")
        return img[..., ::-1].copy()

    def depth_frame(self, frame: int, planar: bool = True) -> np.ndarray:
        """Depth in metres. ``planar=True`` converts the stored *radial* distance to
        depth along the camera forward axis (perspective clips only; panoramic clips
        are radial by construction and returned unchanged)."""
        meta = self.depth_meta
        d = _depth.read_depth_frame(self.path, frame, meta)
        if planar and not self.is_panoramic:
            cam = self.poses[frame]
            fx, fy, _, _ = _camera.intrinsics(cam, int(meta["width"]), int(meta["height"]))
            d = _depth.radial_to_planar(d, fx, fy)
        return d

    def iter_depth(self, planar: bool = True) -> Iterator[np.ndarray]:
        meta = self.depth_meta
        pano = self.is_panoramic
        poses = self.poses
        for i, d in enumerate(_depth.iter_depth(self.path, meta)):
            if planar and not pano:
                fx, fy, _, _ = _camera.intrinsics(poses[min(i, len(poses) - 1)],
                                                  int(meta["width"]), int(meta["height"]))
                d = _depth.radial_to_planar(d, fx, fy)
            yield d

    def points_world(self, frame: int, stride: int = 4) -> np.ndarray:
        """Unproject one frame to world points (cm), subsampled by ``stride``."""
        cam = self.poses[frame]
        if self.is_panoramic:
            from . import equirect
            d = self.depth_frame(frame, planar=False)
            return equirect.unproject(d[::stride, ::stride], cam)
        d = self.depth_frame(frame, planar=True)
        pts = _camera.unproject(d, cam)
        return pts[::stride, ::stride]

    # ---- contract -------------------------------------------------------
    def check(self) -> List[str]:
        """Return a list of problems; empty means the clip satisfies the contract."""
        problems: List[str] = []
        for rel in REQUIRED_FILES:
            p = os.path.join(self.path, rel)
            if not os.path.exists(p):
                problems.append(f"missing {rel}")
            elif os.path.getsize(p) == 0:
                problems.append(f"empty {rel}")
        if problems:
            return problems
        vid = video_info(os.path.join(self.path, "rgb.mp4"))
        meta = self.depth_meta
        n_poses = len(self.poses)
        if vid["n_frames"] != int(meta.get("n_frames", -1)):
            problems.append(f"rgb frames {vid['n_frames']} != depth frames {meta.get('n_frames')}")
        if n_poses != vid["n_frames"] + 1:
            problems.append(f"csv rows {n_poses} != rgb frames + 1 ({vid['n_frames'] + 1})")
        if (vid["width"], vid["height"]) != (int(meta["width"]), int(meta["height"])):
            problems.append("rgb and depth resolutions differ")
        return problems


def find_clips(root: str) -> List[Clip]:
    """All clip directories under ``root`` (a clip is a dir containing ``rgb.mp4``)."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        if "rgb.mp4" in filenames:
            out.append(Clip(dirpath))
            dirnames[:] = []
    return sorted(out, key=lambda c: c.path)


def paired_clips(scene_dir: str) -> List[tuple]:
    """``[(pano_clip, fp_clip), ...]`` for a scene laid out as ``<scene>/{pano,fp}/<id>``.

    Pairing is by clip id: the first-person clip was rendered from the panoramic
    clip's own per-frame camera trajectory, so ids match and frame *k* of one is
    frame *k* of the other (see ``docs/PAIRING.md``).
    """
    pano_root, fp_root = os.path.join(scene_dir, "pano"), os.path.join(scene_dir, "fp")
    if not (os.path.isdir(pano_root) and os.path.isdir(fp_root)):
        return []
    fp = {os.path.basename(c.path): c for c in find_clips(fp_root)}
    return [(p, fp[os.path.basename(p.path)]) for p in find_clips(pano_root)
            if os.path.basename(p.path) in fp]
