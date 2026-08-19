# On-disk format

```
WorldRover/
  <scene>/                        # med_village | paris | venice | art_nouveau
    pano/<clip_id>/               # 360 equirectangular
    fp/<clip_id>/                 # first person, pinhole — same clip_id = same trajectory
```

Every clip directory, both views, contains exactly this:

| Path | What it is |
|---|---|
| `rgb.mp4` | H.264, 30 fps. Already tone-mapped to sRGB (ACES filmic); no further transform needed. Perspective clips are 1280x720, panoramic 4096x2048. |
| `depth/depth.mkv` | FFV1 (lossless) 16-bit, one code per pixel, **log-quantized** between `near_m` and `far_m`. |
| `depth/depth.meta.json` | `near_m`, `far_m`, `n_frames`, `width`, `height`, `fps`, `format`, `decode_formula`. |
| `camera_trajectory.csv` | Per-frame pose + intrinsics. `n_frames + 1` rows (the extra row is the renderer's closing keyframe). |
| `description.json` | Scene identity (`umap`, asset pack, license, tags), camera block (projection, resolution, sensor), trajectory summary (frames, duration, path length, start/end), render config, provenance (git commit, schema doc). |
| `gamepad_format/` | Action labels — see [Actions](#actions). |
| `trajectory.png` | Top-down preview of the path. |

## camera_trajectory.csv

| Column | Unit | Notes |
|---|---|---|
| `frame` | — | 0-based; row `k` is the pose `rgb.mp4` frame `k` was rendered with |
| `location_x/y/z` | cm | world position, left-handed X-forward / Y-right / Z-up |
| `rotation_pitch/yaw/roll` | deg | Unreal rotator; pitch about Y, yaw about Z, roll about X |
| `hfov_deg` | deg | 65.470451 for the released first-person clips; 360 for panoramic |
| `focal_length_mm`, `sensor_width_mm`, `sensor_height_mm` | mm | physical camera: 28 mm on 36 x 20.25 mm (perspective clips) |

`description.json`'s `camera.trajectory.num_frames` counts **keyframes**, which includes
the closing keyframe, so it reads one higher than the video's frame count. The
authoritative frame count is `depth/depth.meta.json` -> `n_frames`, which equals the
number of frames in `rgb.mp4`. Both views of a pair agree on it.

## Depth

The stored 16-bit code decodes to **radial distance in metres**:

```python
depth_m = exp(code / 65535 * (log(far_m) - log(near_m)) + log(near_m))
```

Two gotchas, both handled by `worldrover.depth`:

1. **Log, not linear.** Codes are spaced logarithmically between `near_m = 0.1` and
   `far_m = 200`; reading them as linear depth destroys the near field.
2. **Radial, not planar.** The value is the distance from the camera centre along
   that pixel's ray. For a pinhole frame, divide by
   `sqrt(1 + ((u-cx)/fx)^2 + ((v-cy)/fy)^2)` to get depth along the forward axis
   before unprojecting (`worldrover.depth.radial_to_planar`). The two differ by 13%
   in the corner of a 1280x720 frame at hfov 65.5 deg.

   *Measured:* unprojecting frame *A* and reprojecting into frame *B* six frames
   later, the median disagreement is **0.3 cm and flat across the image** with the
   conversion, versus 0.7 cm at the centre rising to **8.2 cm at the edge** without
   it — which is what makes the convention unambiguous.

For panoramic clips the value is already radial along the equirect ray, so no
conversion applies; multiply the ray direction by the distance.

Older releases wrote depth as 3-channel `gbrp16le` with the payload in R and
`G = B = 0`; newer ones are single-channel `gray16le`. `depth.meta.json` says which,
and the reader handles both.

## Actions

`gamepad_format/` carries a gamepad-style action stream so a policy can be trained on
(frame, action) pairs:

| File | Contents |
|---|---|
| `keybinds_snapshot.json` | `fps`, `hfov_deg`, `start_pose`, `axis_normalization`, `bindings` |
| `gamepad_axis_0.txt` | `"<timestamp>: axis_<n>,d,<value>"`, **event driven** (a line when an axis changes) |
| `gamepad_button_0.txt`, `key_0.txt`, `mouse_move_0.txt`, `mouse_wheel_0.txt` | present for format compatibility; empty for these clips |
| `timeline.txt` | render start/end markers |

Axes are normalized to [-1, 1]; `axis_normalization` gives the physical value at 1.0
(default profile: strafe 100 cm/s, forward 210 cm/s, yaw 30 deg/s, vertical
100 cm/s). **Forward is `AXIS_1_NEG`** — negate axis 1.

Because the stream is event driven, sample it at frame boundaries
(`worldrover.actions.load_axes` does this) rather than treating one line as one frame.

**Fidelity.** The actions are derived from the camera motion, not recorded from a
human, and the event threshold makes the encoding slightly lossy. Replaying them from
`start_pose` reproduces a 40 s clip's heading to **~0.1 deg** (median) and its position
to **~0.5 m** — good enough to learn from, not a bit-exact inverse. When you need the
exact pose, read `camera_trajectory.csv`.
