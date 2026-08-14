// Videos.
//
// Desktop autoplays muted clips freely; phones do not. iOS checks muted and
// playsinline as properties at play() time, and refuses autoplay outright in
// Low Power Mode. So: set those as properties, retry once the reader first
// touches the page, and if playback is still refused hand over controls rather
// than leaving a poster that looks broken.
(function () {
  var boxes = [].slice.call(document.querySelectorAll('.vid'));
  if (!boxes.length) return;

  var blocked = [];          // tiles whose play() was refused

  function placeholder(box, src) {
    box.classList.add('vid-missing');
    box.innerHTML =
      '<div class="vid-note"><b>Video pending</b><span>' + src + '</span></div>';
  }

  function prime(v) {
    // properties, not just attributes — iOS checks these at play() time
    v.muted = true;
    v.playsInline = true;
    v.setAttribute('muted', '');
    v.setAttribute('playsinline', '');
    v.setAttribute('webkit-playsinline', '');
  }

  function play(box) {
    var v = box.querySelector('video');
    if (!v || !v.src) return;
    prime(v);
    var p = v.play();
    if (!p || !p.catch) return;
    p.catch(function () {
      // refused: remember it, and let the reader start it by hand
      if (blocked.indexOf(box) === -1) blocked.push(box);
      v.controls = true;
    });
  }

  function load(box) {
    if (box.dataset.loaded === '1') return;
    var v = box.querySelector('video');
    var src = box.dataset.src;
    if (!v || !src) return;
    box.dataset.loaded = '1';
    prime(v);
    v.addEventListener('error', function () { placeholder(box, src); });
    v.src = src;
  }

  if (!('IntersectionObserver' in window)) {
    boxes.forEach(function (box) { load(box); play(box); });
    return;
  }

  // fetch ahead of the viewport so playback starts without a visible stall
  var loadObs = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) load(e.target); });
  }, { rootMargin: '400px 0px' });

  // only decode what is on screen
  var playObs = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      var v = e.target.querySelector('video');
      if (!v) return;
      if (e.isIntersecting) { play(e.target); }
      else { v.pause(); }
    });
  }, { threshold: 0.2 });

  boxes.forEach(function (box) {
    loadObs.observe(box);
    playObs.observe(box);
  });

  // A gesture lifts the autoplay block on every browser that has one; take the
  // first one the reader makes and retry whatever was refused.
  function retry() {
    blocked.splice(0).forEach(function (box) {
      var v = box.querySelector('video');
      if (v) { v.controls = false; }
      play(box);
    });
  }
  ['touchstart', 'pointerdown', 'keydown'].forEach(function (evt) {
    window.addEventListener(evt, retry, { once: true, passive: true });
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
