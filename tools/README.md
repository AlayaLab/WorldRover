# WorldRover — dataset tools

Tools for the **WorldRover** dataset: paired 360-panoramic and first-person video of
photoreal 3D environments, with per-frame depth, camera pose and action labels.

* Paper: https://arxiv.org/abs/2608.15659
* Project page: https://alayalab.github.io/WorldRover/
* Dataset: https://huggingface.co/collections/xjxu21/worldrover-6a851193b19350ca6de9f424

This directory holds the *dataset-side* code — readers, geometry, verification and
visualisation. The renderer and trajectory planner that produce the clips are not part of
this release.

```bash
pip install -r requirements.txt          # numpy, opencv-python; ffmpeg/ffprobe on PATH

python scripts/verify_dataset.py /data/WorldRover --check-actions
python scripts/check_pairing.py   /data/WorldRover/venice
python scripts/make_depth_preview.py /data/WorldRover/venice/fp/venice_000003 preview.mp4
```

```python
from worldrover import Clip

clip = Clip("/data/WorldRover/venice/fp/venice_000003")
rgb     = clip.rgb_frame(100)            # uint8 (H, W, 3), sRGB, ready to use
depth_m = clip.depth_frame(100)          # planar depth in metres
points  = clip.points_world(100)         # world points in centimetres
poses   = clip.poses                     # per-frame camera pose + intrinsics
```

## What is in the dataset

| | |
|---|---|
| Scenes | `med_village`, `paris`, `venice`, `art_nouveau` |
| Views | `pano` — 4096x2048 equirectangular · `fp` — 1280x720 pinhole (hfov 65.5 deg) |
| Per scene | ~30 min panoramic + ~30 min first-person, ~4 h total |
| Frame rate | 30 fps |
| Per clip | `rgb.mp4`, lossless 16-bit depth, per-frame camera pose, action labels, scene metadata |
| Pairing | `pano/<id>` and `fp/<id>` are the **same camera path**, frame for frame |

Clips are 20 s to 3.5 min of continuous motion through the scene — no cuts, no teleports.

## Layout

```
WorldRover/
  <scene>/
    pano/<clip_id>/  rgb.mp4  depth/{depth.mkv,depth.meta.json}
                     camera_trajectory.csv  description.json
                     gamepad_format/  trajectory.png
    fp/<clip_id>/    (identical structure; same clip_id = same trajectory)
```

## Three things to get right

1. **Depth is log-quantized and radial.** Decode with the formula in
   `depth.meta.json`, then convert radial distance to planar depth before
   unprojecting. Skipping the conversion costs 13% at the frame corner.
2. **`camera_trajectory.csv` has `n_frames + 1` rows.** The last row is the
   renderer's closing keyframe, not a frame of video.
3. **Poses are Unreal-style**: left-handed, centimetres, X-forward/Y-right/Z-up, and
   the camera looks down its own +X with image up = -Z.

All three are handled for you by this package; the reasoning and the measurements
behind them are in [`docs/DATA_FORMAT.md`](docs/DATA_FORMAT.md) and
[`docs/CAMERA_MODEL.md`](docs/CAMERA_MODEL.md).

## Documentation

* [`docs/DATA_FORMAT.md`](docs/DATA_FORMAT.md) — every file, every column, depth and action encodings
* [`docs/CAMERA_MODEL.md`](docs/CAMERA_MODEL.md) — coordinate conventions, pinhole and equirect projection
* [`docs/PAIRING.md`](docs/PAIRING.md) — how the two views line up, and how to verify it

## Package

| Module | Purpose |
|---|---|
| `worldrover.dataset` | `Clip` handle: metadata, frames, point clouds, contract check |
| `worldrover.camera` | intrinsics, Unreal rotator -> matrix, project / unproject, speed |
| `worldrover.depth` | mkv decoding, log dequantization, radial -> planar, colourisation |
| `worldrover.equirect` | equirect ray map, unprojection, equirect -> pinhole view |
| `worldrover.actions` | gamepad action stream: parse, denormalize, replay to poses |
| `worldrover.viz` | rgb/depth pairs, contact sheets, top-down trajectories, PLY export |

## Scripts

| Script | What it does |
|---|---|
| `verify_dataset.py` | checks every clip against the delivery contract; `--check-actions` replays the action labels |
| `check_pairing.py` | proves `pano/<id>` and `fp/<id>` are frame-exact |
| `make_depth_preview.py` | RGB-next-to-depth preview video |
| `export_pointcloud.py` | one frame -> coloured PLY point cloud (metres) |
| `pano_to_perspective.py` | cut a pinhole video out of a panoramic clip at any hfov/yaw/pitch |
| `plot_trajectory.py` | top-down path plot, coloured by speed |
| `first_frame_grid.py` | contact sheet of a scene's clips |

## License

The code in this repository is MIT licensed (see [LICENSE](LICENSE)).

The dataset itself is distributed under its own terms: the clips are renders of
third-party commercial environment assets, and `description.json` records each scene's
asset pack and license. Redistribution of the *rendered video, depth, pose and action
data* is permitted for research; the source assets are not included and are not
redistributable here.
