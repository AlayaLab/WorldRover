---
license: other
license_name: worldrover-research
pretty_name: WorldRover (lite)
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

# WorldRover

Paired **360-panoramic** and **first-person** video of photoreal 3D environments, with
per-frame depth, camera pose and action labels. Four scenes, ~30 min of each view per
scene — **129 clips per view, ~4.1 h of video** at 30 fps.

**This repository is the lite subset**: RGB + camera pose + actions + metadata, **no depth**
(~103 GB instead of ~800 GB). Lossless 16-bit depth is 87% of the bytes, so it lives in the
per-scene repositories — take it only for the scenes you need.

| Scene | Clips per view | Per view | Full repo (with depth) |
|---|---|---|---|
| med_village | 13 | 32.1 min | [WorldRover-med_village](https://huggingface.co/datasets/xjxu21/WorldRover-med_village) — 270 GB |
| paris | 23 | 30.7 min | [WorldRover-paris](https://huggingface.co/datasets/xjxu21/WorldRover-paris) — 152 GB |
| venice | 46 | 30.4 min | [WorldRover-venice](https://huggingface.co/datasets/xjxu21/WorldRover-venice) — 154 GB |
| art_nouveau | 47 | 30.2 min | [WorldRover-art_nouveau](https://huggingface.co/datasets/xjxu21/WorldRover-art_nouveau) — 164 GB |

## What makes it paired

`pano/<clip_id>` and `fp/<clip_id>` share the same camera path frame for frame: the first-person
clip was rendered from the panoramic clip's per-frame trajectory, so the two
`camera_trajectory.csv` files match exactly. That gives the same world state under two very
different projections without relying on an interpolated alignment.

Clips are 35 s to 3.5 min of continuous motion — no cuts, no teleports.

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
