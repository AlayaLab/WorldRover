---
license: other
license_name: worldrover-research
pretty_name: WorldRover — paris
task_categories:
  - depth-estimation
  - robotics
tags:
  - video
  - panoramic
  - equirectangular
  - depth
  - camera-pose
  - embodied-ai
  - world-model
  - synthetic
size_categories:
  - 100B<n<1T
---

# WorldRover — paris

Parisian city blocks, outdoor. **23 clips per view, 30.7 min each of panoramic and first-person video**,
30 fps, with lossless per-frame depth, camera pose and action labels.

`pano/<clip_id>` and `fp/<clip_id>` share the same camera path: the first-person clip was rendered
from the panoramic clip's per-frame trajectory, so frame *k* of one is frame *k* of the other and
the two pose files match exactly.

| | |
|---|---|
| Clips | 23 per view (46 total) |
| Duration | 30.7 min per view |
| Panoramic | 4096x2048 equirectangular — 18 GB rgb + 134 GB depth |
| First person | 1280x720 pinhole, hfov 65.5 deg — ~15 GB |

```
paris/
  pano/<clip_id>/  rgb.mp4  depth/{depth.mkv,depth.meta.json}
                   camera_trajectory.csv  description.json
                   gamepad_format/  trajectory.png
  fp/<clip_id>/    (same structure)
```

## Tools

```bash
git clone https://github.com/AlayaLab/WorldRover
pip install -r WorldRover/requirements.txt
```

```python
from worldrover import Clip
clip = Clip("venice/fp/venice_000003")
rgb, depth_m = clip.rgb_frame(100), clip.depth_frame(100)   # sRGB uint8; planar metres
pts = clip.points_world(100)                                # world points, centimetres
```

Three conventions the tools handle for you, and that are easy to get wrong by hand:
depth codes are **log-quantized** and store **radial** distance (convert before
unprojecting); `camera_trajectory.csv` has `n_frames + 1` rows (the last is the closing
keyframe, the authoritative count is `depth/depth.meta.json`); poses are Unreal-style —
left-handed, centimetres, X-forward / Y-right / Z-up, camera looking down its own +X.

## Related

* Collection (all parts in one place): https://huggingface.co/collections/xjxu21/worldrover-6a851193b19350ca6de9f424
* Lite subset (no depth, ~103 GB): https://huggingface.co/datasets/xjxu21/WorldRover
* Full per-scene: [med_village](https://huggingface.co/datasets/xjxu21/WorldRover-med_village) · [paris](https://huggingface.co/datasets/xjxu21/WorldRover-paris) · [venice](https://huggingface.co/datasets/xjxu21/WorldRover-venice) · [art_nouveau](https://huggingface.co/datasets/xjxu21/WorldRover-art_nouveau)
* Tools: https://github.com/AlayaLab/WorldRover

## License

Rendered video, depth, camera pose and action labels are released for research use. The
underlying 3D environments are third-party commercial assets, are **not** redistributed
here, and each clip's `description.json` records its asset pack and license. Tools are MIT.
