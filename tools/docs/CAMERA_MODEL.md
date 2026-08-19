# Camera model and coordinate conventions

## World

Left-handed, **centimetres**, inherited from Unreal Engine:

```
+X forward      +Y right      +Z up
```

Poses are Unreal rotators in degrees — `pitch` about Y, `yaw` about Z, `roll` about X
— and compose exactly like `FRotationMatrix(FRotator(pitch, yaw, roll))`:

```python
R = worldrover.camera.rotation_world_from_cam(pitch, yaw, roll)   # columns = fwd, right, up
```

## Perspective camera

The camera looks along its own **+X**; image right is **+Y**, image up is **-Z**
(pixel row `v` grows downward). With `fx, fy, cx, cy` from
`worldrover.camera.intrinsics`:

```
ray_cam(u, v) = ( 1, (u - cx)/fx, -(v - cy)/fy )        # forward-normalized
world = R @ (ray_cam * planar_depth_cm) + location
```

`intrinsics` prefers the physical filmback (`focal_length_mm` / `sensor_width_mm`) and
falls back to `hfov_deg`; both agree in the released clips (28 mm on 36 mm -> 65.470451
deg over 1280 px, `fx = fy = 995.6`, principal point at the image centre).

Round-trip: `project(unproject(depth, cam), cam)` returns the original pixel
coordinates to ~1e-9 px, which is the cheapest way to confirm the conventions above
in your own reimplementation.

## Panoramic camera

Full 360x180 equirectangular, rendered as six cube faces (1536x1536) and stitched:

```
lon = (u + 0.5)/W * 2*pi - pi          # 0 = camera forward (+X), grows towards +Y
lat = pi/2 - (v + 0.5)/H * pi          # +pi/2 up, -pi/2 down
ray_cam = ( cos(lat)cos(lon), cos(lat)sin(lon), sin(lat) )
world = R @ (ray_cam * radial_distance_cm) + location
```

`worldrover.equirect.to_perspective` cuts a pinhole view out of a panorama at a chosen
hfov / yaw / pitch, with yaw and pitch measured relative to the panorama's own forward
axis (so `0, 0` looks where the capture looked).

## Units, in one place

| Quantity | Unit |
|---|---|
| Poses, point clouds, path lengths | cm |
| Depth (decoded) | m |
| Rotations | deg |
| Speeds in actions | cm/s, deg/s |

`worldrover.viz.write_ply` divides by 100 on the way out, so exported point clouds are
in metres — the usual convention for the tools that read PLY.
