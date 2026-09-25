<h1 align="center">WorldRover</h1>
<p align="center"><b>A Scalable Synthetic Video Data Engine for World Exploration with Rich Annotations</b></p>

<p align="center">
  Xiaojie Xu<sup>1,2,*</sup> &nbsp; Zhengyuan Lin<sup>1,2,*</sup> &nbsp; Runyi Li<sup>1,2</sup> &nbsp;
  Yihao Liu<sup>1</sup> &nbsp; Kaipeng Zhang<sup>1,†</sup> &nbsp; Yongtao Ge<sup>1,†</sup>
</p>

<p align="center">
  <sup>1</sup> Alaya Lab &nbsp;·&nbsp; <sup>2</sup> The University of Tokyo
  &nbsp;·&nbsp; <sup>*</sup> Equal contribution &nbsp;·&nbsp; <sup>†</sup> Corresponding author
</p>

<p align="center">
  <a href="https://arxiv.org/abs/2608.15659"><b>Paper</b></a> ·
  <a href="https://alayalab.github.io/WorldRover/"><b>Project page</b></a> ·
  <a href="https://huggingface.co/collections/AlayaLab/worldrover-6ab4ee625ea9252fbae26a66"><b>Dataset</b></a> ·
  <a href="tools/"><b>Tools</b></a>
</p>

<p align="center">
  <img src="static/images/teaser.jpg" alt="WorldRover teaser" width="100%">
</p>

## What this is

WorldRover is a data engine that walks a camera — and optionally a character — through
artist-built 3D environments and records the traversal as video **together with the
annotations that a renderer can produce exactly**, rather than estimate afterwards: metric
depth, per-frame camera pose, optical flow, and the action stream that produced the motion.

Five axes of variation come out of the same engine:

| | |
|---|---|
| **Multi-view** | Three observations of a route with matched timing and geometry — first person, third person, 360 panorama |
| **Multi-modal** | Colour, depth and motion from one rasterization of the same instant |
| **Multi-style** | Geometry and motion held fixed while illumination or texture changes |
| **Multi-scene** | 30+ artist-built Unreal Engine scenes, interior to city scale |
| **Multi-character** | 70+ animated humanoids, animals and creatures |

Because the camera path is a first-class input, the same trajectory can be re-rendered in a
different projection, a different lighting state, or with a different character, and the
frames still line up frame for frame.

## The dataset

Three releases, all from the same engine. **Start with `WorldRover-6scenes`** — it is the
largest and newest.

| Release | What it is | Scenes | Clips | Video | Size |
|---|---|---|---|---|---|
| [**WorldRover-6scenes**](https://huggingface.co/datasets/AlayaLab/WorldRover-6scenes) | paired 360 panoramic + first person, lossless depth | 6 | 600 per view | 18.9 h per view | 7.6 TB |
| [**WorldRover-styles**](https://huggingface.co/datasets/AlayaLab/WorldRover-styles) | one trajectory set under six lighting / style treatments | 4 | 1000 | 48 h | 818 GB |
| [**WorldRover**](https://huggingface.co/datasets/AlayaLab/WorldRover) | index, and the lite subset of the original release (no depth) | 4 | 129 per view | 4.1 h per view | 103 GB |

`WorldRover-6scenes` covers `med_village`, `venice`, `apartment`, `paris`, `office` and
`art_nouveau`, 100 clips per view each, 11 s to 8.5 min per clip. The four scenes of the
original release also remain available one repo per scene, with full depth:
[med_village](https://huggingface.co/datasets/AlayaLab/WorldRover-med_village) 334 GB ·
[paris](https://huggingface.co/datasets/AlayaLab/WorldRover-paris) 170 GB ·
[venice](https://huggingface.co/datasets/AlayaLab/WorldRover-venice) 169 GB ·
[art_nouveau](https://huggingface.co/datasets/AlayaLab/WorldRover-art_nouveau) 178 GB.

Depth is 87% of the bytes, so if you only need RGB, pose and actions, the lite subset is the
cheap way in.

Every clip, both views, ships:

```
<scene>/{pano,fp}/<clip_id>/
  rgb.mp4                    H.264 30 fps, sRGB;  pano 4096x2048 equirect,  fp 1280x720 pinhole
  depth/depth.mkv            FFV1 lossless 16-bit, log-quantized radial distance
  depth/depth.meta.json      near/far, frame count, decode formula
  camera_trajectory.csv      per-frame pose (cm, deg) + intrinsics
  description.json           scene identity, asset pack + license, trajectory summary
  gamepad_format/            action labels (axes normalized to [-1, 1])
  trajectory.png             top-down path preview
```

The two views of a clip id share the same camera path frame for frame: the first-person clip was
rendered from the panoramic clip's per-frame trajectory, so the two pose files match exactly. To
check a scene:

```bash
python tools/scripts/check_pairing.py /data/WorldRover-6scenes/venice
```

Clips are 11 s to 8.5 min of continuous motion — no cuts, no teleports.

## Dataset tools

`tools/` holds the dataset-side Python package and scripts: reading clips, decoding depth,
camera geometry, verifying a download, and visualising trajectories and point clouds.

```bash
pip install -r tools/requirements.txt
python tools/scripts/verify_dataset.py /data/WorldRover-6scenes --check-actions
```

```python
from worldrover import Clip                      # with tools/ on PYTHONPATH
clip = Clip("/data/WorldRover-6scenes/venice/fp/venice_000000")
rgb     = clip.rgb_frame(100)                    # uint8 (720, 1280, 3), sRGB
depth_m = clip.depth_frame(100)                  # planar depth in metres
points  = clip.points_world(100)                 # world points in centimetres
```

Three conventions are easy to get wrong by hand, and the tools handle all three: depth codes
are **log-quantized** and store **radial** distance (convert before unprojecting), and the
pixel format differs between releases — `gray16le` in `WorldRover-6scenes`, mostly `gbrp16le`
with the code in R in `WorldRover-styles` — so read it from each clip's `depth.meta.json`;
`camera_trajectory.csv` has `n_frames + 1` rows, the last being the closing keyframe; poses
are Unreal-style — left-handed, centimetres, X-forward / Y-right / Z-up, camera looking down
its own +X. See [`tools/README.md`](tools/README.md) and `tools/docs/` for the full format,
camera model and pairing notes.

The renderer and trajectory planner are **not** part of this release.

## TODO

- [x] Preview release — first-person and 360-panoramic RGB-D, 4 scenes
- [x] Dataset tools
- [x] Style and white-model video (first person) — `WorldRover-styles`
- [ ] Third-person video with motion labels
- [x] More scenes — `WorldRover-6scenes` adds `office` and `apartment`, 100 clips per view per scene
- [ ] More scenes still
- [ ] WorldRover-Engine — scene pre-processing, trajectory planning, rendering pipeline

## Citation

```bibtex
@article{worldrover2026,
  title         = {WorldRover: A Scalable Synthetic Video Data Engine
                   for World Exploration with Rich Annotations},
  author        = {Xu, Xiaojie and Lin, Zhengyuan and Li, Runyi and
                   Liu, Yihao and Zhang, Kaipeng and Ge, Yongtao},
  journal       = {arXiv preprint arXiv:2608.15659},
  year          = {2026},
  eprint        = {2608.15659},
  archivePrefix = {arXiv},
  url           = {https://arxiv.org/abs/2608.15659}
}
```

## License

The dataset's rendered video, depth, camera pose and action labels are released for research
use; the underlying 3D environments are third-party commercial assets, are **not**
redistributed, and each clip's `description.json` records its asset pack and license. The
tools in `tools/` are MIT licensed (`tools/LICENSE`).
