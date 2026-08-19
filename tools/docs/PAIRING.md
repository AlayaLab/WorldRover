# Paired views

For each scene, `pano/<clip_id>` and `fp/<clip_id>` are the **same camera path**
rendered twice: once as a 360 equirectangular panorama, once as a 1280x720 pinhole
view. The first-person clip was rendered from the panoramic clip's own delivered
`camera_trajectory.csv`, one keyframe per frame, so:

* frame *k* of `fp/<id>/rgb.mp4` and frame *k* of `pano/<id>/rgb.mp4` are the same
  instant from the same position and heading;
* the two `camera_trajectory.csv` files agree row for row — position and yaw match to
  0.000000 cm / deg;
* the first-person view looks along the panorama's forward axis, i.e. the equirect
  centre column (`worldrover.equirect.to_perspective(..., yaw=0, pitch=0)` reproduces
  the framing, up to the 65.5 deg vs 90 deg hfov you ask for).

Verify a scene yourself:

```bash
python scripts/check_pairing.py /data/WorldRover/venice
```

which prints the worst per-frame deviation for every pair and exits non-zero if any
pair is not frame-exact.

## Why this matters

The pair gives the same world state under two very different projections, which is what
makes it usable for cross-projection tasks — panorama-conditioned novel view synthesis,
FOV/projection robustness, distillation from 360 context into a narrow FOV — without
having to trust an interpolated or re-timed alignment.

## What is *not* paired

Panoramic and first-person clips of the *same scene* but **different** clip ids are
independent trajectories. And note that earlier internal batches rendered the two views
from the same waypoints but re-timed the path, which makes them route-identical yet
frame-misaligned; only the ids released here as pairs are frame-exact, which is what
`check_pairing.py` checks.
