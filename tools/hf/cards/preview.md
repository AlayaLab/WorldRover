---
license: other
license_name: worldrover-research
pretty_name: WorldRover (preview)
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

# WorldRover-preview

Long, continuous camera paths through photoreal 3D environments, rendered with **per-frame
metric depth, camera pose and action labels** — and, where it matters, rendered **more than
once along the same path**, so you can hold geometry and motion fixed while the projection or
the lighting changes.

This repository is the **original preview release**, as a lite subset: RGB, camera pose,
actions and metadata for four scenes, **without depth** (depth is 87% of the bytes). The
rest of the data lives in the repositories below — see the [collection](https://huggingface.co/collections/AlayaLab/worldrover-6ab4ee625ea9252fbae26a66) for all
parts in one place.

## Parts

| Repository | What it is | Scenes | Clips | Video | Size |
|---|---|---|---|---|---|
| **this repo** (`WorldRover-preview`) | lite: paired panoramic + first-person, RGB + pose + actions, **no depth** | 4 | 129 per view | 4.1 h per view | 103 GB |
| [**WorldRover-6scenes**](https://huggingface.co/datasets/AlayaLab/WorldRover-6scenes) | paired 360° panoramic + first-person, **with lossless depth** | 6 | 600 per view | 18.9 h per view | 7.6 TB |
| [**WorldRover-styles**](https://huggingface.co/datasets/AlayaLab/WorldRover-styles) | one trajectory set re-rendered under 6 lighting/style treatments | 4 | 1000 | 48 h | 818 GB |
| [med_village](https://huggingface.co/datasets/AlayaLab/WorldRover-med_village) · [paris](https://huggingface.co/datasets/AlayaLab/WorldRover-paris) · [venice](https://huggingface.co/datasets/AlayaLab/WorldRover-venice) · [art_nouveau](https://huggingface.co/datasets/AlayaLab/WorldRover-art_nouveau) | the original release, full depth, one repo per scene | 1 each | 13–47 per view | ~30 min per view | 169–334 GB |

**Start with `WorldRover-6scenes`** unless you specifically want the original four-scene
release or the style variants — it is the largest, newest and most complete part.

## The two kinds of pairing

**Same path, two projections** (`WorldRover-6scenes`, and this preview repo). `pano/<clip_id>` and
`fp/<clip_id>` are the same camera path: the first-person clip is rendered from the panoramic
clip's per-frame trajectory, so the two `camera_trajectory.csv` files agree row for row and only
the intrinsics differ (360°/0 mm equirect vs 65.5°/28 mm pinhole). No interpolated alignment is
involved.

**Same path, six appearances** (`WorldRover-styles`). Each trajectory is rendered as a reference
first-person clip plus up to five variants — untextured white model, golden hour, night, snow,
storm — frame-aligned, so the depth, pose and action labels of the reference clip apply to every
variant of it unchanged.

## What a clip contains

```
rgb.mp4                 H.264, 30 fps
depth/depth.mkv         FFV1 16-bit, lossless, log-quantized radial depth
depth/depth.meta.json   near/far, authoritative frame count, decode formula
camera_trajectory.csv   per-frame world pose + intrinsics
description.json        scene, asset pack, licence, trajectory summary, render settings
gamepad_format/         action labels (axis events + timeline)
trajectory.png          top-down path plot
```

Clips are 11 s to 8.5 min of continuous motion — no cuts, no teleports.

## Conventions that are easy to get wrong

* **Depth is log-quantized and radial**: `depth_m = exp(code/65535 * (log 200 − log 0.1) + log 0.1)`,
  and the value is distance along the ray, not along the optical axis. Convert before unprojecting.
  The pixel format is **not the same everywhere**: `WorldRover-6scenes` is uniformly
  `gray16le`, while `WorldRover-styles` is mostly `gbrp16le` with the code in the **R** channel
  (three art_nouveau clips excepted). Each clip's `depth/depth.meta.json` names its own format
  — read it instead of assuming.
* **Frame counts**: `camera_trajectory.csv` has one row more than the video has frames (the last
  row is the closing keyframe). The authoritative count is `depth/depth.meta.json`.
* **Poses are Unreal-style**: left-handed, centimetres, X-forward / Y-right / Z-up, camera looking
  down its own +X.
* **Panoramic frames are equirectangular**: a rectangular crop is *not* a perspective view.
  Reproject before comparing one against a first-person clip.

## Tools

```bash
git clone https://github.com/AlayaLab/WorldRover
pip install -r WorldRover/tools/requirements.txt   # numpy, opencv-python; ffmpeg/ffprobe on PATH
cd WorldRover/tools                                # the package is not pip-installable yet
```

```python
from worldrover import Clip

clip    = Clip("/data/WorldRover-6scenes/venice/fp/venice_000000")
rgb     = clip.rgb_frame(100)     # uint8 (H, W, 3), sRGB
depth_m = clip.depth_frame(100)   # planar depth in metres
pts     = clip.points_world(100)  # world points, centimetres
poses   = clip.poses              # per-frame pose + intrinsics
```

`Clip` takes a filesystem path to a clip directory. The reader takes the depth pixel format
from that clip's own `depth/depth.meta.json`, so it handles both encodings used across these
repositories, and it converts radial depth and the off-by-one trajectory row for you.

## License

Rendered video, depth, camera pose and action labels are released for research use. The
underlying 3D environments are third-party commercial assets, are **not** redistributed here,
and each clip's `description.json` records its asset pack and licence. Tools are MIT.
