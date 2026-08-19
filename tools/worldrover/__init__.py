"""WorldRover dataset tools — read, verify and visualise the released clips.

    from worldrover import Clip
    clip = Clip("WorldRover/venice/fp/venice_000003")
    rgb = clip.rgb_frame(100)                 # uint8 (H, W, 3), sRGB
    depth_m = clip.depth_frame(100)           # planar depth in metres
    pts = clip.points_world(100, stride=4)    # world points in centimetres

See ``docs/DATA_FORMAT.md`` for the on-disk layout and ``docs/CAMERA_MODEL.md`` for
the coordinate and projection conventions.
"""
from .dataset import Clip, find_clips, paired_clips, video_info  # noqa: F401

__all__ = ["Clip", "find_clips", "paired_clips", "video_info"]
__version__ = "0.1.0"
