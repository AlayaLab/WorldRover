// Lighting-state switcher
(function () {
  var stage = document.querySelector('[data-stage]');
  if (!stage) return;
  var img = stage.querySelector('img');
  var tag = stage.querySelector('.tag');

  document.querySelectorAll('.thumb').forEach(function (t) {
    t.addEventListener('click', function () {
      document.querySelectorAll('.thumb').forEach(function (o) { o.classList.remove('on'); });
      t.classList.add('on');
      img.style.opacity = 0;
      var next = new Image();
      next.onload = function () {
        img.src = next.src;
        tag.textContent = t.dataset.name;
        img.style.opacity = 1;
      };
      next.src = t.dataset.img;
    });
  });
})();

// Reveal on scroll
(function () {
  var els = document.querySelectorAll('.rv');
  if (!('IntersectionObserver' in window)) {
    els.forEach(function (el) { el.classList.add('in'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px' });
  els.forEach(function (el) { io.observe(el); });
})();
