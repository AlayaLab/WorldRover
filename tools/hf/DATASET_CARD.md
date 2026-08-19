---
license: other
license_name: worldrover-research
license_link: LICENSE
pretty_name: WorldRover
task_categories:
  - video-classification
  - depth-estimation
  - robotics
tags:
  - video
  - panoramic
  - 360
  - equirectangular
  - depth
  - camera-pose
  - embodied-ai
  - world-model
  - synthetic
size_categories:
  - 100B<n<1T
configs:
  - config_name: default
    data_files:
      - split: train
        path: "*/fp/*/rgb.mp4"
---

# WorldRover

Paired **360-panoramic** and **first-person** video of photoreal 3D environments, with
per-frame depth, camera pose and action labels. Four scenes, roughly 30 min of each view
per scene (~4 h of video in total, 30 fps).

The two views of a clip id share the same camera path frame for frame: the first-person clip was
rendered from the panoramic clip's per-frame trajectory, so the pose files match exactly.

## Layout

```
<scene>/                       med_village | paris | venice | art_nouveau
  pano/<clip_id>/              4096x2048 equirectangular
  fp/<clip_id>/                1280x720 pinhole, hfov 65.5 deg
    rgb.mp4                    H.264, 30 fps, sRGB (ACES filmic already applied)
    depth/depth.mkv            FFV1 lossless 16-bit, log-quantized radial distance
    depth/depth.meta.json      near/far, frame count, decode formula
    camera_trajectory.csv      per-frame pose (cm, deg) + intrinsics; n_frames + 1 rows
    description.json           scene identity, asset pack + license, trajectory summary
    gamepad_format/            action labels (axes normalized to [-1, 1])
    trajectory.png             top-down path preview
```

## Reading it

```bash
pip install worldrover  # or: git clone https://github.com/AlayaLab/WorldRover
```

```python
from worldrover import Clip
clip = Clip("venice/fp/venice_000003")
rgb     = clip.rgb_frame(100)      # uint8 (720, 1280, 3), sRGB
depth_m = clip.depth_frame(100)    # planar depth in metres
points  = clip.points_world(100)   # world points in centimetres
```

Three conventions that are easy to get wrong, and are handled by the tools:

1. Depth codes are **log-quantized** between `near_m` and `far_m`, and store **radial**
   distance — divide by `sqrt(1 + ((u-cx)/fx)^2 + ((v-cy)/fy)^2)` for planar depth.
2. `camera_trajectory.csv` has `n_frames + 1` rows; the last row is the closing keyframe.
   The authoritative frame count is `depth/depth.meta.json` -> `n_frames`.
3. Poses are Unreal-style: left-handed, centimetres, X-forward / Y-right / Z-up, camera
   looking down its own +X with image up = -Z.

See the repository's `docs/` for the full format, camera model and pairing notes.

## Sizes

| Scene | Clips (per view) | Duration per view | Panoramic | First person |
|---|---|---|---|---|
| med_village | 13 | 32.1 min | 270 GB | 16 GB |
| paris | 23 | 30.7 min | 152 GB | 15 GB |
| venice | 46 | 30.4 min | 154 GB | 15 GB |
| art_nouveau | 47 | 30.2 min | 164 GB | 15 GB |

Lossless 16-bit depth is ~87% of the volume; the RGB + pose + action subset of the whole
release is about 103 GB.

## License

The rendered video, depth, camera pose and action labels are released for research use.
The underlying 3D environments are third-party commercial assets and are **not**
redistributed here; each clip's `description.json` records the asset pack and its
license. Tools are MIT (see the GitHub repository).
