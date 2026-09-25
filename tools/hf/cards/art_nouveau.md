---
license: other
license_name: worldrover-research
pretty_name: WorldRover — art_nouveau
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

# WorldRover — art_nouveau

Art Nouveau mansion, indoor. **47 clips per view, 30.2 min each of panoramic and first-person video**,
30 fps, with lossless per-frame depth, camera pose and action labels.

`pano/<clip_id>` and `fp/<clip_id>` share the same camera path: the first-person clip was rendered
from the panoramic clip's per-frame trajectory, so frame *k* of one is frame *k* of the other and
the two pose files match exactly.

| | |
|---|---|
| Clips | 47 per view (94 total) |
| Duration | 30.2 min per view |
| Panoramic | 4096x2048 equirectangular — 22 GB rgb + 142 GB depth |
| First person | 1280x720 pinhole, hfov 65.5 deg — ~15 GB |

```
art_nouveau/
  pano/<clip_id>/  rgb.mp4  depth/{depth.mkv,depth.meta.json}
                   camera_trajectory.csv  description.json
                   gamepad_format/  trajectory.png
  fp/<clip_id>/    (same structure)
```

## Tools

```bash
git clone https://github.com/AlayaLab/WorldRover
pip install -r WorldRover/tools/requirements.txt   # numpy, opencv-python; ffmpeg/ffprobe on PATH
cd WorldRover/tools                                # the package is not pip-installable yet
```

```python
from worldrover import Clip
clip = Clip("/data/WorldRover-art_nouveau/venice/fp/venice_000003")
rgb, depth_m = clip.rgb_frame(100), clip.depth_frame(100)   # sRGB uint8; planar metres
pts = clip.points_world(100)                                # world points, centimetres
```

Three conventions the tools handle for you, and that are easy to get wrong by hand:
depth codes are **log-quantized** and store **radial** distance (convert before
unprojecting); `camera_trajectory.csv` has `n_frames + 1` rows (the last is the closing
keyframe, the authoritative count is `depth/depth.meta.json`); poses are Unreal-style —
left-handed, centimetres, X-forward / Y-right / Z-up, camera looking down its own +X.

## Related

* Collection (all parts in one place): https://huggingface.co/collections/AlayaLab/worldrover-6ab4ee625ea9252fbae26a66
* Lite subset (no depth, ~103 GB): https://huggingface.co/datasets/AlayaLab/WorldRover
* Full per-scene: [med_village](https://huggingface.co/datasets/AlayaLab/WorldRover-med_village) · [paris](https://huggingface.co/datasets/AlayaLab/WorldRover-paris) · [venice](https://huggingface.co/datasets/AlayaLab/WorldRover-venice) · [art_nouveau](https://huggingface.co/datasets/AlayaLab/WorldRover-art_nouveau)
* Newer releases: [WorldRover-6scenes](https://huggingface.co/datasets/AlayaLab/WorldRover-6scenes) — six scenes, 600 paired clips per view, 7.6 TB · [WorldRover-styles](https://huggingface.co/datasets/AlayaLab/WorldRover-styles) — the same trajectories under six lighting/style treatments
* Tools: https://github.com/AlayaLab/WorldRover

## License

Rendered video, depth, camera pose and action labels are released for research use. The
underlying 3D environments are third-party commercial assets, are **not** redistributed
here, and each clip's `description.json` records its asset pack and license. Tools are MIT.
