// Starfield + occasional meteors for the SC2 theme.
//
// Split across two canvases on purpose. The stars are painted once, on load and
// on resize, and then left alone — a full-viewport canvas cleared and repainted
// every frame costs a texture upload per frame and competes with video decoding.
// Only the meteor layer animates, and its loop runs solely while a meteor is
// alive; between streaks nothing is scheduled at all.
(function () {
  var reduce = window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function make(cls) {
    var c = document.createElement('canvas');
    c.className = cls;
    document.body.insertBefore(c, document.body.firstChild);
    return c;
  }

  var starCanvas = make('sky sky-stars');
  var starCtx = starCanvas.getContext('2d');
  var meteorCanvas = make('sky sky-meteors');
  var meteorCtx = meteorCanvas.getContext('2d');

  var W, H, dpr;
  var meteors = [];
  var running = false;
  var spawnTimer = null;

  function rand(a, b) { return a + Math.random() * (b - a); }

  function size(c, ctx) {
    c.width = W * dpr;
    c.height = H * dpr;
    c.style.width = W + 'px';
    c.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function paintStars() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth;
    H = window.innerHeight;
    size(starCanvas, starCtx);
    size(meteorCanvas, meteorCtx);

    starCtx.clearRect(0, 0, W, H);
    var n = Math.round((W * H) / 9000);
    for (var i = 0; i < n; i++) {
      var r = rand(0.35, 1.25);
      starCtx.fillStyle = 'rgba(204, 230, 255, ' + rand(0.18, 0.75).toFixed(3) + ')';
      starCtx.fillRect(Math.random() * W, Math.random() * H, r, r);
    }
  }

  function spawn() {
    // enter from the top edge, travel down-left, like the SC2 key art
    var gold = Math.random() < 0.22;
    meteors.push({
      x: rand(W * 0.25, W * 1.15),
      y: rand(-80, H * 0.45),
      len: rand(120, 300),
      speed: rand(520, 880),
      life: 0,
      ttl: rand(0.9, 1.5),
      head: gold ? '255,221,153' : '210,238,255'
    });
    if (!running) { running = true; last = 0; requestAnimationFrame(frame); }
    schedule();
  }

  function schedule() {
    clearTimeout(spawnTimer);
    spawnTimer = setTimeout(spawn, rand(600, 1800));
  }

  var last = 0;
  function frame(t) {
    var dt = last ? Math.min((t - last) / 1000, 0.05) : 0;
    last = t;

    meteorCtx.clearRect(0, 0, W, H);

    for (var j = meteors.length - 1; j >= 0; j--) {
      var m = meteors[j];
      m.life += dt;
      if (m.life > m.ttl) { meteors.splice(j, 1); continue; }

      var d = m.speed * m.life;
      var hx = m.x - d * 0.75, hy = m.y + d * 0.66;   // heading down-left
      var tx = hx + m.len * 0.75, ty = hy - m.len * 0.66;

      // fade in over the first fifth of its life, out over the rest
      var k = m.life / m.ttl;
      var alpha = (k < 0.2 ? k / 0.2 : 1 - (k - 0.2) / 0.8) * 0.9;

      var g = meteorCtx.createLinearGradient(hx, hy, tx, ty);
      g.addColorStop(0, 'rgba(' + m.head + ',' + alpha.toFixed(3) + ')');
      g.addColorStop(1, 'rgba(' + m.head + ',0)');
      meteorCtx.strokeStyle = g;
      meteorCtx.lineWidth = 1.6;
      meteorCtx.lineCap = 'round';
      meteorCtx.beginPath();
      meteorCtx.moveTo(hx, hy);
      meteorCtx.lineTo(tx, ty);
      meteorCtx.stroke();

      meteorCtx.fillStyle = 'rgba(255,255,255,' + (alpha * 0.9).toFixed(3) + ')';
      meteorCtx.beginPath();
      meteorCtx.arc(hx, hy, 1.5, 0, Math.PI * 2);
      meteorCtx.fill();
    }

    if (meteors.length) {
      requestAnimationFrame(frame);
    } else {
      running = false;                 // nothing to draw: stop scheduling frames
      meteorCtx.clearRect(0, 0, W, H);
    }
  }

  paintStars();
  window.addEventListener('resize', paintStars);

  if (!reduce) {
    schedule();
    // pause the whole thing while the tab is hidden
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { clearTimeout(spawnTimer); }
      else { schedule(); }
    });
  }
})();
