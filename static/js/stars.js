// Starfield + occasional meteors for the SC2 theme.
// Creates its own canvas so the page only needs to load this one file.
// Stars are painted once to an offscreen layer and blitted; only the handful of
// live meteors is drawn per frame.
(function () {
  var reduce = window.matchMedia &&
               window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var canvas = document.createElement('canvas');
  canvas.className = 'sky';
  document.body.insertBefore(canvas, document.body.firstChild);
  var ctx = canvas.getContext('2d');

  var W, H, dpr, stars, meteors = [], nextSpawn = 0;

  function rand(a, b) { return a + Math.random() * (b - a); }

  function build() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    var n = Math.round((W * H) / 9000);
    stars = [];
    for (var i = 0; i < n; i++) {
      stars.push({
        x: Math.random() * W,
        y: Math.random() * H,
        r: rand(0.35, 1.25),
        a: rand(0.18, 0.75),
        // a slow twinkle, each star on its own phase and rate
        p: Math.random() * Math.PI * 2,
        s: rand(0.4, 1.3)
      });
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
  }

  var last = 0;
  function frame(t) {
    var dt = last ? Math.min((t - last) / 1000, 0.05) : 0;
    last = t;

    ctx.clearRect(0, 0, W, H);

    for (var i = 0; i < stars.length; i++) {
      var s = stars[i];
      var a = s.a * (0.65 + 0.35 * Math.sin(t / 1000 * s.s + s.p));
      ctx.fillStyle = 'rgba(204, 230, 255, ' + a.toFixed(3) + ')';
      ctx.fillRect(s.x, s.y, s.r, s.r);
    }

    if (!reduce) {
      if (t > nextSpawn) {
        spawn();
        nextSpawn = t + rand(600, 1800);
      }

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

        var g = ctx.createLinearGradient(hx, hy, tx, ty);
        g.addColorStop(0, 'rgba(' + m.head + ',' + alpha.toFixed(3) + ')');
        g.addColorStop(1, 'rgba(' + m.head + ',0)');
        ctx.strokeStyle = g;
        ctx.lineWidth = 1.6;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(hx, hy);
        ctx.lineTo(tx, ty);
        ctx.stroke();

        ctx.fillStyle = 'rgba(255,255,255,' + (alpha * 0.9).toFixed(3) + ')';
        ctx.beginPath();
        ctx.arc(hx, hy, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    requestAnimationFrame(frame);
  }

  build();
  window.addEventListener('resize', build);
  requestAnimationFrame(frame);
})();
