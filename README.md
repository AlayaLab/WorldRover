# WorldRover — project page

Live at **https://alayalab.github.io/WorldRover/**

Source for the paper *WorldRover: A Scalable Synthetic Video Data Engine for World
Exploration with Rich Annotations* (Alaya Lab).

## Local preview

```bash
python3 -m http.server 8765
```

Then open http://localhost:8765

## Layout

```
index.html              the page
static/css/site.css     structure: layout, section shell, media tiles
static/css/sc2.css      palette + type, loaded after site.css
static/js/site.js       lazy video loading, modality sync, side rail, reveal
static/js/stars.js      starfield + meteors
static/images/          teaser, engine diagram (engine.gif animates its six stages)
static/videos/          web-encoded clips, by section
.nojekyll               serve files as-is
```

All body copy is quoted from the report — section subtitles from `sec/*.tex`, the
Highlights list from the three contributions in `sec/01.intro.tex`, and the release
figures from `tab:stats`.

## Adding a video

Source renders are **not** in this repo (see `.gitignore`) — they are 720p/4K masters
running to hundreds of MB each. Only web-encoded copies are published, at roughly
1.5 Mbps:

```bash
ffmpeg -i SOURCE.mp4 -an -c:v libx264 -profile:v high -pix_fmt yuv420p \
  -crf 28 -preset slow -maxrate 1600k -bufsize 3200k -g 48 \
  -movflags +faststart static/videos/SECTION/NAME.mp4
```

Panoramas are downscaled from 4096×2048 to 1920×960 first (`-vf scale=1920:960:flags=lanczos`,
`-maxrate 2800k`) — the page never displays them wider than ~1180 px.

Each clip also needs a poster frame, so the page shows something before the video loads:

```bash
ffmpeg -ss 2 -i SOURCE.mp4 -frames:v 1 -vf scale=720:-2 -q:v 5 \
  static/videos/SECTION/NAME.jpg
```

Then add a tile pointing at it:

```html
<figure>
  <div class="stage vid" data-src="static/videos/SECTION/NAME.mp4">
    <span class="badge">Label</span>
    <video muted loop playsinline preload="metadata" poster="static/videos/SECTION/NAME.jpg"></video>
  </div>
</figure>
```

Clips are fetched only once they come near the viewport, play while visible and pause
when they leave. A grid marked `data-sync` keeps its tiles on the same frame — used
where several videos show one moment (the four modalities, the five lighting states,
the three viewpoints).

## Publishing

Push to `main`. Pages is set to deploy from the branch root.
