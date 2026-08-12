# WorldRover

Project page: https://alayalab.github.io/WorldRover/

## Local preview

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000

## Layout

```
index.html            # the page
static/css/style.css  # styles
static/images/        # teaser / figures
.nojekyll             # serve files as-is (no Jekyll processing)
```

## Publishing

Push to `main`, then in the repo: Settings → Pages → Source = "Deploy from a branch",
Branch = `main`, folder = `/ (root)`.
