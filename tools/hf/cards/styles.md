---
license: other
license_name: worldrover-research
pretty_name: WorldRover style variants
task_categories:
  - depth-estimation
  - robotics
tags:
  - video
  - depth
  - camera-pose
  - embodied-ai
  - world-model
  - synthetic
  - relighting
  - domain-randomization
size_categories:
  - 100B<n<1T
---

# WorldRover-styles

**The same camera path rendered under six different treatments.** 200 first-person
trajectories across four scenes, each re-rendered as up to six variants — so the geometry,
motion and action labels are held fixed while lighting, weather and material appearance
change. 1000 clips, ~48 h of video at 30 fps, ~818 GB.

| Variant | Scenes | Clips | What changes | Per clip |
|---|---|---|---|---|
| `first_person` | all 4 | 200 | the reference render | rgb + depth + pose + actions |
| `white_model` | all 4 | 200 | untextured white shading — pure geometry | rgb only |
| `goldenhour` | 3 | 150 | low warm sun | rgb only |
| `night` | 3 | 150 | night lighting | rgb only |
| `snow` | 3 | 150 | snow cover + overcast | rgb only |
| `storm` | 3 | 150 | storm sky + wet surfaces | rgb only |

`goldenhour` / `night` / `snow` / `storm` cover med_village, paris and venice; art_nouveau is
an interior set and ships `first_person` + `white_model` only.

| Scene | Base trajectories | Median clip | Range | Video per variant |
|---|---|---|---|---|
| med_village | 50 | 3 min 29 s | 41 s – 6 min 45 s | 3.01 h |
| venice | 50 | 2 min 54 s | 1 min 07 s – 6 min 43 s | 2.66 h |
| paris | 50 | 1 min 54 s | 49 s – 5 min 15 s | 1.80 h |
| art_nouveau | 50 | 1 min 32 s | 14 s – 5 min 00 s | 1.39 h |

## Layout

```
<scene>/first_person/<clip_id>/     pinhole 1280x720, 30 fps
    rgb.mp4  depth/depth.mkv  depth/depth.meta.json
    camera_trajectory.csv  description.json  gamepad_format/  trajectory.png
<scene>/<variant>/<clip_id>/rgb.mp4  same path, same frame count, different look
style_grids/batch_grid_<scene>_<variant>.mp4   contact-sheet previews (64 videos)
```

A variant clip shares its `<clip_id>` with the `first_person` clip, so the pose, depth and
action labels from `first_person/<clip_id>` apply to every variant of it unchanged.

## Conventions

* **Read the depth pixel format from each clip's `depth/depth.meta.json` — this batch is not
  uniform.** 197 of the 200 clips are `FFV1 / gbrp16le` with the code in the **R** channel
  (G = B = 0); three art_nouveau clips — `an725_navmesh_000005`, `an_react_000022`,
  `an_react_000037` — are single-plane `FFV1 / gray16le` instead. Every clip's
  `depth.meta.json` states its own format correctly (verified against the files), so read it
  rather than assuming. [WorldRover-6scenes](https://huggingface.co/datasets/AlayaLab/WorldRover-6scenes)
  is uniformly `gray16le`. The quantization is identical either way:
  `depth_m = exp(code/65535 * (log 200 − log 0.1) + log 0.1)`, radial distance.
* `camera_trajectory.csv` has one row more than the video has frames; the authoritative count
  is `depth/depth.meta.json`.
* Poses are Unreal-style: left-handed, centimetres, X-forward / Y-right / Z-up.

## Tools

```bash
git clone https://github.com/AlayaLab/WorldRover
pip install -r WorldRover/tools/requirements.txt   # numpy, opencv-python; ffmpeg/ffprobe on PATH
cd WorldRover/tools                                # the package is not pip-installable yet
```

```python
from worldrover import Clip

clip    = Clip("/data/WorldRover-styles/venice/first_person/fix_venice_000000")
rgb     = clip.rgb_frame(100)     # uint8 (H, W, 3), sRGB
depth_m = clip.depth_frame(100)   # planar depth in metres
pts     = clip.points_world(100)  # world points, centimetres
poses   = clip.poses              # per-frame pose + intrinsics
```

`Clip` takes a filesystem path to a clip directory. The reader takes the depth pixel format
from that clip's own `depth/depth.meta.json`, so it handles both encodings used across these
repositories, and it converts radial depth and the off-by-one trajectory row for you.

The style variants hold only `rgb.mp4`; point `Clip` at the matching `first_person`
clip for that trajectory's depth, pose and action labels.

## Related

* [WorldRover-preview](https://huggingface.co/datasets/AlayaLab/WorldRover-preview) — the original release as a lite subset (no depth)
* [Collection](https://huggingface.co/collections/AlayaLab/worldrover-6ab4ee625ea9252fbae26a66) — every part in one place
* [WorldRover-6scenes](https://huggingface.co/datasets/AlayaLab/WorldRover-6scenes) — paired
  360° panoramic + first-person, six scenes, 7.6 TB

## License

Rendered video, depth, camera pose and action labels are released for research use. The
underlying 3D environments are third-party commercial assets, are **not** redistributed here,
and each clip's `description.json` records its asset pack and licence. Tools are MIT.
