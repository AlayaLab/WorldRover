---
license: other
license_name: worldrover-research
pretty_name: WorldRover 6-scene paired panoramic + first-person
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
  - n>1T
---

# WorldRover-6scenes

**600 camera paths through six photoreal 3D environments, each rendered twice** — once as a
360° panorama, once as a first-person pinhole view — with per-frame metric depth, camera pose
and action labels. 1200 clips, **18.9 h of video per view** (37.9 h total) at 30 fps, 2.05 M
frames per view, ~7.6 TB.

| Scene | Clips per view | Median clip | Range | Video per view |
|---|---|---|---|---|
| med_village | 100 | 2 min 17 s | 30 s – 6 min 40 s | 4.54 h |
| venice | 100 | 1 min 42 s | 21 s – 8 min 32 s | 4.19 h |
| apartment | 100 | 1 min 39 s | 29 s – 3 min 00 s | 2.91 h |
| paris | 100 | 1 min 39 s | 37 s – 3 min 00 s | 2.86 h |
| office | 100 | 1 min 15 s | 16 s – 3 min 01 s | 2.25 h |
| art_nouveau | 100 | 1 min 01 s | 11 s – 4 min 07 s | 2.19 h |

## Layout

```
<scene>/pano/<clip_id>/     equirectangular 4096x2048
<scene>/fp/<clip_id>/       pinhole 1280x720, hfov 65.5 deg (28 mm on a 36 mm sensor)
    rgb.mp4                 H.264, 30 fps
    depth/depth.mkv         FFV1 gray16le, lossless, log-quantized radial depth
    depth/depth.meta.json   near/far, frame count, decode formula
    camera_trajectory.csv   per-frame world pose + intrinsics
    description.json        scene, asset pack, licence, trajectory summary, render settings
    gamepad_format/         action labels (axis events + timeline)
    trajectory.png          top-down path plot (fp only)
```

## Paired, frame for frame

`pano/<clip_id>` and `fp/<clip_id>` are the **same camera path**: the first-person clip is
rendered from the panoramic clip's per-frame trajectory, so the two `camera_trajectory.csv`
files agree row for row (only `hfov_deg`/`focal_length_mm` differ — 360°/0 mm for the
equirect camera, 65.47°/28 mm for the pinhole). You get the same world state under two very
different projections without an interpolated alignment.

Clips are 11 s to 8.5 min of continuous motion — no cuts, no teleports.

## Conventions that are easy to get wrong

* **Depth is log-quantized and radial.** `depth_m = exp(gray/65535 * (log 200 − log 0.1) + log 0.1)`,
  and the value is distance along the ray, not along the optical axis — convert before unprojecting.
* **Frame counts.** `camera_trajectory.csv` has one row more than the video has frames (the
  last row is the closing keyframe). The authoritative count is `depth/depth.meta.json`.
* **Poses are Unreal-style**: left-handed, centimetres, X-forward / Y-right / Z-up, camera
  looking down its own +X.
* **Panoramic frames are equirectangular.** A rectangular crop is *not* a perspective view —
  reproject before comparing against the first-person clip.

## Render provenance

`description.json` records the exact render path per clip, and it is **not identical across
scenes**. Five scenes (med_village, venice, office, apartment, art_nouveau) were rendered in
two rounds — `MPPC_RGBOnly` then `MPPC_DepthPlus` — and stitched with a Lanczos kernel, so
`render.mppc` is an object with `rgb`/`depth` keys. **paris** was re-rendered later through a
corrected single-pass path (`MPPC_VelocityDepthPlus` with the extra pass dropped, linear-HDR
output, fixed exposure, linear stitch kernel), so its `render.mppc` is a plain string and its
`render.cube` additionally carries `fixed_ev` and `tm_comp`.

The reason for the paris re-render: a Lanczos resampling kernel has negative lobes, which on
high-contrast sky/architecture boundaries interpolate linear HDR below zero; clamping to zero
left a one-pixel pure-black rim along building silhouettes. Switching to a linear kernel took
sky edges with undershoot from 15.5% to 3.4% — below the 6.1% baseline of the cube faces
themselves. Per-frame auto-exposure was replaced with a fixed value at the same time, so
brightness no longer drifts with what happens to be in view.

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

## Related

* [WorldRover-preview](https://huggingface.co/datasets/AlayaLab/WorldRover-preview) — the original release as a lite subset (no depth)
* [Collection](https://huggingface.co/collections/AlayaLab/worldrover-6ab4ee625ea9252fbae26a66) — every part in one place
* [WorldRover-styles](https://huggingface.co/datasets/AlayaLab/WorldRover-styles) — the same
  kind of trajectories re-rendered under six lighting/style treatments

## License

Rendered video, depth, camera pose and action labels are released for research use. The
underlying 3D environments are third-party commercial assets, are **not** redistributed here,
and each clip's `description.json` records its asset pack and licence. Tools are MIT.
