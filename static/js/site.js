// Videos: lazy — a clip is only fetched once it is near the viewport, plays
// while visible, pauses when it leaves. Until the file exists, the stage falls
// back to a placeholder naming the path that is still missing.
(function () {
  var boxes = document.querySelectorAll('.vid');
  if (!boxes.length) return;

  function placeholder(box, src) {
    box.classList.add('vid-missing');
    box.innerHTML =
      '<div class="vid-note"><b>Video pending</b><span>' + src + '</span></div>';
  }

  function load(box) {
    if (box.dataset.loaded) return;
    box.dataset.loaded = '1';
    var v = box.querySelector('video');
    var src = box.dataset.src;
    if (!v || !src) return;
    v.addEventListener('error', function () { placeholder(box, src); });
    v.src = src;
  }

  if (!('IntersectionObserver' in window)) {
    boxes.forEach(load);
    return;
  }

  // Fetch ahead of the viewport so playback starts without a visible stall.
  var near = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      load(e.target);
      near.unobserve(e.target);
    });
  }, { rootMargin: '400px 0px' });

  // Only decode what is on screen.
  var visible = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var v = e.target.querySelector('video');
      if (!v) return;
      if (e.isIntersecting) { v.play().catch(function () {}); }
      else { v.pause(); }
    });
  }, { threshold: 0.2 });

  boxes.forEach(function (box) {
    near.observe(box);
    visible.observe(box);
  });

  // A [data-sync] grid shows one moment in several modalities, so the tiles
  // should sit on the same frame. Realign only at the start and each time the
  // lead wraps around: seeking mid-playback interrupts decoding, and doing it
  // continuously leaves the later tiles stuck in a seek loop.
  document.querySelectorAll('[data-sync]').forEach(function (group) {
    var vids = [].slice.call(group.querySelectorAll('video'));
    if (vids.length < 2) return;
    var lead = vids[0];
    var prev = 0;

    function align() {
      vids.slice(1).forEach(function (v) {
        if (v.readyState < 1 || v.seeking) return;
        if (Math.abs(v.currentTime - lead.currentTime) > 0.4) {
          v.currentTime = lead.currentTime;
        }
      });
    }

    lead.addEventListener('play', align);
    lead.addEventListener('timeupdate', function () {
      if (lead.currentTime < prev) align();   // lead looped
      prev = lead.currentTime;
    });
  });
})();

// Scroll progress bar
(function () {
  var bar = document.getElementById('progress');
  if (!bar) return;
  var ticking = false;
  function update() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.width = (h > 0 ? (window.scrollY / h) * 100 : 0) + '%';
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(update);
  }, { passive: true });
  update();
})();

// Side rail: highlight the section currently under the reader.
(function () {
  var links = [].slice.call(document.querySelectorAll('.side-nav a:not(.home)'));
  if (!links.length || !('IntersectionObserver' in window)) return;

  var byId = {};
  var targets = [];
  links.forEach(function (a) {
    var el = document.querySelector(a.getAttribute('href'));
    if (!el) return;
    byId[el.id] = a;
    targets.push(el);
  });

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      links.forEach(function (a) { a.classList.remove('on'); });
      var a = byId[e.target.id];
      if (a) a.classList.add('on');
    });
  }, { rootMargin: '-45% 0px -50% 0px' });

  targets.forEach(function (el) { io.observe(el); });
})();

// Reveal on scroll
(function () {
  var els = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    els.forEach(function (el) { el.classList.add('vis'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('vis'); io.unobserve(e.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px' });
  els.forEach(function (el) { io.observe(el); });
})();
